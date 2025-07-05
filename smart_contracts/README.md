# Feedback System Smart Contract (Foundry)

A smart contract system for managing feedback requests with IPFS audio files and AI validation, built with Foundry.

## Features

- **Feedback Requests**: Anyone can create feedback requests with bounty and instructions
- **IPFS Audio Files**: Users submit feedback as IPFS audio file hashes
- **AI Validation**: AI agents can validate feedbacks as VALID or NOT_VALID
- **Automatic Closure**: Requests close when enough valid feedbacks are received
- **Bounty Distribution**: Valid feedback providers can claim their share of the bounty

## Quick Start

### Prerequisites
- [Foundry](https://getfoundry.sh/) installed

### Installation
```bash
# Install Foundry dependencies
make install

# Or manually:
forge install OpenZeppelin/openzeppelin-contracts --no-commit
forge install foundry-rs/forge-std --no-commit
```

### Environment Setup
```bash
cp .env.example .env
# Edit .env with your private key and RPC URLs
```

### Build
```bash
make build
# Or: forge build
```

### Test
```bash
make test
# Or: forge test
```

## Usage

### Deploy

#### Local Network
```bash
make deploy-local
```

#### Sepolia Testnet
```bash
make deploy-sepolia
```

#### Worldcoin Sepolia
```bash
make deploy-worldcoin
```

### Interact
```bash
make interact
```

## Contract Functions

### For Requesters
- `createFeedbackRequest()` - Create new feedback request with bounty
- `closeRequest()` - Manually close a request

### For Feedback Providers
- `submitFeedback()` - Submit feedback with IPFS audio hash
- `claimBounty()` - Claim bounty for valid feedback

### For AI Validators
- `validateFeedback()` - Mark feedback as VALID or NOT_VALID

### For Contract Owner
- `addAIValidator()` / `removeAIValidator()` - Manage AI validators
- `emergencyWithdraw()` - Emergency fund withdrawal

## Testing

### Run All Tests
```bash
make test
```

### Run Specific Test
```bash
make test-match TEST=test_CreateFeedbackRequest
```

### Verbose Testing
```bash
make test-v    # -vv
make test-vv   # -vvv
```

### Gas Report
```bash
make gas
```

### Coverage Report
```bash
make coverage
```

### Fuzz Testing
```bash
make fuzz
```

### Invariant Testing
```bash
make invariant
```

## Development

### Code Formatting
```bash
make fmt        # Format code
make fmt-check  # Check formatting
```

### Linting
```bash
make lint
```

### Clean Build
```bash
make clean
```

## Contract Architecture

### Core Components

1. **FeedbackRequest**: Contains request details, bounty, and status
2. **Feedback**: Contains feedback submission with IPFS hash and validation status
3. **AI Validators**: Authorized addresses that can validate feedbacks
4. **Bounty System**: Automatic distribution when requests close

### Workflow

1. **Request Creation**: User creates feedback request with bounty and instructions
2. **Feedback Submission**: Users submit IPFS audio file hashes
3. **AI Validation**: AI agents validate each feedback
4. **Automatic Closure**: Request closes when enough valid feedbacks
5. **Bounty Claims**: Valid feedback providers claim their share

## Security Features

- **Reentrancy Protection**: Prevents reentrancy attacks
- **Access Control**: Only AI validators can validate feedbacks
- **Input Validation**: Validates all inputs
- **Emergency Withdraw**: Owner can withdraw funds in emergency

## Gas Optimization

- Efficient storage patterns
- Minimal external calls
- Optimized loops and mappings

## License

MIT License 