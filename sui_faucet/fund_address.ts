import { getFaucetHost, requestSuiFromFaucetV0 } from '@mysten/sui.js/faucet';

async function fundAddress(address: string, network: 'testnet' | 'devnet' = 'testnet') {
  try {
    console.log(`Funding address: ${address}`);
    console.log(`Network: ${network}`);

    // Request tokens from faucet
    const response = await requestSuiFromFaucetV0({
      host: getFaucetHost(network),
      recipient: address,
    });

    console.log("Faucet response:", response);
    console.log(`Successfully funded address ${address} on ${network}`);
    
    return { address, response };
  } catch (error) {
    console.error("Error funding address:", error);
    throw error;
  }
}

// CLI usage
if (typeof require !== 'undefined' && require.main === module) {
  const address = process.argv[2];
  const network = process.argv[3] as 'testnet' | 'devnet' || 'testnet';

  if (!address) {
    console.error("Usage: ts-node fund_address.ts <sui_address> [testnet|devnet]");
    console.error("Example: ts-node fund_address.ts 0x1234567890abcdef... testnet");
    process.exit(1);
  }

  fundAddress(address, network)
    .then(() => {
      console.log("Funding completed successfully");
      process.exit(0);
    })
    .catch((error) => {
      console.error("Funding failed:", error);
      process.exit(1);
    });
}

export { fundAddress }; 