const { ethers } = require("hardhat");

async function main() {
  // Get the contract instance
  const contractAddress = "YOUR_DEPLOYED_CONTRACT_ADDRESS";
  const FeedbackSystem = await ethers.getContractFactory("FeedbackSystem");
  const feedbackSystem = await FeedbackSystem.attach(contractAddress);

  const [owner, requester, provider1, provider2, aiValidator] = await ethers.getSigners();

  console.log("🎯 Feedback System Interaction Script");
  console.log("=====================================");

  // 1. Create a feedback request
  console.log("\n1️⃣ Creating feedback request...");
  const instructions = "Please provide feedback on our new voice recognition feature";
  const feedbacksWanted = 3;
  const bounty = ethers.utils.parseEther("0.1"); // 0.1 ETH

  const tx1 = await feedbackSystem.connect(requester).createFeedbackRequest(
    instructions,
    feedbacksWanted,
    { value: bounty }
  );
  await tx1.wait();
  console.log("✅ Feedback request created!");

  // 2. Submit feedbacks
  console.log("\n2️⃣ Submitting feedbacks...");
  
  const ipfsHashes = [
    "QmAudioFile1Hash123456789",
    "QmAudioFile2Hash987654321",
    "QmAudioFile3Hash456789123"
  ];

  for (let i = 0; i < ipfsHashes.length; i++) {
    const provider = i === 0 ? provider1 : provider2;
    const tx = await feedbackSystem.connect(provider).submitFeedback(1, ipfsHashes[i]);
    await tx.wait();
    console.log(`✅ Feedback ${i + 1} submitted by ${provider.address}`);
  }

  // 3. Validate feedbacks
  console.log("\n3️⃣ Validating feedbacks...");
  
  for (let i = 1; i <= 3; i++) {
    const isValid = i <= 2; // First 2 are valid, third is invalid
    const tx = await feedbackSystem.connect(aiValidator).validateFeedback(i, isValid);
    await tx.wait();
    console.log(`✅ Feedback ${i} validated as ${isValid ? 'VALID' : 'NOT_VALID'}`);
  }

  // 4. Check request status
  console.log("\n4️⃣ Checking request status...");
  const request = await feedbackSystem.getFeedbackRequest(1);
  const stats = await feedbackSystem.getRequestStats(1);
  
  console.log(` Request Status: ${request.status === 0 ? 'OPEN' : 'CLOSED'}`);
  console.log(`📈 Valid Feedbacks: ${stats.validCount}/${stats.wantedCount}`);
  console.log(`📉 Total Feedbacks: ${stats.totalCount}`);

  // 5. Claim bounties
  console.log("\n5️⃣ Claiming bounties...");
  
  for (let i = 1; i <= 2; i++) {
    const feedback = await feedbackSystem.getFeedback(i);
    if (feedback.status === 1) { // VALID
      const tx = await feedbackSystem.connect(feedback.provider).claimBounty(i);
      await tx.wait();
      console.log(`✅ Bounty claimed for feedback ${i} by ${feedback.provider}`);
    }
  }

  console.log("\n🎉 Interaction completed successfully!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  }); 