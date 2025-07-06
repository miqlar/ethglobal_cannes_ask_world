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
        UNANSWERED,    // 0 - User has not answered
        PENDING,       // 1 - Waiting for AI validation
        APPROVED,      // 2 - AI approved and paid out
        REJECTED       // 3 - AI rejected the answer
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
        address provider;
        string blobId;  // Walrus blob ID instead of IPFS hash
        AnswerStatus status;
        uint256 submittedAt;
        uint256 validatedAt;
    }

    // State variables
    uint256 private _questionIds = 0;
    
    mapping(uint256 => Question) public questions;
    mapping(uint256 => Answer[]) public questionAnswers; // questionId => Answer[]
    mapping(address => uint256[]) public userQuestions; // user => questionIds[]
    mapping(address => mapping(uint256 => uint256[])) public userAnswers; // user => questionId => answerIndices[]
    mapping(address => bool) public aiValidators;
    
    // Global counters
    uint256 public totalQuestions;
    uint256 public totalAnswers;
    uint256 public totalValidAnswers;

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
        string blobId
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

    event AnswerProviderChanged(
        uint256 indexed answerId,
        uint256 indexed questionId,
        address indexed oldProvider,
        address newProvider,
        address changer
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
        totalQuestions++;

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
     * @param blobId Walrus blob ID of the audio file
     */
    function submitAnswer(
        uint256 questionId,
        string memory blobId
    ) external questionExists(questionId) questionOpen(questionId) {
        require(bytes(blobId).length > 0, "Blob ID cannot be empty");
        
        // HACKATHON MODE: Removed constraint to allow multiple answers from same user for testing

        Answer memory newAnswer = Answer({
            provider: msg.sender,
            blobId: blobId,
            status: AnswerStatus.PENDING,
            submittedAt: block.timestamp,
            validatedAt: 0
        });

        questionAnswers[questionId].push(newAnswer);
        uint256 answerIndex = questionAnswers[questionId].length - 1;
        userAnswers[msg.sender][questionId].push(answerIndex);
        
        questions[questionId].totalAnswersCount++;
        totalAnswers++;

        emit AnswerSubmitted(answerIndex, questionId, msg.sender, blobId);
    }

    /**
     * @dev Validate an answer (only AI validators)
     * @param questionId ID of the question containing the answer
     * @param answerIndex Index of the answer within the question
     * @param isValid Whether the answer is valid
     */
    function validateAnswer(
        uint256 questionId,
        uint256 answerIndex,
        bool isValid
    ) external onlyAIValidator questionExists(questionId) nonReentrant {
        require(answerIndex < questionAnswers[questionId].length, "Answer does not exist");
        require(questionAnswers[questionId][answerIndex].status == AnswerStatus.PENDING, "Answer already processed");

        Answer storage answer = questionAnswers[questionId][answerIndex];

        if (isValid) {
            answer.status = AnswerStatus.APPROVED;
            answer.validatedAt = block.timestamp;
            
            questions[questionId].validAnswersCount++;
            totalValidAnswers++;
            
            // Pay the bounty immediately
            uint256 bountyPerAnswer = questions[questionId].bounty / 
                                     questions[questionId].answersNeeded;
            
            (bool success, ) = payable(answer.provider).call{value: bountyPerAnswer}("");
            require(success, "Transfer failed");

            emit BountyPaid(answerIndex, answer.provider, bountyPerAnswer);
            
            // Check if question should be closed
            if (questions[questionId].validAnswersCount >= 
                questions[questionId].answersNeeded) {
                _closeQuestion(questionId);
            }
        } else {
            answer.status = AnswerStatus.REJECTED;
            answer.validatedAt = block.timestamp;
        }

        emit AnswerValidated(answerIndex, questionId, answer.status, msg.sender);
    }

    /**
     * @dev Overwrite the state of any answer (only owner)
     * HACKATHON DEMO: This function allows easy answer state modification for demo purposes
     * @param questionId ID of the question
     * @param answerIndex Index of the answer to overwrite
     * @param newStatus New status for the answer (0=PENDING, 1=APPROVED, 2=REJECTED, 3=PROCESSING)
     * @param newBlobId New blob ID (optional, empty string to keep existing)
     * @param newProvider New provider address (optional, zero address to keep existing)
     */
    function owner_overwriteAnswerState(
        uint256 questionId,
        uint256 answerIndex,
        uint8 newStatus,
        string memory newBlobId,
        address newProvider
    ) external onlyOwner questionExists(questionId) {
        require(answerIndex < questionAnswers[questionId].length, "Answer does not exist");
        require(newStatus <= 3, "Invalid status (0=PENDING, 1=APPROVED, 2=REJECTED, 3=PROCESSING)");
        
        Answer storage answer = questionAnswers[questionId][answerIndex];
        AnswerStatus oldStatus = answer.status;
        address oldProvider = answer.provider;
        
        // Update provider if provided (not zero address)
        if (newProvider != address(0) && newProvider != oldProvider) {
            // Remove the answer from the old provider's mapping
            uint256[] storage oldProviderAnswers = userAnswers[oldProvider][questionId];
            for (uint256 i = 0; i < oldProviderAnswers.length; i++) {
                if (oldProviderAnswers[i] == answerIndex) {
                    // Remove this answer index from the old provider's list
                    oldProviderAnswers[i] = oldProviderAnswers[oldProviderAnswers.length - 1];
                    oldProviderAnswers.pop();
                    break;
                }
            }
            
            // Add the answer to the new provider's mapping
            userAnswers[newProvider][questionId].push(answerIndex);
            
            // Update the answer's provider
            answer.provider = newProvider;
            
            // Emit provider change event
            emit AnswerProviderChanged(answerIndex, questionId, oldProvider, newProvider, msg.sender);
        }
        
        // Update blob ID if provided
        if (bytes(newBlobId).length > 0) {
            answer.blobId = newBlobId;
        }
        
        // Handle status change
        if (oldStatus != AnswerStatus(newStatus)) {
            // If changing from approved to something else, decrease valid count
            if (oldStatus == AnswerStatus.APPROVED && AnswerStatus(newStatus) != AnswerStatus.APPROVED) {
                questions[questionId].validAnswersCount--;
                totalValidAnswers--;
            }
            // If changing to approved from something else, increase valid count
            else if (oldStatus != AnswerStatus.APPROVED && AnswerStatus(newStatus) == AnswerStatus.APPROVED) {
                questions[questionId].validAnswersCount++;
                totalValidAnswers++;
            }
            
            answer.status = AnswerStatus(newStatus);
            answer.validatedAt = block.timestamp;
        }
        
        emit AnswerValidated(answerIndex, questionId, answer.status, msg.sender);
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
    function owner_addAIValidator(address validator) external onlyOwner {
        aiValidators[validator] = true;
    }

    function owner_removeAIValidator(address validator) external onlyOwner {
        aiValidators[validator] = false;
    }

    function isAIValidator(address validator) public view returns (bool) {
        return aiValidators[validator];
    }

    // Emergency functions
    function owner_emergencyWithdraw() external onlyOwner {
        (bool success, ) = payable(owner()).call{value: address(this).balance}("");
        require(success, "Transfer failed");
    }

    /**
     * @dev Overwrite question details (only owner)
     * HACKATHON DEMO: This function allows easy question modification for demo purposes
     * @param questionId ID of the question to overwrite
     * @param newPrompt New question prompt
     * @param newAnswersNeeded New number of answers needed
     * @param newBounty New bounty amount (if 0, keeps existing bounty)
     */
    function owner_overwriteQuestion(
        uint256 questionId,
        string memory newPrompt,
        uint256 newAnswersNeeded,
        uint256 newBounty
    ) external onlyOwner questionExists(questionId) {
        Question storage question = questions[questionId];
        
        // Only allow overwriting if question is still open
        require(question.status == QuestionStatus.OPEN, "Can only overwrite open questions");
        
        // Update question details
        if (bytes(newPrompt).length > 0) {
            question.prompt = newPrompt;
        }
        
        if (newAnswersNeeded > 0) {
            question.answersNeeded = newAnswersNeeded;
        }
        
        // Handle bounty update
        if (newBounty > 0) {
            // If new bounty is provided, update it
            question.bounty = newBounty;
        }
        
        emit QuestionAsked(
            questionId,
            question.asker,
            question.prompt,
            question.answersNeeded,
            question.bounty
        );
    }

    /**
     * @dev Force close a question and refund bounty (only owner)
     * HACKATHON DEMO: This function allows easy question closure for demo purposes
     * @param questionId ID of the question to force close
     */
    function owner_forceCloseQuestion(uint256 questionId) external onlyOwner questionExists(questionId) {
        Question storage question = questions[questionId];
        
        require(question.status == QuestionStatus.OPEN, "Question is not open");
        
        // Refund the bounty to the asker
        if (question.bounty > 0) {
            (bool success, ) = payable(question.asker).call{value: question.bounty}("");
            require(success, "Bounty refund failed");
        }
        
        // Close the question
        _closeQuestion(questionId);
    }

    /**
     * @dev Delete the last question and all its answers (only owner)
     * HACKATHON DEMO: This function allows easy cleanup for demo purposes
     * Refunds the bounty to the asker
     */
    function owner_deleteLastQuestion() external onlyOwner {
        require(_questionIds > 0, "No questions exist");
        
        uint256 lastQuestionId = _questionIds;
        Question storage question = questions[lastQuestionId];
        
        require(question.exists, "Last question does not exist");
        
        // Refund the bounty to the asker
        if (question.bounty > 0) {
            (bool success, ) = payable(question.asker).call{value: question.bounty}("");
            require(success, "Bounty refund failed");
        }
        
        // Delete all answers for this question
        delete questionAnswers[lastQuestionId];
        
        // Remove from user questions
        uint256[] storage userQ = userQuestions[question.asker];
        for (uint256 i = 0; i < userQ.length; i++) {
            if (userQ[i] == lastQuestionId) {
                // Remove this question from user's questions
                userQ[i] = userQ[userQ.length - 1];
                userQ.pop();
                break;
            }
        }
        
        // Delete user answers for this question
        for (uint256 i = 0; i < questionAnswers[lastQuestionId].length; i++) {
            address provider = questionAnswers[lastQuestionId][i].provider;
            delete userAnswers[provider][lastQuestionId]; // Clear all answers for this user for this question
        }
        
        // Delete the question
        delete questions[lastQuestionId];
        
        // Update counters
        totalQuestions--;
        totalAnswers -= question.totalAnswersCount;
        totalValidAnswers -= question.validAnswersCount;
        
        // Decrement question ID counter
        _questionIds--;
    }

    /**
     * @dev Wipe all questions and answers, reset contract to initial state (only owner)
     * HACKATHON DEMO: This function allows complete reset for demo purposes
     * Refunds all bounties to their respective askers
     */
    function owner_wipeAllData() external onlyOwner {
        // Refund all bounties first
        for (uint256 i = 1; i <= _questionIds; i++) {
            if (questions[i].exists && questions[i].bounty > 0) {
                (bool success, ) = payable(questions[i].asker).call{value: questions[i].bounty}("");
                require(success, "Bounty refund failed");
            }
        }
        
        // Clear all questions
        for (uint256 i = 1; i <= _questionIds; i++) {
            delete questions[i];
            delete questionAnswers[i];
        }
        
        // Clear all user mappings
        // Note: This is a simplified approach. In production, you might want to track all users
        // and clear their data more systematically
        
        // Reset counters
        _questionIds = 0;
        totalQuestions = 0;
        totalAnswers = 0;
        totalValidAnswers = 0;
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

    function getAnswer(uint256 questionId, uint256 answerIndex) 
        external 
        view 
        questionExists(questionId)
        returns (Answer memory) 
    {
        require(answerIndex < questionAnswers[questionId].length, "Answer does not exist");
        return questionAnswers[questionId][answerIndex];
    }

    function getQuestionAnswers(uint256 questionId) 
        external 
        view 
        questionExists(questionId) 
        returns (Answer[] memory) 
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

    function getUserAnswers(address user, uint256 questionId) 
        external 
        view 
        questionExists(questionId)
        returns (uint256[] memory) 
    {
        return userAnswers[user][questionId];
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
    
    function getContractStats() 
        external 
        view 
        returns (
            uint256 totalQuestionsCount,
            uint256 totalAnswersCount,
            uint256 totalValidAnswersCount,
            uint256 openQuestionsCount,
            uint256 closedQuestionsCount
        ) 
    {
        uint256 openCount = 0;
        uint256 closedCount = 0;
        
        for (uint256 i = 1; i <= _questionIds; i++) {
            if (questions[i].exists) {
                if (questions[i].status == QuestionStatus.OPEN) {
                    openCount++;
                } else if (questions[i].status == QuestionStatus.CLOSED) {
                    closedCount++;
                }
            }
        }
        
        return (totalQuestions, totalAnswers, totalValidAnswers, openCount, closedCount);
    }
    
    function getNextUnvalidatedAnswer() 
        external 
        view 
        returns (
            uint256 questionId,
            uint256 answerIndex,
            address provider,
            string memory blobId,
            uint256 submittedAt
        ) 
    {
        // Search through all questions to find the first unvalidated answer
        for (uint256 q = 1; q <= _questionIds; q++) {
            if (questions[q].exists && questions[q].status == QuestionStatus.OPEN) {
                for (uint256 a = 0; a < questionAnswers[q].length; a++) {
                    if (questionAnswers[q][a].status == AnswerStatus.PENDING) {
                        Answer memory answer = questionAnswers[q][a];
                        return (q, a, answer.provider, answer.blobId, answer.submittedAt);
                    }
                }
            }
        }
        
        // No unvalidated answers found
        revert("No unvalidated answers found");
    }

    /**
     * @dev Get all questions and the user's answer status for each
     * @param user Address to check for answers
     * @return questionIds Array of all question IDs
     * @return answerStatus Array indicating the user's answer status for each question (0=UNANSWERED, 1=PENDING, 2=APPROVED, 3=REJECTED)
     */
    function getQuestionsWithAnswerStatus(address user) 
        external 
        view 
        returns (
            uint256[] memory questionIds,
            uint8[] memory answerStatus
        ) 
    {
        uint256[] memory tempQuestionIds = new uint256[](_questionIds);
        uint8[] memory tempAnswerStatus = new uint8[](_questionIds);
        uint256 count = 0;
        
        for (uint256 i = 1; i <= _questionIds; i++) {
            if (questions[i].exists) {
                tempQuestionIds[count] = i;
                
                // Default: UNANSWERED
                uint8 status = uint8(AnswerStatus.UNANSWERED);
                // Find the last answer from this user (most recent)
                for (uint256 j = questionAnswers[i].length; j > 0; j--) {
                    if (questionAnswers[i][j - 1].provider == user) {
                        status = uint8(questionAnswers[i][j - 1].status);
                        break;
                    }
                }
                tempAnswerStatus[count] = status;
                count++;
            }
        }
        
        // Create properly sized arrays
        questionIds = new uint256[](count);
        answerStatus = new uint8[](count);
        
        for (uint256 i = 0; i < count; i++) {
            questionIds[i] = tempQuestionIds[i];
            answerStatus[i] = tempAnswerStatus[i];
        }
    }

    /**
     * @dev Get all open questions and whether a user has answered them
     * @param user Address to check for answers
     * @return questionIds Array of open question IDs
     * @return hasAnswered Array indicating if user has answered each question (true/false)
     */
    function getOpenQuestionsWithAnswerStatus(address user) 
        external 
        view 
        returns (
            uint256[] memory questionIds,
            bool[] memory hasAnswered
        ) 
    {
        uint256[] memory tempQuestionIds = new uint256[](_questionIds);
        bool[] memory tempHasAnswered = new bool[](_questionIds);
        uint256 count = 0;
        
        for (uint256 i = 1; i <= _questionIds; i++) {
            if (questions[i].exists && 
                questions[i].status == QuestionStatus.OPEN &&
                questions[i].validAnswersCount < questions[i].answersNeeded) {
                
                tempQuestionIds[count] = i;
                
                // Check if user has answered this question
                bool answered = false;
                for (uint256 j = 0; j < questionAnswers[i].length; j++) {
                    if (questionAnswers[i][j].provider == user) {
                        answered = true;
                        break;
                    }
                }
                tempHasAnswered[count] = answered;
                count++;
            }
        }
        
        // Create properly sized arrays
        questionIds = new uint256[](count);
        hasAnswered = new bool[](count);
        
        for (uint256 i = 0; i < count; i++) {
            questionIds[i] = tempQuestionIds[i];
            hasAnswered[i] = tempHasAnswered[i];
        }
    }

    /**
     * @dev Get detailed answer status for all questions
     * @param user Address to check for answers
     * @return questionIds Array of question IDs
     * @return answerStatus Array with detailed status:
     *         0 = Not answered
     *         1 = Answered and pending validation
     *         2 = Answered and approved
     *         3 = Answered and rejected
     */
    function getQuestionsWithDetailedAnswerStatus(address user) 
        external 
        view 
        returns (
            uint256[] memory questionIds,
            uint8[] memory answerStatus
        ) 
    {
        uint256[] memory tempQuestionIds = new uint256[](_questionIds);
        uint8[] memory tempAnswerStatus = new uint8[](_questionIds);
        uint256 count = 0;
        
        for (uint256 i = 1; i <= _questionIds; i++) {
            if (questions[i].exists) {
                tempQuestionIds[count] = i;
                
                // Check user's answer status for this question
                uint8 status = 0; // Default: Not answered
                for (uint256 j = 0; j < questionAnswers[i].length; j++) {
                    if (questionAnswers[i][j].provider == user) {
                        // User has answered, check the status
                        if (questionAnswers[i][j].status == AnswerStatus.PENDING) {
                            status = 1; // Pending validation
                        } else if (questionAnswers[i][j].status == AnswerStatus.APPROVED) {
                            status = 2; // Approved
                        } else if (questionAnswers[i][j].status == AnswerStatus.REJECTED) {
                            status = 3; // Rejected
                        }
                        break; // User can only have one answer per question
                    }
                }
                tempAnswerStatus[count] = status;
                count++;
            }
        }
        
        // Create properly sized arrays
        questionIds = new uint256[](count);
        answerStatus = new uint8[](count);
        
        for (uint256 i = 0; i < count; i++) {
            questionIds[i] = tempQuestionIds[i];
            answerStatus[i] = tempAnswerStatus[i];
        }
    }

    /**
     * @dev Get detailed answer status for open questions only
     * @param user Address to check for answers
     * @return questionIds Array of open question IDs
     * @return answerStatus Array with detailed status:
     *         0 = Not answered
     *         1 = Answered and pending validation
     *         2 = Answered and approved
     *         3 = Answered and rejected
     */
    function getOpenQuestionsWithDetailedAnswerStatus(address user) 
        external 
        view 
        returns (
            uint256[] memory questionIds,
            uint8[] memory answerStatus
        ) 
    {
        uint256[] memory tempQuestionIds = new uint256[](_questionIds);
        uint8[] memory tempAnswerStatus = new uint8[](_questionIds);
        uint256 count = 0;
        
        for (uint256 i = 1; i <= _questionIds; i++) {
            if (questions[i].exists && 
                questions[i].status == QuestionStatus.OPEN &&
                questions[i].validAnswersCount < questions[i].answersNeeded) {
                
                tempQuestionIds[count] = i;
                
                // Check user's answer status for this question
                uint8 status = 0; // Default: Not answered
                for (uint256 j = 0; j < questionAnswers[i].length; j++) {
                    if (questionAnswers[i][j].provider == user) {
                        // User has answered, check the status
                        if (questionAnswers[i][j].status == AnswerStatus.PENDING) {
                            status = 1; // Pending validation
                        } else if (questionAnswers[i][j].status == AnswerStatus.APPROVED) {
                            status = 2; // Approved
                        } else if (questionAnswers[i][j].status == AnswerStatus.REJECTED) {
                            status = 3; // Rejected
                        }
                        break; // User can only have one answer per question
                    }
                }
                tempAnswerStatus[count] = status;
                count++;
            }
        }
        
        // Create properly sized arrays
        questionIds = new uint256[](count);
        answerStatus = new uint8[](count);
        
        for (uint256 i = 0; i < count; i++) {
            questionIds[i] = tempQuestionIds[i];
            answerStatus[i] = tempAnswerStatus[i];
        }
    }
} 