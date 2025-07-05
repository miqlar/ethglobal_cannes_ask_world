// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/FeedbackSystem.sol";

contract FeedbackSystemTest is Test {
    FeedbackSystem public feedbackSystem;
    
    address public owner;
    address public requester;
    address public provider1;
    address public provider2;
    address public aiValidator;

    event FeedbackRequestCreated(
        uint256 indexed requestId,
        address indexed requester,
        string instructions,
        uint256 feedbacksWanted,
        uint256 totalBounty
    );

    event FeedbackSubmitted(
        uint256 indexed feedbackId,
        uint256 indexed requestId,
        address indexed provider,
        string ipfsAudioHash
    );

    event FeedbackValidated(
        uint256 indexed feedbackId,
        uint256 indexed requestId,
        FeedbackSystem.FeedbackStatus status,
        address validator
    );

    event RequestClosed(
        uint256 indexed requestId,
        uint256 validFeedbacksCount,
        uint256 totalBounty
    );

    event BountyPaid(
        uint256 indexed feedbackId,
        address indexed provider,
        uint256 amount
    );

    function setUp() public {
        owner = address(this);
        requester = makeAddr("requester");
        provider1 = makeAddr("provider1");
        provider2 = makeAddr("provider2");
        aiValidator = makeAddr("aiValidator");

        feedbackSystem = new FeedbackSystem();
        feedbackSystem.addAIValidator(aiValidator);

        // Fund accounts
        vm.deal(requester, 10 ether);
        vm.deal(provider1, 1 ether);
        vm.deal(provider2, 1 ether);
    }

    function test_Deployment() public view{
        assertEq(feedbackSystem.owner(), owner);
        assertTrue(feedbackSystem.isAIValidator(aiValidator));
    }

    function test_CreateFeedbackRequest() public {
        string memory instructions = "Please provide feedback on our new feature";
        uint256 feedbacksWanted = 3;
        uint256 bounty = 0.1 ether;

        vm.prank(requester);
        vm.expectEmit(true, true, false, true);
        emit FeedbackRequestCreated(1, requester, instructions, feedbacksWanted, bounty);
        
        feedbackSystem.createFeedbackRequest{value: bounty}(instructions, feedbacksWanted);

        FeedbackSystem.FeedbackRequest memory request = feedbackSystem.getFeedbackRequest(1);
        assertEq(request.requester, requester);
        assertEq(request.instructions, instructions);
        assertEq(request.feedbacksWanted, feedbacksWanted);
        assertEq(request.totalBounty, bounty);
        assertEq(uint256(request.status), 0); // OPEN
    }

    function test_CreateFeedbackRequest_ZeroBounty() public {
        vm.prank(requester);
        vm.expectRevert("Bounty must be greater than 0");
        feedbackSystem.createFeedbackRequest("Instructions", 1);
    }

    function test_SubmitFeedback() public {
        // Create request first
        vm.prank(requester);
        feedbackSystem.createFeedbackRequest{value: 0.1 ether}("Instructions", 2);

        string memory ipfsHash = "QmTestHash123";

        vm.prank(provider1);
        vm.expectEmit(true, true, true, true);
        emit FeedbackSubmitted(1, 1, provider1, ipfsHash);
        
        feedbackSystem.submitFeedback(1, ipfsHash);

        FeedbackSystem.Feedback memory feedback = feedbackSystem.getFeedback(1);
        assertEq(feedback.provider, provider1);
        assertEq(feedback.ipfsAudioHash, ipfsHash);
        assertEq(uint256(feedback.status), 0); // PENDING
    }

    function test_SubmitFeedback_Duplicate() public {
        // Create request first
        vm.prank(requester);
        feedbackSystem.createFeedbackRequest{value: 0.1 ether}("Instructions", 2);

        // Submit first feedback
        vm.prank(provider1);
        feedbackSystem.submitFeedback(1, "QmHash1");
        
        // Try to submit second feedback from same provider
        vm.prank(provider1);
        vm.expectRevert("Already submitted feedback for this request");
        feedbackSystem.submitFeedback(1, "QmHash2");
    }

    function test_ValidateFeedback_Valid() public {
        // Create request and submit feedback
        vm.prank(requester);
        feedbackSystem.createFeedbackRequest{value: 0.1 ether}("Instructions", 2);

        vm.prank(provider1);
        feedbackSystem.submitFeedback(1, "QmHash1");

        // Validate as valid
        vm.prank(aiValidator);
        vm.expectEmit(true, true, false, true);
        emit FeedbackValidated(1, 1, FeedbackSystem.FeedbackStatus.VALID, aiValidator);
        
        feedbackSystem.validateFeedback(1, true);

        FeedbackSystem.Feedback memory feedback = feedbackSystem.getFeedback(1);
        assertEq(uint256(feedback.status), 1); // VALID
    }

    function test_ValidateFeedback_Invalid() public {
        // Create request and submit feedback
        vm.prank(requester);
        feedbackSystem.createFeedbackRequest{value: 0.1 ether}("Instructions", 2);

        vm.prank(provider1);
        feedbackSystem.submitFeedback(1, "QmHash1");

        // Validate as invalid
        vm.prank(aiValidator);
        vm.expectEmit(true, true, false, true);
        emit FeedbackValidated(1, 1, FeedbackSystem.FeedbackStatus.NOT_VALID, aiValidator);
        
        feedbackSystem.validateFeedback(1, false);

        FeedbackSystem.Feedback memory feedback = feedbackSystem.getFeedback(1);
        assertEq(uint256(feedback.status), 2); // NOT_VALID
    }

    function test_ValidateFeedback_Unauthorized() public {
        // Create request and submit feedback
        vm.prank(requester);
        feedbackSystem.createFeedbackRequest{value: 0.1 ether}("Instructions", 2);

        vm.prank(provider1);
        feedbackSystem.submitFeedback(1, "QmHash1");

        // Try to validate without authorization
        vm.prank(provider1);
        vm.expectRevert("Not authorized");
        feedbackSystem.validateFeedback(1, true);
    }

    function test_RequestClosure_Automatic() public {
        // Create request
        vm.prank(requester);
        feedbackSystem.createFeedbackRequest{value: 0.1 ether}("Instructions", 2);

        // Submit feedbacks
        vm.prank(provider1);
        feedbackSystem.submitFeedback(1, "QmHash1");
        vm.prank(provider2);
        feedbackSystem.submitFeedback(1, "QmHash2");

        // Validate as valid
        vm.prank(aiValidator);
        feedbackSystem.validateFeedback(1, true);
        vm.prank(aiValidator);
        feedbackSystem.validateFeedback(2, true);

        // Check if request is closed
        FeedbackSystem.FeedbackRequest memory request = feedbackSystem.getFeedbackRequest(1);
        assertEq(uint256(request.status), 1); // CLOSED
    }

    function test_RequestClosure_Manual() public {
        // Create request
        vm.prank(requester);
        feedbackSystem.createFeedbackRequest{value: 0.1 ether}("Instructions", 2);

        // Close manually
        vm.prank(requester);
        vm.expectEmit(true, false, false, true);
        emit RequestClosed(1, 0, 0.1 ether);
        
        feedbackSystem.closeRequest(1);

        FeedbackSystem.FeedbackRequest memory request = feedbackSystem.getFeedbackRequest(1);
        assertEq(uint256(request.status), 1); // CLOSED
    }

    function test_ClaimBounty() public {
        // Create request
        vm.prank(requester);
        feedbackSystem.createFeedbackRequest{value: 0.1 ether}("Instructions", 2);

        // Submit and validate feedback
        vm.prank(provider1);
        feedbackSystem.submitFeedback(1, "QmHash1");
        vm.prank(aiValidator);
        feedbackSystem.validateFeedback(1, true);

        // Claim bounty
        uint256 initialBalance = provider1.balance;
        vm.prank(provider1);
        vm.expectEmit(true, true, false, true);
        emit BountyPaid(1, provider1, 0.05 ether);
        
        feedbackSystem.claimBounty(1);

        assertEq(provider1.balance, initialBalance + 0.05 ether);
    }

    function test_ClaimBounty_InvalidFeedback() public {
        // Create request
        vm.prank(requester);
        feedbackSystem.createFeedbackRequest{value: 0.1 ether}("Instructions", 2);

        // Submit and validate as invalid
        vm.prank(provider1);
        feedbackSystem.submitFeedback(1, "QmHash1");
        vm.prank(aiValidator);
        feedbackSystem.validateFeedback(1, false);

        // Try to claim bounty
        vm.prank(provider1);
        vm.expectRevert("Feedback not valid");
        feedbackSystem.claimBounty(1);
    }

    function test_GetRequestStats() public {
        // Create request
        vm.prank(requester);
        feedbackSystem.createFeedbackRequest{value: 0.1 ether}("Instructions", 3);

        // Submit feedbacks
        vm.prank(provider1);
        feedbackSystem.submitFeedback(1, "QmHash1");
        vm.prank(provider2);
        feedbackSystem.submitFeedback(1, "QmHash2");

        // Validate one as valid
        vm.prank(aiValidator);
        feedbackSystem.validateFeedback(1, true);

        // Get stats
        (uint256 validCount, uint256 totalCount, uint256 wantedCount, bool isComplete) = 
            feedbackSystem.getRequestStats(1);

        assertEq(validCount, 1);
        assertEq(totalCount, 2);
        assertEq(wantedCount, 3);
        assertEq(isComplete, false);
    }

    function test_AddRemoveAIValidator() public {
        address newValidator = makeAddr("newValidator");

        // Add validator
        feedbackSystem.addAIValidator(newValidator);
        assertTrue(feedbackSystem.isAIValidator(newValidator));

        // Remove validator
        feedbackSystem.removeAIValidator(newValidator);
        assertFalse(feedbackSystem.isAIValidator(newValidator));
    }

    function test_GetUserRequests() public {
        // Create requests
        vm.prank(requester);
        feedbackSystem.createFeedbackRequest{value: 0.1 ether}("Instructions1", 1);
        vm.prank(requester);
        feedbackSystem.createFeedbackRequest{value: 0.1 ether}("Instructions2", 1);

        uint256[] memory requests = feedbackSystem.getUserRequests(requester);
        assertEq(requests.length, 2);
        assertEq(requests[0], 1);
        assertEq(requests[1], 2);
    }

    function test_GetUserFeedbacks() public {
        // Create request
        vm.prank(requester);
        feedbackSystem.createFeedbackRequest{value: 0.1 ether}("Instructions", 2);

        // Submit feedbacks
        vm.prank(provider1);
        feedbackSystem.submitFeedback(1, "QmHash1");
        vm.prank(provider2);
        feedbackSystem.submitFeedback(1, "QmHash2");

        uint256[] memory feedbacks1 = feedbackSystem.getUserFeedbacks(provider1);
        uint256[] memory feedbacks2 = feedbackSystem.getUserFeedbacks(provider2);

        assertEq(feedbacks1.length, 1);
        assertEq(feedbacks2.length, 1);
        assertEq(feedbacks1[0], 1);
        assertEq(feedbacks2[0], 2);
    }
} 