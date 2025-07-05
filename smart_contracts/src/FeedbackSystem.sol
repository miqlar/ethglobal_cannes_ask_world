// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title FeedbackSystem
 * @dev A smart contract for managing feedback requests with IPFS audio files and AI validation
 */
contract FeedbackSystem is Ownable, ReentrancyGuard {

    // Enums
    enum FeedbackStatus {
        PENDING,    // 0 - Waiting for AI validation
        VALID,      // 1 - AI validated as good feedback
        NOT_VALID,  // 2 - AI rejected the feedback
        PAID        // 3 - Feedback has been paid out
    }

    enum RequestStatus {
        OPEN,       // 0 - Accepting feedback submissions
        CLOSED,     // 1 - Enough valid feedbacks received
        CANCELLED   // 2 - Request was cancelled
    }

    // Structs
    struct FeedbackRequest {
        uint256 id;
        address requester;
        string instructions;
        uint256 feedbacksWanted;
        uint256 totalBounty;
        uint256 validFeedbacksCount;
        uint256 totalFeedbacksCount;
        RequestStatus status;
        uint256 createdAt;
        uint256 closedAt;
        bool exists;
    }

    struct Feedback {
        uint256 id;
        uint256 requestId;
        address provider;
        string ipfsAudioHash;
        FeedbackStatus status;
        uint256 submittedAt;
        uint256 validatedAt;
        bool exists;
    }

    // State variables
    uint256 private _requestIds = 0;
    uint256 private _feedbackIds = 0;
    
    mapping(uint256 => FeedbackRequest) public feedbackRequests;
    mapping(uint256 => Feedback) public feedbacks;
    mapping(uint256 => uint256[]) public requestFeedbacks; // requestId => feedbackIds[]
    mapping(address => uint256[]) public userRequests; // user => requestIds[]
    mapping(address => uint256[]) public userFeedbacks; // user => feedbackIds[]

    // Events
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
        FeedbackStatus status,
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

    // Modifiers
    modifier onlyAIValidator() {
        require(msg.sender == owner() || isAIValidator(msg.sender), "Not authorized");
        _;
    }

    modifier requestExists(uint256 requestId) {
        require(feedbackRequests[requestId].exists, "Request does not exist");
        _;
    }

    modifier feedbackExists(uint256 feedbackId) {
        require(feedbacks[feedbackId].exists, "Feedback does not exist");
        _;
    }

    modifier requestOpen(uint256 requestId) {
        require(feedbackRequests[requestId].status == RequestStatus.OPEN, "Request not open");
        _;
    }

    // AI validators mapping
    mapping(address => bool) public aiValidators;

    constructor() Ownable(msg.sender) {
        aiValidators[msg.sender] = true; // Owner is default AI validator
    }

    /**
     * @dev Create a new feedback request
     * @param instructions Instructions for the feedback
     * @param feedbacksWanted Number of valid feedbacks needed
     */
    function createFeedbackRequest(
        string memory instructions,
        uint256 feedbacksWanted
    ) external payable {
        require(msg.value > 0, "Bounty must be greater than 0");
        require(feedbacksWanted > 0, "Must want at least 1 feedback");
        require(bytes(instructions).length > 0, "Instructions cannot be empty");

        _requestIds++;
        uint256 requestId = _requestIds;

        FeedbackRequest memory newRequest = FeedbackRequest({
            id: requestId,
            requester: msg.sender,
            instructions: instructions,
            feedbacksWanted: feedbacksWanted,
            totalBounty: msg.value,
            validFeedbacksCount: 0,
            totalFeedbacksCount: 0,
            status: RequestStatus.OPEN,
            createdAt: block.timestamp,
            closedAt: 0,
            exists: true
        });

        feedbackRequests[requestId] = newRequest;
        userRequests[msg.sender].push(requestId);

        emit FeedbackRequestCreated(
            requestId,
            msg.sender,
            instructions,
            feedbacksWanted,
            msg.value
        );
    }

    /**
     * @dev Submit feedback for a request
     * @param requestId ID of the feedback request
     * @param ipfsAudioHash IPFS hash of the audio file
     */
    function submitFeedback(
        uint256 requestId,
        string memory ipfsAudioHash
    ) external requestExists(requestId) requestOpen(requestId) {
        require(bytes(ipfsAudioHash).length > 0, "IPFS hash cannot be empty");
        
        // Check if user already submitted feedback for this request
        uint256[] memory userFeedbackIds = userFeedbacks[msg.sender];
        for (uint256 i = 0; i < userFeedbackIds.length; i++) {
            require(
                feedbacks[userFeedbackIds[i]].requestId != requestId,
                "Already submitted feedback for this request"
            );
        }

        _feedbackIds++;
        uint256 feedbackId = _feedbackIds;

        Feedback memory newFeedback = Feedback({
            id: feedbackId,
            requestId: requestId,
            provider: msg.sender,
            ipfsAudioHash: ipfsAudioHash,
            status: FeedbackStatus.PENDING,
            submittedAt: block.timestamp,
            validatedAt: 0,
            exists: true
        });

        feedbacks[feedbackId] = newFeedback;
        requestFeedbacks[requestId].push(feedbackId);
        userFeedbacks[msg.sender].push(feedbackId);
        
        feedbackRequests[requestId].totalFeedbacksCount++;

        emit FeedbackSubmitted(feedbackId, requestId, msg.sender, ipfsAudioHash);
    }

    /**
     * @dev Validate feedback (only AI validators)
     * @param feedbackId ID of the feedback to validate
     * @param isValid Whether the feedback is valid
     */
    function validateFeedback(
        uint256 feedbackId,
        bool isValid
    ) external onlyAIValidator feedbackExists(feedbackId) {
        Feedback storage feedback = feedbacks[feedbackId];
        require(feedback.status == FeedbackStatus.PENDING, "Feedback already validated");

        FeedbackStatus status = isValid ? FeedbackStatus.VALID : FeedbackStatus.NOT_VALID;
        feedback.status = status;
        feedback.validatedAt = block.timestamp;

        if (isValid) {
            feedbackRequests[feedback.requestId].validFeedbacksCount++;
            
            // Check if request should be closed
            if (feedbackRequests[feedback.requestId].validFeedbacksCount >= 
                feedbackRequests[feedback.requestId].feedbacksWanted) {
                _closeRequest(feedback.requestId);
            }
        }

        emit FeedbackValidated(feedbackId, feedback.requestId, status, msg.sender);
    }

    /**
     * @dev Close a request manually (only requester or owner)
     * @param requestId ID of the request to close
     */
    function closeRequest(uint256 requestId) 
        external 
        requestExists(requestId) 
        requestOpen(requestId) 
    {
        FeedbackRequest storage request = feedbackRequests[requestId];
        require(
            msg.sender == request.requester || msg.sender == owner(),
            "Only requester or owner can close"
        );
        
        _closeRequest(requestId);
    }

    /**
     * @dev Claim bounty for valid feedback
     * @param feedbackId ID of the feedback to claim for
     */
    function claimBounty(uint256 feedbackId) 
        external 
        nonReentrant 
        feedbackExists(feedbackId) 
    {
        Feedback storage feedback = feedbacks[feedbackId];
        require(feedback.provider == msg.sender, "Not the feedback provider");
        require(feedback.status == FeedbackStatus.VALID, "Feedback not valid");
        require(feedback.status != FeedbackStatus.PAID, "Already claimed");

        feedback.status = FeedbackStatus.PAID;

        uint256 bountyPerFeedback = feedbackRequests[feedback.requestId].totalBounty / 
                                   feedbackRequests[feedback.requestId].feedbacksWanted;
        
        (bool success, ) = payable(msg.sender).call{value: bountyPerFeedback}("");
        require(success, "Transfer failed");

        emit BountyPaid(feedbackId, msg.sender, bountyPerFeedback);
    }

    /**
     * @dev Get all feedbacks for a request
     * @param requestId ID of the request
     * @return Array of feedback IDs
     */
    function getRequestFeedbacks(uint256 requestId) 
        external 
        view 
        requestExists(requestId) 
        returns (uint256[] memory) 
    {
        return requestFeedbacks[requestId];
    }

    /**
     * @dev Get all requests by a user
     * @param user Address of the user
     * @return Array of request IDs
     */
    function getUserRequests(address user) 
        external 
        view 
        returns (uint256[] memory) 
    {
        return userRequests[user];
    }

    /**
     * @dev Get all feedbacks by a user
     * @param user Address of the user
     * @return Array of feedback IDs
     */
    function getUserFeedbacks(address user) 
        external 
        view 
        returns (uint256[] memory) 
    {
        return userFeedbacks[user];
    }

    /**
     * @dev Add AI validator
     * @param validator Address of the AI validator
     */
    function addAIValidator(address validator) external onlyOwner {
        aiValidators[validator] = true;
    }

    /**
     * @dev Remove AI validator
     * @param validator Address of the AI validator
     */
    function removeAIValidator(address validator) external onlyOwner {
        aiValidators[validator] = false;
    }

    /**
     * @dev Check if address is AI validator
     * @param validator Address to check
     * @return True if AI validator
     */
    function isAIValidator(address validator) public view returns (bool) {
        return aiValidators[validator];
    }

    /**
     * @dev Emergency withdraw (only owner)
     */
    function emergencyWithdraw() external onlyOwner {
        (bool success, ) = payable(owner()).call{value: address(this).balance}("");
        require(success, "Transfer failed");
    }

    // Internal functions
    function _closeRequest(uint256 requestId) internal {
        FeedbackRequest storage request = feedbackRequests[requestId];
        request.status = RequestStatus.CLOSED;
        request.closedAt = block.timestamp;

        emit RequestClosed(requestId, request.validFeedbacksCount, request.totalBounty);
    }

    // View functions for better UX
    function getFeedbackRequest(uint256 requestId) 
        external 
        view 
        requestExists(requestId) 
        returns (FeedbackRequest memory) 
    {
        return feedbackRequests[requestId];
    }

    function getFeedback(uint256 feedbackId) 
        external 
        view 
        feedbackExists(feedbackId) 
        returns (Feedback memory) 
    {
        return feedbacks[feedbackId];
    }

    function getRequestStats(uint256 requestId) 
        external 
        view 
        requestExists(requestId) 
        returns (
            uint256 validCount,
            uint256 totalCount,
            uint256 wantedCount,
            bool isComplete
        ) 
    {
        FeedbackRequest storage request = feedbackRequests[requestId];
        return (
            request.validFeedbacksCount,
            request.totalFeedbacksCount,
            request.feedbacksWanted,
            request.validFeedbacksCount >= request.feedbacksWanted
        );
    }
} 