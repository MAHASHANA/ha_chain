# ha_chain Smart Contracts

## Architecture

ha_chain uses a modular smart contract architecture with abstract interfaces
and blockchain-specific implementations.

### Interfaces (`interfaces/`)

- **EscrowInterface**: Lock, release, and refund USDC for transfer escrow.
  Uses 2-of-3 multi-sig (sender, agent, platform) for authorization.
- **StakingInterface**: Agent collateral management. Stake, slash, and unstake.
- **SettlementInterface**: Batch settlement, platform fee collection, netting.

### Stellar Implementation (`stellar/`)

- **StellarEscrowAccount**: Multi-sig escrow accounts on Stellar testnet.
  Supports time-bounded pre-authorized refund transactions (24h timeout).
- **StellarStakingAccount**: Agent staking via Stellar claimable balances.
  Minimum stake: $100 USDC. Slashing reduces the claimable amount.
- **StellarSettlement**: Batch settlement using Stellar path payments for
  atomic multi-party transfers.

## USDC on Stellar

USDC is represented as a Stellar asset (asset code: USDC) issued by a
trusted anchor. All amounts are in USDC.

## Development

For testing, use the mock implementations in `tests/mocks/mock_blockchain.py`.
These simulate all blockchain operations in memory without network calls.
