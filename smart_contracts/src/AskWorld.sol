// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title AskWorld
 * @dev A smart contract for managing questions with audio answers and AI validation
 */
contract AskWorld is Ownable, ReentrancyGuard {

    // Enums
    enum AnswerStatus {
        PENDING,        // 0 - Waiting for AI validation
        REJECTED,       // 1 - AI rejected the answer
        APPROVED        // 2 - AI approved and paid out
    }

    enum QuestionStatus {
        OPEN,       // 0 - Accepting answers
        CLOSED,     // 1 - Enough valid answers received
        CANCELLED   // 2 - Question was cancelled
    }

    // Structs
    struct Question {
        uint256 id;
        address asker;
        string prompt;
        uint256 answersNeeded;
        uint256 bounty;
        uint256 validAnswersCount;
        uint256 totalAnswersCount;
        QuestionStatus status;
        uint256 createdAt;
        uint256 closedAt;
        bool exists;
    }

    struct Answer {
        uint256 id;
        uint256 questionId;
        address provider;
        string audioHash;
        AnswerStatus status;
        uint256 submittedAt;
        uint256 validatedAt;
        bool exists;
    }

    // State variables
    uint256 private _questionIds = 0;
    uint256 private _answerIds = 0;
    
    mapping(uint256 => Question) public questions;
    mapping(uint256 => Answer) public answers;
    mapping(uint256 => uint256[]) public questionAnswers; // questionId => answerIds[]
    mapping(address => uint256[]) public userQuestions; // user => questionIds[]
    mapping(address => uint256[]) public userAnswers; // user => answerIds[]
    mapping(address => bool) public aiValidators;

    // Events
    event QuestionAsked(
        uint256 indexed questionId,
        address indexed asker,
        string prompt,
        uint256 answersNeeded,
        uint256 bounty
    );

    event AnswerSubmitted(
        uint256 indexed answerId,
        uint256 indexed questionId,
        address indexed provider,
        string audioHash
    );

    event AnswerValidated(
        uint256 indexed answerId,
        uint256 indexed questionId,
        AnswerStatus status,
        address validator
    );

    event QuestionClosed(
        uint256 indexed questionId,
        uint256 validAnswersCount,
        uint256 totalBounty
    );

    event BountyPaid(
        uint256 indexed answerId,
        address indexed provider,
        uint256 amount
    );

    // Modifiers
    modifier onlyAIValidator() {
        require(msg.sender == owner() || isAIValidator(msg.sender), "Not authorized");
        _;
    }

    modifier questionExists(uint256 questionId) {
        require(questions[questionId].exists, "Question does not exist");
        _;
    }

    modifier answerExists(uint256 answerId) {
        require(answers[answerId].exists, "Answer does not exist");
        _;
    }

    modifier questionOpen(uint256 questionId) {
        require(questions[questionId].status == QuestionStatus.OPEN, "Question not open");
        _;
    }

    constructor() Ownable(msg.sender) {
        aiValidators[msg.sender] = true; // Owner is default AI validator
    }

    /**
     * @dev Ask a new question
     * @param prompt The question prompt
     * @param answersNeeded Number of valid answers needed
     */
    function askQuestion(
        string memory prompt,
        uint256 answersNeeded
    ) external payable {
        require(msg.value > 0, "Bounty must be greater than 0");
        require(answersNeeded > 0, "Must need at least 1 answer");
        require(bytes(prompt).length > 0, "Prompt cannot be empty");

        _questionIds++;
        uint256 questionId = _questionIds;

        Question memory newQuestion = Question({
            id: questionId,
            asker: msg.sender,
            prompt: prompt,
            answersNeeded: answersNeeded,
            bounty: msg.value,
            validAnswersCount: 0,
            totalAnswersCount: 0,
            status: QuestionStatus.OPEN,
            createdAt: block.timestamp,
            closedAt: 0,
            exists: true
        });

        questions[questionId] = newQuestion;
        userQuestions[msg.sender].push(questionId);

        emit QuestionAsked(
            questionId,
            msg.sender,
            prompt,
            answersNeeded,
            msg.value
        );
    }

    /**
     * @dev Submit an answer to a question
     * @param questionId ID of the question
     * @param audioHash IPFS hash of the audio file
     */
    function submitAnswer(
        uint256 questionId,
        string memory audioHash
    ) external questionExists(questionId) questionOpen(questionId) {
        require(bytes(audioHash).length > 0, "Audio hash cannot be empty");
        
        // Check if user already submitted answer for this question
        uint256[] memory userAnswerIds = userAnswers[msg.sender];
        for (uint256 i = 0; i < userAnswerIds.length; i++) {
            require(
                answers[userAnswerIds[i]].questionId != questionId,
                "Already submitted answer for this question"
            );
        }

        _answerIds++;
        uint256 answerId = _answerIds;

        Answer memory newAnswer = Answer({
            id: answerId,
            questionId: questionId,
            provider: msg.sender,
            audioHash: audioHash,
            status: AnswerStatus.PENDING,
            submittedAt: block.timestamp,
            validatedAt: 0,
            exists: true
        });

        answers[answerId] = newAnswer;
        questionAnswers[questionId].push(answerId);
        userAnswers[msg.sender].push(answerId);
        
        questions[questionId].totalAnswersCount++;

        emit AnswerSubmitted(answerId, questionId, msg.sender, audioHash);
    }

    /**
     * @dev Validate an answer (only AI validators)
     * @param answerId ID of the answer to validate
     * @param isValid Whether the answer is valid
     */
    function validateAnswer(
        uint256 answerId,
        bool isValid
    ) external onlyAIValidator answerExists(answerId) nonReentrant {
        Answer storage answer = answers[answerId];
        require(answer.status == AnswerStatus.PENDING, "Answer already processed");

        if (isValid) {
            answer.status = AnswerStatus.APPROVED;
            answer.validatedAt = block.timestamp;
            
            questions[answer.questionId].validAnswersCount++;
            
            // Pay the bounty immediately
            uint256 bountyPerAnswer = questions[answer.questionId].bounty / 
                                     questions[answer.questionId].answersNeeded;
            
            (bool success, ) = payable(answer.provider).call{value: bountyPerAnswer}("");
            require(success, "Transfer failed");

            emit BountyPaid(answerId, answer.provider, bountyPerAnswer);
            
            // Check if question should be closed
            if (questions[answer.questionId].validAnswersCount >= 
                questions[answer.questionId].answersNeeded) {
                _closeQuestion(answer.questionId);
            }
        } else {
            answer.status = AnswerStatus.REJECTED;
            answer.validatedAt = block.timestamp;
        }

        emit AnswerValidated(answerId, answer.questionId, answer.status, msg.sender);
    }

    /**
     * @dev Close a question manually (only asker or owner)
     * @param questionId ID of the question to close
     */
    function closeQuestion(uint256 questionId) 
        external 
        questionExists(questionId) 
        questionOpen(questionId) 
    {
        Question storage question = questions[questionId];
        require(
            msg.sender == question.asker || msg.sender == owner(),
            "Only asker or owner can close"
        );
        
        _closeQuestion(questionId);
    }

    // AI Validator Management
    function addAIValidator(address validator) external onlyOwner {
        aiValidators[validator] = true;
    }

    function removeAIValidator(address validator) external onlyOwner {
        aiValidators[validator] = false;
    }

    function isAIValidator(address validator) public view returns (bool) {
        return aiValidators[validator];
    }

    // Emergency functions
    function emergencyWithdraw() external onlyOwner {
        (bool success, ) = payable(owner()).call{value: address(this).balance}("");
        require(success, "Transfer failed");
    }

    // Internal functions
    function _closeQuestion(uint256 questionId) internal {
        Question storage question = questions[questionId];
        question.status = QuestionStatus.CLOSED;
        question.closedAt = block.timestamp;

        emit QuestionClosed(questionId, question.validAnswersCount, question.bounty);
    }

    // View functions
    function getQuestion(uint256 questionId) 
        external 
        view 
        questionExists(questionId) 
        returns (Question memory) 
    {
        return questions[questionId];
    }

    function getAnswer(uint256 answerId) 
        external 
        view 
        answerExists(answerId) 
        returns (Answer memory) 
    {
        return answers[answerId];
    }

    function getQuestionAnswers(uint256 questionId) 
        external 
        view 
        questionExists(questionId) 
        returns (uint256[] memory) 
    {
        return questionAnswers[questionId];
    }

    function getUserQuestions(address user) 
        external 
        view 
        returns (uint256[] memory) 
    {
        return userQuestions[user];
    }

    function getUserAnswers(address user) 
        external 
        view 
        returns (uint256[] memory) 
    {
        return userAnswers[user];
    }

    function getQuestionStats(uint256 questionId) 
        external 
        view 
        questionExists(questionId) 
        returns (
            uint256 validCount,
            uint256 totalCount,
            uint256 neededCount,
            bool isComplete
        ) 
    {
        Question storage question = questions[questionId];
        return (
            question.validAnswersCount,
            question.totalAnswersCount,
            question.answersNeeded,
            question.validAnswersCount >= question.answersNeeded
        );
    }

    function getOpenQuestions() 
        external 
        view 
        returns (uint256[] memory) 
    {
        uint256[] memory tempQuestions = new uint256[](_questionIds);
        uint256 count = 0;
        
        for (uint256 i = 1; i <= _questionIds; i++) {
            if (questions[i].exists && 
                questions[i].status == QuestionStatus.OPEN &&
                questions[i].validAnswersCount < questions[i].answersNeeded) {
                tempQuestions[count] = i;
                count++;
            }
        }
        
        // Create properly sized array
        uint256[] memory result = new uint256[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = tempQuestions[i];
        }
        
        return result;
    }
} 