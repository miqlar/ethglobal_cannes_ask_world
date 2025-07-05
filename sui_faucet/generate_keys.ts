import { Ed25519Keypair } from '@mysten/sui.js/keypairs/ed25519';

async function generateKeys() {
  try {
    // Generate a new keypair
    const keypair = new Ed25519Keypair();
    const address = keypair.getPublicKey().toSuiAddress();
    const { privateKey } = keypair.export();

    console.log("Generated Sui wallet:");
    console.log("Address:     ", address);
    console.log("Private Key: ", privateKey);
    console.log("Public Key:  ", keypair.getPublicKey().toBase64());

    return { address, privateKey, publicKey: keypair.getPublicKey().toBase64() };
  } catch (error) {
    console.error("Error generating keys:", error);
    throw error;
  }
}

// CLI usage
if (typeof require !== 'undefined' && require.main === module) {
  generateKeys()
    .then(() => {
      console.log("Key generation completed successfully");
      process.exit(0);
    })
    .catch((error) => {
      console.error("Key generation failed:", error);
      process.exit(1);
    });
}

export { generateKeys }; 