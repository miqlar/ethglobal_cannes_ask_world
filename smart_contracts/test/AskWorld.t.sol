// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/AskWorld.sol";

contract AskWorldTest is Test {
    AskWorld public askWorld;
    
    address public owner;
    address public user1;
    address public user2;
    address public aiValidator;
    
    function setUp() public {
        owner = address(this);
        user1 = makeAddr("user1");
        user2 = makeAddr("user2");
        aiValidator = makeAddr("aiValidator");
        
        askWorld = new AskWorld();
        
        // Add AI validator
        askWorld.addAIValidator(aiValidator);
        
        // Fund users
        vm.deal(user1, 10 ether);
        vm.deal(user2, 10 ether);
    }
    
    function testConstructor() public {
        assertTrue(askWorld.owner() == owner);
        assertTrue(askWorld.isAIValidator(owner));
    }
    
    function testAskQuestion() public {
        vm.startPrank(user1);
        
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 2);
        
        AskWorld.Question memory question = askWorld.getQuestion(1);
        assertEq(question.id, 1);
        assertEq(question.asker, user1);
        assertEq(question.prompt, "What is the capital of France?");
        assertEq(question.answersNeeded, 2);
        assertEq(question.bounty, 1 ether);
        assertEq(question.validAnswersCount, 0);
        assertEq(question.totalAnswersCount, 0);
        assertEq(uint256(question.status), uint256(AskWorld.QuestionStatus.OPEN));
        assertTrue(question.exists);
        
        vm.stopPrank();
    }
    
    function testAskQuestionWithZeroBounty() public {
        vm.startPrank(user1);
        
        vm.expectRevert("Bounty must be greater than 0");
        askWorld.askQuestion{value: 0}("What is the capital of France?", 2);
        
        vm.stopPrank();
    }
    
    function testAskQuestionWithZeroAnswers() public {
        vm.startPrank(user1);
        
        vm.expectRevert("Must need at least 1 answer");
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 0);
        
        vm.stopPrank();
    }
    
    function testAskQuestionWithEmptyPrompt() public {
        vm.startPrank(user1);
        
        vm.expectRevert("Prompt cannot be empty");
        askWorld.askQuestion{value: 1 ether}("", 2);
        
        vm.stopPrank();
    }
    
    function testSubmitAnswer() public {
        // First ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 2);
        vm.stopPrank();
        
        // Submit an answer
        vm.startPrank(user2);
        askWorld.submitAnswer(1, "QmHash123");
        
        AskWorld.Answer memory answer = askWorld.getAnswer(1);
        assertEq(answer.id, 1);
        assertEq(answer.questionId, 1);
        assertEq(answer.provider, user2);
        assertEq(answer.audioHash, "QmHash123");
        assertEq(uint256(answer.status), uint256(AskWorld.AnswerStatus.PENDING));
        assertTrue(answer.exists);
        
        vm.stopPrank();
    }
    
    function testSubmitAnswerToNonExistentQuestion() public {
        vm.startPrank(user2);
        
        vm.expectRevert("Question does not exist");
        askWorld.submitAnswer(999, "QmHash123");
        
        vm.stopPrank();
    }
    
    function testSubmitAnswerToClosedQuestion() public {
        // First ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 1);
        vm.stopPrank();
        
        // Submit an answer
        vm.startPrank(user2);
        askWorld.submitAnswer(1, "QmHash123");
        vm.stopPrank();
        
        // Validate the answer (this will close the question)
        vm.startPrank(aiValidator);
        askWorld.validateAnswer(1, true);
        vm.stopPrank();
        
        // Try to submit another answer
        vm.startPrank(user1);
        vm.expectRevert("Question not open");
        askWorld.submitAnswer(1, "QmHash456");
        vm.stopPrank();
    }
    
    function testSubmitDuplicateAnswer() public {
        // First ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 2);
        vm.stopPrank();
        
        // Submit an answer
        vm.startPrank(user2);
        askWorld.submitAnswer(1, "QmHash123");
        
        // Try to submit another answer from the same user
        vm.expectRevert("Already submitted answer for this question");
        askWorld.submitAnswer(1, "QmHash456");
        
        vm.stopPrank();
    }
    
    function testSubmitAnswerWithEmptyHash() public {
        // First ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 2);
        vm.stopPrank();
        
        // Submit an answer with empty hash
        vm.startPrank(user2);
        vm.expectRevert("Audio hash cannot be empty");
        askWorld.submitAnswer(1, "");
        
        vm.stopPrank();
    }
    
    function testValidateAnswer() public {
        // First ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 2);
        vm.stopPrank();
        
        // Submit an answer
        vm.startPrank(user2);
        askWorld.submitAnswer(1, "QmHash123");
        vm.stopPrank();
        
        // Validate the answer
        vm.startPrank(aiValidator);
        askWorld.validateAnswer(1, true);
        
        AskWorld.Answer memory answer = askWorld.getAnswer(1);
        assertEq(uint256(answer.status), uint256(AskWorld.AnswerStatus.APPROVED));
        
        AskWorld.Question memory question = askWorld.getQuestion(1);
        assertEq(question.validAnswersCount, 1);
        
        vm.stopPrank();
    }
    
    function testValidateAnswerByNonValidator() public {
        // First ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 2);
        vm.stopPrank();
        
        // Submit an answer
        vm.startPrank(user2);
        askWorld.submitAnswer(1, "QmHash123");
        vm.stopPrank();
        
        // Try to validate with non-validator
        vm.startPrank(user1);
        vm.expectRevert("Not authorized");
        askWorld.validateAnswer(1, true);
        
        vm.stopPrank();
    }
    
    function testValidateNonExistentAnswer() public {
        vm.startPrank(aiValidator);
        
        vm.expectRevert("Answer does not exist");
        askWorld.validateAnswer(999, true);
        
        vm.stopPrank();
    }
    
    function testValidateAlreadyProcessedAnswer() public {
        // First ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 2);
        vm.stopPrank();
        
        // Submit an answer
        vm.startPrank(user2);
        askWorld.submitAnswer(1, "QmHash123");
        vm.stopPrank();
        
        // Validate the answer
        vm.startPrank(aiValidator);
        askWorld.validateAnswer(1, true);
        
        // Try to validate again
        vm.expectRevert("Answer already processed");
        askWorld.validateAnswer(1, false);
        
        vm.stopPrank();
    }
    
    function testRejectAnswer() public {
        // First ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 2);
        vm.stopPrank();
        
        // Submit an answer
        vm.startPrank(user2);
        askWorld.submitAnswer(1, "QmHash123");
        vm.stopPrank();
        
        // Reject the answer
        vm.startPrank(aiValidator);
        askWorld.validateAnswer(1, false);
        
        AskWorld.Answer memory answer = askWorld.getAnswer(1);
        assertEq(uint256(answer.status), uint256(AskWorld.AnswerStatus.REJECTED));
        
        AskWorld.Question memory question = askWorld.getQuestion(1);
        assertEq(question.validAnswersCount, 0);
        
        vm.stopPrank();
    }
    
    function testCloseQuestion() public {
        // First ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 2);
        vm.stopPrank();
        
        // Close the question
        vm.startPrank(user1);
        askWorld.closeQuestion(1);
        
        AskWorld.Question memory question = askWorld.getQuestion(1);
        assertEq(uint256(question.status), uint256(AskWorld.QuestionStatus.CLOSED));
        
        vm.stopPrank();
    }
    
    function testCloseQuestionByNonAsker() public {
        // First ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 2);
        vm.stopPrank();
        
        // Try to close by non-asker
        vm.startPrank(user2);
        vm.expectRevert("Only asker or owner can close");
        askWorld.closeQuestion(1);
        
        vm.stopPrank();
    }
    
    function testCloseNonExistentQuestion() public {
        vm.startPrank(user1);
        
        vm.expectRevert("Question does not exist");
        askWorld.closeQuestion(999);
        
        vm.stopPrank();
    }
    
    function testCloseAlreadyClosedQuestion() public {
        // First ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 2);
        askWorld.closeQuestion(1);
        vm.stopPrank();
        
        // Try to close again
        vm.startPrank(user1);
        vm.expectRevert("Question not open");
        askWorld.closeQuestion(1);
        
        vm.stopPrank();
    }
    
    function testAutoCloseQuestion() public {
        // First ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 1);
        vm.stopPrank();
        
        // Submit an answer
        vm.startPrank(user2);
        askWorld.submitAnswer(1, "QmHash123");
        vm.stopPrank();
        
        // Validate the answer (this should auto-close the question)
        vm.startPrank(aiValidator);
        askWorld.validateAnswer(1, true);
        
        AskWorld.Question memory question = askWorld.getQuestion(1);
        assertEq(uint256(question.status), uint256(AskWorld.QuestionStatus.CLOSED));
        
        vm.stopPrank();
    }
    
    function testBountyPayment() public {
        uint256 initialBalance = user2.balance;
        
        // First ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 1);
        vm.stopPrank();
        
        // Submit an answer
        vm.startPrank(user2);
        askWorld.submitAnswer(1, "QmHash123");
        vm.stopPrank();
        
        // Validate the answer
        vm.startPrank(aiValidator);
        askWorld.validateAnswer(1, true);
        vm.stopPrank();
        
        // Check that bounty was paid
        assertEq(user2.balance, initialBalance + 1 ether);
    }
    
    function testMultipleAnswers() public {
        // First ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 2);
        vm.stopPrank();
        
        // Submit first answer
        vm.startPrank(user2);
        askWorld.submitAnswer(1, "QmHash123");
        vm.stopPrank();
        
        // Submit second answer
        address user3 = makeAddr("user3");
        vm.deal(user3, 10 ether);
        vm.startPrank(user3);
        askWorld.submitAnswer(1, "QmHash456");
        vm.stopPrank();
        
        // Validate both answers
        vm.startPrank(aiValidator);
        askWorld.validateAnswer(1, true);
        askWorld.validateAnswer(2, true);
        vm.stopPrank();
        
        // Check that question is closed
        AskWorld.Question memory question = askWorld.getQuestion(1);
        assertEq(uint256(question.status), uint256(AskWorld.QuestionStatus.CLOSED));
        assertEq(question.validAnswersCount, 2);
    }
    
    function testGetQuestionStats() public {
        // First ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 2);
        vm.stopPrank();
        
        // Submit an answer
        vm.startPrank(user2);
        askWorld.submitAnswer(1, "QmHash123");
        vm.stopPrank();
        
        // Get stats
        (uint256 validCount, uint256 totalCount, uint256 neededCount, bool isComplete) = askWorld.getQuestionStats(1);
        assertEq(validCount, 0);
        assertEq(totalCount, 1);
        assertEq(neededCount, 2);
        assertEq(isComplete, false);
        
        // Validate the answer
        vm.startPrank(aiValidator);
        askWorld.validateAnswer(1, true);
        vm.stopPrank();
        
        // Get stats again
        (validCount, totalCount, neededCount, isComplete) = askWorld.getQuestionStats(1);
        assertEq(validCount, 1);
        assertEq(totalCount, 1);
        assertEq(neededCount, 2);
        assertEq(isComplete, false);
    }
    
    function testGetOpenQuestions() public {
        // Ask multiple questions
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("Question 1", 1);
        askWorld.askQuestion{value: 1 ether}("Question 2", 1);
        askWorld.askQuestion{value: 1 ether}("Question 3", 1);
        vm.stopPrank();
        
        // Get open questions
        uint256[] memory openQuestions = askWorld.getOpenQuestions();
        assertEq(openQuestions.length, 3);
        assertEq(openQuestions[0], 1);
        assertEq(openQuestions[1], 2);
        assertEq(openQuestions[2], 3);
        
        // Close one question
        vm.startPrank(user1);
        askWorld.closeQuestion(1);
        vm.stopPrank();
        
        // Get open questions again
        openQuestions = askWorld.getOpenQuestions();
        assertEq(openQuestions.length, 2);
        assertEq(openQuestions[0], 2);
        assertEq(openQuestions[1], 3);
    }
    
    function testAIValidatorManagement() public {
        address newValidator = makeAddr("newValidator");
        
        // Add validator
        askWorld.addAIValidator(newValidator);
        assertTrue(askWorld.isAIValidator(newValidator));
        
        // Remove validator
        askWorld.removeAIValidator(newValidator);
        assertFalse(askWorld.isAIValidator(newValidator));
    }
    
    
    function testGetUserQuestions() public {
        // Ask questions from different users
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("Question 1", 1);
        askWorld.askQuestion{value: 1 ether}("Question 2", 1);
        vm.stopPrank();
        
        vm.startPrank(user2);
        askWorld.askQuestion{value: 1 ether}("Question 3", 1);
        vm.stopPrank();
        
        // Get user questions
        uint256[] memory user1Questions = askWorld.getUserQuestions(user1);
        assertEq(user1Questions.length, 2);
        assertEq(user1Questions[0], 1);
        assertEq(user1Questions[1], 2);
        
        uint256[] memory user2Questions = askWorld.getUserQuestions(user2);
        assertEq(user2Questions.length, 1);
        assertEq(user2Questions[0], 3);
    }
    
    function testGetUserAnswers() public {
        // Ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 2);
        vm.stopPrank();
        
        // Submit answers from different users
        vm.startPrank(user2);
        askWorld.submitAnswer(1, "QmHash123");
        vm.stopPrank();
        
        address user3 = makeAddr("user3");
        vm.deal(user3, 10 ether);
        vm.startPrank(user3);
        askWorld.submitAnswer(1, "QmHash456");
        vm.stopPrank();
        
        // Get user answers
        uint256[] memory user2Answers = askWorld.getUserAnswers(user2);
        assertEq(user2Answers.length, 1);
        assertEq(user2Answers[0], 1);
        
        uint256[] memory user3Answers = askWorld.getUserAnswers(user3);
        assertEq(user3Answers.length, 1);
        assertEq(user3Answers[0], 2);
    }
    
    function testGetQuestionAnswers() public {
        // Ask a question
        vm.startPrank(user1);
        askWorld.askQuestion{value: 1 ether}("What is the capital of France?", 2);
        vm.stopPrank();
        
        // Submit answers
        vm.startPrank(user2);
        askWorld.submitAnswer(1, "QmHash123");
        vm.stopPrank();
        
        address user3 = makeAddr("user3");
        vm.deal(user3, 10 ether);
        vm.startPrank(user3);
        askWorld.submitAnswer(1, "QmHash456");
        vm.stopPrank();
        
        // Get question answers
        uint256[] memory answers = askWorld.getQuestionAnswers(1);
        assertEq(answers.length, 2);
        assertEq(answers[0], 1);
        assertEq(answers[1], 2);
    }
} 