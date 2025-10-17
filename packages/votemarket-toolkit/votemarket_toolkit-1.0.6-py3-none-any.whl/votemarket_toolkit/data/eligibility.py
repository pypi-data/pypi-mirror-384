"""
Eligibility service for determining which users can claim rewards.

This service identifies users who are eligible to claim VoteMarket rewards
based on their voting activity and current voting power.
"""

from typing import List, Optional

from eth_utils import to_checksum_address
from w3multicall.multicall import W3Multicall

from votemarket_toolkit.shared import registry
from votemarket_toolkit.shared.exceptions import VoteMarketDataException
from votemarket_toolkit.shared.services.web3_service import Web3Service
from votemarket_toolkit.shared.types import EligibleUser
from votemarket_toolkit.utils.blockchain import get_rounded_epoch
from votemarket_toolkit.votes.services.votes_service import votes_service


class EligibilityService:
    """
    Service for checking user eligibility to claim VoteMarket rewards.

    This service determines which users have active votes and are eligible
    to claim rewards for specific gauges and epochs.
    """

    def __init__(self, chain_id: int):
        """
        Initialize the eligibility service.

        Args:
            chain_id: Blockchain network ID (1 for Ethereum, 42161 for Arbitrum)
        """
        self.chain_id = chain_id
        self.web3_service = Web3Service.get_instance(chain_id)

    async def get_eligible_users(
        self,
        protocol: str,
        gauge_address: str,
        current_epoch: int,
        block_number: int,
        chain_id: Optional[int] = None,
        platform: Optional[str] = None,
    ) -> List[EligibleUser]:
        """
        Identify users who are eligible to claim rewards for a gauge/epoch.

        Returns users who meet ALL eligibility criteria:
        1. User voted for the gauge before the epoch (last_vote < current_epoch)
        2. Vote is still active at the epoch (end > current_epoch)
        3. User has positive voting power (slope > 0)

        Args:
            protocol: Protocol name ("curve", "balancer", "frax", "pendle")
            gauge_address: Address of the gauge to check
            current_epoch: Timestamp of the epoch to check eligibility for
            block_number: Block number to query at
            chain_id: Optional - if provided with platform, fetches canonical block from oracle
            platform: Optional - VoteMarket platform address for oracle lookup

        Returns:
            List[EligibleUser]: Users who can claim rewards

        Raises:
            VoteMarketDataException: If blockchain data retrieval fails

        Example:
            >>> eligible = await service.get_eligible_users(
            ...     protocol="curve",
            ...     gauge_address="0x7E1444BA99dcdFfE8fBdb42C02fb0DA4",
            ...     current_epoch=1699920000,
            ...     block_number=18500000
            ... )
        """
        # Always round epoch to the day for consistency
        current_epoch = get_rounded_epoch(current_epoch)

        try:
            w3 = self.web3_service.w3

            # If chain and platform provided, fetch the canonical block number from oracle
            if chain_id is not None and platform is not None:
                from votemarket_toolkit.data.oracle import OracleService

                oracle_service = OracleService(self.chain_id)
                epoch_blocks = oracle_service.get_epochs_block(
                    chain_id, platform, [current_epoch]
                )
                block_number = epoch_blocks[current_epoch]
                if block_number == 0:
                    raise VoteMarketDataException(
                        f"No block set for epoch {current_epoch}"
                    )

            # Initialize multicall for efficient batch queries
            multicall = W3Multicall(w3)

            # Get the gauge controller contract address for this protocol
            gauge_controller = registry.get_gauge_controller(protocol)
            if not gauge_controller:
                raise VoteMarketDataException(
                    f"No gauge controller found for protocol: {protocol}"
                )
            gauge_controller_address = to_checksum_address(gauge_controller)

            # Step 1: Get all users who have EVER voted on this gauge
            gauge_votes = await votes_service.get_gauge_votes(
                protocol, gauge_address, block_number
            )
            unique_users = list(set(vote.user for vote in gauge_votes.votes))

            # Step 2: Query current vote status for each historical voter
            for user in unique_users:
                if protocol == "pendle":
                    # Pendle uses different contract interface
                    multicall.add(
                        W3Multicall.Call(
                            gauge_controller_address,
                            "getUserPoolVote(address,address)(uint256,uint256,uint256)",
                            [
                                to_checksum_address(user),
                                to_checksum_address(gauge_address),
                            ],
                        )
                    )
                    # Also get vote end time from veToken position
                    ve_address = registry.get_ve_address(protocol)
                    if ve_address:
                        multicall.add(
                            W3Multicall.Call(
                                to_checksum_address(ve_address),
                                "positionData(address)(uint128,uint128)",
                                [to_checksum_address(user)],
                            )
                        )
                else:
                    # Curve/Balancer/Frax use standard gauge controller interface
                    # Get last vote timestamp
                    multicall.add(
                        W3Multicall.Call(
                            gauge_controller_address,
                            "last_user_vote(address,address)(uint256)",
                            [
                                to_checksum_address(user),
                                to_checksum_address(gauge_address),
                            ],
                        )
                    )
                    # Get vote slopes: (slope, power, end_timestamp)
                    multicall.add(
                        W3Multicall.Call(
                            gauge_controller_address,
                            "vote_user_slopes(address,address)(int128,int128,uint256)",
                            [
                                to_checksum_address(user),
                                to_checksum_address(gauge_address),
                            ],
                        )
                    )

            # Step 3: Execute all queries in a single RPC call for efficiency
            results = multicall.call(block_number)

            eligible_users: List[EligibleUser] = []

            # Step 4: Filter to only ELIGIBLE users based on vote status
            for i in range(0, len(results), 2):
                user = unique_users[i // 2]

                if protocol == "pendle":
                    # Pendle data structure
                    last_vote = 0  # Pendle doesn't track last vote timestamp
                    power, _, slope = results[i]
                    end = results[i + 1][1]  # Position end timestamp
                else:
                    # Standard gauge controller data
                    last_vote = results[i]
                    slope, power, end = results[i + 1]

                # Check eligibility
                if (
                    current_epoch < end
                    and current_epoch > last_vote
                    and slope > 0
                ):
                    eligible_users.append(
                        EligibleUser(
                            user=user,
                            last_vote=last_vote,
                            slope=slope,
                            power=power,
                            end=end,
                        )
                    )

            return eligible_users
        except Exception as e:
            raise VoteMarketDataException(
                f"Error getting eligible users: {str(e)}"
            )
