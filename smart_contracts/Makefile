.PHONY: build test deploy clean install

# Build the project
build:
	forge build

# Run tests
test:
	forge test

# Run tests with verbose output
test-v:
	forge test -vv

# Run tests with very verbose output
test-vv:
	forge test -vvv

# Run specific test
test-match:
	forge test --match-test $(TEST)

# Deploy to local network
deploy-local:
	forge script script/Deploy.s.sol --rpc-url http://localhost:8545 --broadcast

# Deploy to Sepolia
deploy-sepolia:
	forge script script/Deploy.s.sol --rpc-url $(SEPOLIA_RPC_URL) --broadcast --verify

# Deploy to Worldcoin Sepolia
deploy-worldcoin:
	forge script script/Deploy.s.sol --rpc-url $(WORLDCOIN_SEPOLIA_RPC_URL) --broadcast --verify

# Interact with deployed contract
interact:
	forge script script/Interact.s.sol --rpc-url $(RPC_URL) --broadcast

# Clean build artifacts
clean:
	forge clean

# Install dependencies
install:
	./install.sh

# Format code
fmt:
	forge fmt

# Check code formatting
fmt-check:
	forge fmt --check

# Lint code
lint:
	forge build --sizes

# Gas report
gas:
	forge test --gas-report

# Coverage report
coverage:
	forge coverage --report lcov
	genhtml lcov.info --output-dir coverage

# Fuzz testing
fuzz:
	forge test --fuzz-runs 10000

# Invariant testing
invariant:
	forge test --invariant-runs 1000

# Help
help:
	@echo "Available commands:"
	@echo "  build          - Build the project"
	@echo "  test           - Run tests"
	@echo "  test-v         - Run tests with verbose output"
	@echo "  test-vv        - Run tests with very verbose output"
	@echo "  test-match     - Run specific test (TEST=testName)"
	@echo "  deploy-local   - Deploy to local network"
	@echo "  deploy-sepolia - Deploy to Sepolia"
	@echo "  deploy-worldcoin - Deploy to Worldcoin Sepolia"
	@echo "  interact       - Interact with deployed contract"
	@echo "  clean          - Clean build artifacts"
	@echo "  install        - Install dependencies"
	@echo "  fmt            - Format code"
	@echo "  fmt-check      - Check code formatting"
	@echo "  lint           - Lint code"
	@echo "  gas            - Generate gas report"
	@echo "  coverage       - Generate coverage report"
	@echo "  fuzz           - Run fuzz testing"
	@echo "  invariant      - Run invariant testing"
	@echo "  help           - Show this help" 