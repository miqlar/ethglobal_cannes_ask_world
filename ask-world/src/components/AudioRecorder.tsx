// src/components/AudioRecorder.tsx
'use client';

import { MiniKit, Permission, ResponseEvent } from '@worldcoin/minikit-js';
import { RequestPermissionPayload } from '@worldcoin/minikit-js';
import { useState, useRef, useEffect } from 'react';
import Image from 'next/image';
import CONTRACT_ABI from "../../abi/askworld.json";
import Confetti from './Confetti';
import SkullRain from './SkullRain';

function isSafari() {
    return /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
}

const CONTRACT_ADDRESS = "0xbDBcB9d5f5cF6c6040A7b6151c2ABE25C68f83af";

export default function AudioRecorder() {
    const [isRecording, setIsRecording] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState<string>('');
    const [showToast, setShowToast] = useState(false);
    const [toastType, setToastType] = useState<'success' | 'error'>('success');
    const [blobId, setBlobId] = useState<string | null>(null);
    const [showRecorder, setShowRecorder] = useState(false);
    const [showAskPage, setShowAskPage] = useState(false);
    const [question, setQuestion] = useState('');
    const [submittingQuestion, setSubmittingQuestion] = useState(false);
    const [questionStatus, setQuestionStatus] = useState<string>('');
    const [bountyPrice, setBountyPrice] = useState<string>('');
    const [maxSubmissions, setMaxSubmissions] = useState<string>('');
    const [currentCardIndex, setCurrentCardIndex] = useState(0);
    const [startX, setStartX] = useState(0);
    const [currentX, setCurrentX] = useState(0);
    const [isDragging, setIsDragging] = useState(false);
    const [recordingDuration, setRecordingDuration] = useState(0);
    const [recordingStartTime, setRecordingStartTime] = useState<number | null>(null);
    const [transactionId, setTransactionId] = useState<string | null>(null);
    const [transactionPending, setTransactionPending] = useState(false);
    const [questionRecordings, setQuestionRecordings] = useState<Record<number, Blob>>({});
    const [showConfetti, setShowConfetti] = useState(false);
    const [showSkullRain, setShowSkullRain] = useState(false);
    const [animatedQuestions, setAnimatedQuestions] = useState<Set<number>>(new Set());
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);

    // Function to fetch questions from contract
    const fetchQuestionsFromContract = async () => {
        try {
            setLoadingQuestions(true);

            // Use web3 to read from contract
            const Web3 = (await import('web3')).default;
            const QUICKNODE_RPC_URL = process.env.NEXT_PUBLIC_WORLDCHAIN_RPC || '';
            const web3 = new Web3(new Web3.providers.HttpProvider(QUICKNODE_RPC_URL));

            const userAddress = "0xb9eed315541d3dea07cee2f5ab0909009ccca54f";

            // First, get the question IDs and answer status
            const contract = new web3.eth.Contract(CONTRACT_ABI, CONTRACT_ADDRESS);

            const result = await contract.methods.getQuestionsWithAnswerStatus(userAddress).call();

            console.log('getQuestionsWithAnswerStatus result:', result);
            console.log('Result type:', typeof result);
            console.log('Is array:', Array.isArray(result));
            console.log('Result length:', result ? result.length : 'null/undefined');

            if (result && typeof result === 'object' && 'questionIds' in result && 'answerStatus' in result) {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const questionIds = (result as any).questionIds as string[];
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const answerStatus = (result as any).answerStatus as string[];

                // Fetch details for each question
                const questionsData = [];
                for (let i = 0; i < questionIds.length; i++) {
                    const questionId = questionIds[i];
                    const status = parseInt(answerStatus[i]);

                    try {
                        const questionResult = await contract.methods.getQuestion(questionId).call();

                        if (questionResult) {
                            questionsData.push({
                                id: parseInt(questionId),
                                text: questionResult[2] as string, // prompt
                                reward: parseFloat(questionResult[4] as string) / 1e6, // bounty
                                answerStatus: status // 0=unanswered, 1=pending, 2=approved, 3=rejected
                            });
                        }
                    } catch (error) {
                        console.error(`Error fetching question ${questionId}:`, error);
                    }
                }

                setQuestions(questionsData);
            } else {
                // Fallback to hardcoded questions if no questions found
                const fallbackQuestions = [
                    { id: 1, text: "What's your favorite way to spend a weekend?", reward: 50, answerStatus: 0 },
                    { id: 2, text: "If you could have dinner with anyone, who would it be?", reward: 75, answerStatus: 0 },
                    { id: 3, text: "What's the most valuable lesson you've learned?", reward: 100, answerStatus: 0 },
                    { id: 4, text: "What's your biggest dream for the future?", reward: 150, answerStatus: 0 },
                    { id: 5, text: "What makes you feel most alive?", reward: 200, answerStatus: 0 },
                ];
                setQuestions(fallbackQuestions);
            }

        } catch (error) {
            console.error('Error fetching questions from contract:', error);
            // Fallback to hardcoded questions on error
            const fallbackQuestions = [
                { id: 1, text: "What's your favorite way to spend a weekend?", reward: 50, answerStatus: 0 },
                { id: 2, text: "If you could have dinner with anyone, who would it be?", reward: 75, answerStatus: 0 },
                { id: 3, text: "What's the most valuable lesson you've learned?", reward: 100, answerStatus: 0 },
                { id: 4, text: "What's your biggest dream for the future?", reward: 150, answerStatus: 0 },
                { id: 5, text: "What makes you feel most alive?", reward: 200, answerStatus: 0 },
            ];
            setQuestions(fallbackQuestions);
        } finally {
            setLoadingQuestions(false);
        }
    };

    // Use state for questions so we can update the list
    const [questions, setQuestions] = useState<Array<{ id: number, text: string, reward: number, answerStatus: number }>>([]);
    const [loadingQuestions, setLoadingQuestions] = useState(true);

    // Load questions from contract on component mount
    useEffect(() => {
        fetchQuestionsFromContract();
    }, []);

    // Show confetti when an approved answer is displayed (only first time)
    useEffect(() => {
        if (questions.length > 0 && questions[currentCardIndex]?.answerStatus === 2) {
            const questionId = questions[currentCardIndex].id;
            if (!animatedQuestions.has(questionId)) {
                setShowConfetti(true);
                setAnimatedQuestions(prev => new Set([...prev, questionId]));
                const timer = setTimeout(() => setShowConfetti(false), 6000);
                return () => clearTimeout(timer);
            }
        }
    }, [currentCardIndex, questions, animatedQuestions]);

    // Show skull rain when a rejected answer is displayed
    useEffect(() => {
        if (questions.length > 0 && questions[currentCardIndex]?.answerStatus === 3) {
            setShowSkullRain(true);
            const timer = setTimeout(() => setShowSkullRain(false), 8000);
            return () => clearTimeout(timer);
        }
    }, [currentCardIndex, questions]);

    // Track recording duration
    useEffect(() => {
        let interval: NodeJS.Timeout;

        if (isRecording && recordingStartTime) {
            interval = setInterval(() => {
                const duration = Math.floor((Date.now() - recordingStartTime) / 1000);
                setRecordingDuration(duration);
            }, 100);
        } else {
            setRecordingDuration(0);
        }

        return () => {
            if (interval) {
                clearInterval(interval);
            }
        };
    }, [isRecording, recordingStartTime]);

    useEffect(() => {
        if (!MiniKit.isInstalled()) return;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const handler = (payload: any) => {
            if (payload.status === "error") {
                console.error("Error sending transaction", payload);
                setTransactionPending(false);
                setQuestionStatus('Transaction failed: ' + payload.error);
                setToastType('error');
                setShowToast(true);
            } else {
                setTransactionId(payload.transaction_id);
                setTransactionPending(false);
                console.log("transaction_id:", payload.transaction_id);
                console.log("transaction id:", transactionId);

                // Handle success case - refresh questions from contract
                fetchQuestionsFromContract();

                setQuestionStatus('Question submitted successfully to contract!');
                setToastType('success');
                setShowToast(true);
                setQuestion('');
                setBountyPrice('');
                setMaxSubmissions('');

                // Return to main page after a delay
                setTimeout(() => {
                    setShowAskPage(false);
                    setQuestionStatus('');
                }, 2000);
            }
        };
        MiniKit.subscribe(ResponseEvent.MiniAppSendTransaction, handler);
        return () => {
            MiniKit.unsubscribe(ResponseEvent.MiniAppSendTransaction);
        };
    }, []);

    // Detect supported MIME type
    function getSupportedMimeType() {
        const possibleTypes = isSafari()
            ? ['audio/mp4', 'audio/aac']
            : ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg'];
        for (const type of possibleTypes) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            if ((window as any).MediaRecorder && MediaRecorder.isTypeSupported(type)) return type;
        }
        // fallback
        return '';
    }

    // Request microphone permission
    const requestMicrophonePermission = async () => {
        const requestPermissionPayload: RequestPermissionPayload = {
            permission: Permission.Microphone,
        };

        const payload = await MiniKit.commandsAsync.requestPermission(requestPermissionPayload);
        if (payload.finalPayload.status === 'success') {
            console.log('Microphone permission granted');
        } else {
            console.error('Failed to request microphone permission:', payload);
        }
    };

    // Check existing permissions
    const checkRequestMicrophonePermission = async () => {
        const payload = await MiniKit.commandsAsync.getPermissions();
        if (payload.finalPayload.status === 'success') {
            const hasPermission = payload.finalPayload.permissions.microphone;
            console.log('Microphone permission:', hasPermission ? 'Granted' : 'Not granted');
            if (!hasPermission) {
                requestMicrophonePermission();
            }
        } else {
            console.error('Failed to check permissions:', payload);
        }
    };

    const startRecording = async () => {
        try {
            checkRequestMicrophonePermission();
            const mimeType = getSupportedMimeType();
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorderRef.current = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
            audioChunksRef.current = [];

            mediaRecorderRef.current.ondataavailable = (event) => {
                audioChunksRef.current.push(event.data);
            };

            mediaRecorderRef.current.onstop = () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: mimeType || 'audio/webm' });

                // Save the recording for the current question
                setQuestionRecordings(prev => ({
                    ...prev,
                    [currentCardIndex]: audioBlob
                }));

                stream.getTracks().forEach((track) => track.stop());
            };

            mediaRecorderRef.current.start();
            setIsRecording(true);
            setUploadStatus('');
            setRecordingStartTime(Date.now());
        } catch (error) {
            setUploadStatus('Failed to access microphone: ' + (error as Error).message);
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
            setRecordingStartTime(null);
            setRecordingDuration(0);
        }
    };

    const handleQuestionSubmit = async () => {
        if (!question.trim()) {
            setQuestionStatus('Please enter a question.');
            return;
        }

        // Validate bounty price if provided
        if (bountyPrice.trim()) {
            const bountyValue = parseFloat(bountyPrice);
            if (isNaN(bountyValue) || bountyValue <= 0) {
                setQuestionStatus('Please enter a valid bounty price (positive number).');
                return;
            }
        }

        // Validate max submissions if provided
        if (maxSubmissions.trim()) {
            const maxSubmissionsValue = parseInt(maxSubmissions);
            if (isNaN(maxSubmissionsValue) || maxSubmissionsValue <= 0) {
                setQuestionStatus('Please enter a valid number of submissions (positive integer).');
                return;
            }
        }

        setSubmittingQuestion(true);
        setTransactionPending(true);
        setQuestionStatus('Submitting question to contract...');
        setShowToast(false);

        try {
            // Prepare parameters for askQuestion function
            const prompt = question.trim();
            const answersNeeded = maxSubmissions.trim() ? parseInt(maxSubmissions) : 1;
            const value = "0x0000000000000000000000000000000000000000000000000000000000000001"; // Send 1 wei as requested

            // Send transaction to contract
            const result = await MiniKit.commands.sendTransaction({
                transaction: [
                    {
                        address: CONTRACT_ADDRESS,
                        abi: CONTRACT_ABI,
                        functionName: "askQuestion",
                        args: [prompt, answersNeeded],
                        value: value,
                    },
                ],
            });

            console.log('Transaction sent:', result);
            // Note: We don't set transactionPending to false here
            // It will be set to false in the transaction handler when the transaction is confirmed
            // The success actions will be handled in the transaction handler

        } catch (error) {
            console.error('Error submitting question to contract:', error);
            setQuestionStatus('Error submitting question to contract: ' + (error as Error).message);
            setToastType('error');
            setShowToast(true);
            setTransactionPending(false);
        } finally {
            setSubmittingQuestion(false);
        }
    };

    // Swipe functionality
    const handleTouchStart = (e: React.TouchEvent) => {
        e.preventDefault();
        setStartX(e.touches[0].clientX);
        setCurrentX(e.touches[0].clientX);
        setIsDragging(true);
    };

    const handleTouchMove = (e: React.TouchEvent) => {
        if (isDragging) {
            setCurrentX(e.touches[0].clientX);
        }
    };

    const handleTouchEnd = () => {
        if (isDragging) {
            const diff = startX - currentX;
            const threshold = 50;
            console.log('TouchEnd diff:', diff, 'startX:', startX, 'currentX:', currentX);
            if (Math.abs(diff) > threshold) {
                if (diff > 0 && currentCardIndex < questions.length - 1) {
                    setCurrentCardIndex(currentCardIndex + 1);
                } else if (diff < 0 && currentCardIndex > 0) {
                    setCurrentCardIndex(currentCardIndex - 1);
                }
            }
            setIsDragging(false);
            setCurrentX(startX);
        }
    };

    const handleAfterUpload = async (walrusId: string) => {
        try {
            const questionId = questions[currentCardIndex].id;
            MiniKit.commands.sendTransaction({
                transaction: [
                    {
                        address: CONTRACT_ADDRESS,
                        abi: CONTRACT_ABI,
                        functionName: "submitAnswer",
                        args: [questionId, walrusId],
                    },
                ],
            });
            setUploadStatus('Transaction sent to World Chain!');
            setToastType('success');
            setShowToast(true);

            // Clear the recording for the current question after successful upload
            setQuestionRecordings(prev => {
                const newRecordings = { ...prev };
                delete newRecordings[currentCardIndex];
                return newRecordings;
            });
        } catch (err) {
            setUploadStatus('Failed to send transaction: ' + (err as Error).message);
        }
    };

    const handleUpload = async () => {
        const currentRecording = questionRecordings[currentCardIndex];
        if (!currentRecording) {
            setUploadStatus('No recording to upload.');
            return;
        }

        setUploading(true);
        setUploadStatus('Uploading to Walrus...');
        setShowToast(false);
        setBlobId(null);

        try {
            const formData = new FormData();
            formData.append('audio', currentRecording, `recording-${Date.now()}.webm`);

            const response = await fetch('/api/upload-walrus', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok && result.success) {
                setUploadStatus(`Upload successful! Blob ID: ${result.blobId}`);
                setBlobId(result.blobId);
                setToastType('success');
                setShowToast(true);
                // Call the transaction function
                handleAfterUpload(result.blobId);
            } else {
                setUploadStatus('Upload failed: ' + (result.error || 'Unknown error'));
                setToastType('error');
                setShowToast(true);
            }
        } catch (error) {
            console.error('Error uploading to Walrus:', error);
            setUploadStatus('Error uploading to Walrus: ' + (error as Error).message);
            setToastType('error');
            setShowToast(true);
        } finally {
            setUploading(false);
        }
    };

    // Toast auto-hide
    if (showToast) {
        setTimeout(() => setShowToast(false), 4000);
    }

    // Copy blobId to clipboard
    const copyBlobId = () => {
        if (blobId) {
            navigator.clipboard.writeText(blobId);
        }
    };

    // Ask page
    if (showAskPage) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-500 py-8 px-2">
                <div className="w-full max-w-md bg-white/90 rounded-3xl shadow-2xl p-8 flex flex-col items-center animate-fade-in">
                    <div className="flex flex-col items-center mb-6">
                        <Image src="/askworld-logo.png" alt="Ask World Logo" width={180} height={180} className="mb-2 animate-pop" />
                    </div>

                    <div className="w-full mb-6">
                        <textarea
                            value={question}
                            onChange={(e) => setQuestion(e.target.value)}
                            placeholder="Type your question here..."
                            className="w-full h-32 p-4 border border-gray-300 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-700 placeholder-gray-400 bg-gray-50 shadow-sm"
                            disabled={submittingQuestion}
                        />
                    </div>

                    <div className="w-full mb-4">
                        <div className="flex gap-4 mb-4">
                            <div className="flex-1">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Total Reward (USDC)
                                </label>
                                <input
                                    type="number"
                                    step="0.01"
                                    min="0.01"
                                    value={bountyPrice}
                                    onChange={(e) => setBountyPrice(e.target.value)}
                                    placeholder="100"
                                    className="w-full p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-700 placeholder-gray-400"
                                    disabled={submittingQuestion}
                                />
                            </div>
                            <div className="flex-1">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Max Submissions
                                </label>
                                <input
                                    type="number"
                                    min="1"
                                    value={maxSubmissions}
                                    onChange={(e) => setMaxSubmissions(e.target.value)}
                                    placeholder="100"
                                    className="w-full p-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-700 placeholder-gray-400"
                                    disabled={submittingQuestion}
                                />
                            </div>
                        </div>
                        <div className="w-full flex gap-4 items-end justify-center">
                            <button
                                onClick={handleQuestionSubmit}
                                disabled={!question.trim() || submittingQuestion || transactionPending}
                                className="px-24 py-6 rounded-full font-semibold shadow-md bg-gradient-to-r from-green-500 to-blue-500 text-white hover:from-green-600 hover:to-blue-600 focus:outline-none focus:ring-2 focus:ring-green-400 disabled:opacity-50"
                            >
                                {transactionPending ? (
                                    <div className="flex items-center gap-2">
                                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                        <span>Processing...</span>
                                    </div>
                                ) : submittingQuestion ? 'Submitting...' : 'Submit'}
                            </button>
                        </div>
                    </div>

                    {questionStatus && (
                        <p className={`mb-4 text-center text-base font-medium ${questionStatus.startsWith('Question submitted successfully') ? 'text-green-600' : 'text-red-600'}`}>
                            {questionStatus}
                        </p>
                    )}

                    <div className="flex gap-4 w-full">
                        <button
                            onClick={() => setShowAskPage(false)}
                            disabled={submittingQuestion}
                            className="w-[10%] min-w-[2.5rem] aspect-square flex items-center justify-center rounded-full shadow-md bg-white text-purple-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-400"
                            aria-label="Home"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
                                <path d="M3 12l9-9 9 9" />
                                <path d="M4 10v10a1 1 0 001 1h5m4 0h5a1 1 0 001-1V10" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // Top-level: Ask/Answer buttons
    if (!showRecorder) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-500 py-8 px-2">
                <div className="w-full max-w-md bg-white/90 rounded-3xl shadow-2xl p-8 flex flex-col items-center animate-fade-in">
                    <Image src="/askworld-logo.png" alt="Ask World Logo" width={288} height={288} className="mb-6 animate-pop" />
                    <div className="flex flex-col gap-4 w-full justify-center">
                        <div className="flex gap-8 w-full justify-center">
                            <button
                                className="transition-all flex items-center gap-2 px-12 py-4 rounded-full font-bold shadow-lg bg-gradient-to-r from-green-400 to-blue-500 text-white hover:from-green-500 hover:to-blue-600 focus:outline-none focus:ring-2 focus:ring-green-400 text-xl transform hover:scale-105 active:scale-95"
                                onClick={() => setShowAskPage(true)}
                            >
                                Ask
                            </button>
                            <button
                                className="transition-all flex items-center gap-2 px-12 py-4 rounded-full font-bold shadow-lg bg-gradient-to-r from-purple-500 to-indigo-500 text-white hover:from-purple-600 hover:to-indigo-600 focus:outline-none focus:ring-2 focus:ring-purple-400 text-xl transform hover:scale-105 active:scale-95"
                                onClick={() => setShowRecorder(true)}
                            >
                                Answer
                            </button>
                        </div>
                        <div className="flex justify-center">
                            <a
                                href="/feed"
                                className="transition-all flex items-center gap-2 px-8 py-3 rounded-full font-semibold shadow-md bg-gradient-to-r from-orange-500 to-red-500 text-white hover:from-orange-600 hover:to-red-600 focus:outline-none focus:ring-2 focus:ring-orange-400 text-lg transform hover:scale-105 active:scale-95"
                            >
                                AI Summary
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // Loading state
    if (loadingQuestions) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-500 py-8 px-2">
                <div className="w-full max-w-md bg-white/90 rounded-3xl shadow-2xl p-8 flex flex-col items-center animate-fade-in">
                    <div className="flex items-center gap-3">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                        <span className="text-lg font-medium text-gray-700">Loading questions...</span>
                    </div>
                </div>
            </div>
        );
    }

    // No questions available
    if (questions.length === 0) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-500 py-8 px-2">
                <div className="w-full max-w-md bg-white/90 rounded-3xl shadow-2xl p-8 flex flex-col items-center animate-fade-in">
                    <Image src="/askworld-logo.png" alt="Ask World Logo" width={180} height={180} className="mb-6 animate-pop" />
                    <h2 className="text-xl font-bold text-gray-900 mb-4">No Questions Available</h2>
                    <p className="text-gray-600 text-center mb-6">There are currently no questions to answer. Please try again later or create a new question.</p>
                    <button
                        onClick={() => setShowRecorder(false)}
                        className="px-6 py-3 rounded-full font-semibold shadow-md bg-gradient-to-r from-purple-500 to-indigo-500 text-white hover:from-purple-600 hover:to-indigo-600 focus:outline-none focus:ring-2 focus:ring-purple-400"
                    >
                        Back to Home
                    </button>
                </div>
            </div>
        );
    }

    // Swipable cards UI
    return (
        <>
            <Confetti isActive={showConfetti} />
            <SkullRain isActive={showSkullRain} />
            <div
                className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-500 py-8 px-2"
                onTouchStart={handleTouchStart}
                onTouchMove={handleTouchMove}
                onTouchEnd={handleTouchEnd}
            >
                {/* Left Arrow */}
                {!isRecording && (
                    <button
                        onClick={() => {
                            if (currentCardIndex > 0) {
                                setCurrentCardIndex(currentCardIndex - 1);
                            }
                        }}
                        disabled={currentCardIndex === 0}
                        className="absolute left-4 top-1/2 transform -translate-y-1/2 w-12 h-12 bg-white/80 rounded-full flex items-center justify-center shadow-lg hover:bg-white transition-all disabled:opacity-50 disabled:cursor-not-allowed z-10"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-gray-700">
                            <path d="M15 18l-6-6 6-6" />
                        </svg>
                    </button>
                )}

                {/* Right Arrow */}
                {!isRecording && (
                    <button
                        onClick={() => {
                            if (currentCardIndex < questions.length - 1) {
                                setCurrentCardIndex(currentCardIndex + 1);
                            }
                        }}
                        disabled={currentCardIndex === questions.length - 1}
                        className="absolute right-4 top-1/2 transform -translate-y-1/2 w-12 h-12 bg-white/80 rounded-full flex items-center justify-center shadow-lg hover:bg-white transition-all disabled:opacity-50 disabled:cursor-not-allowed z-10"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-gray-700">
                            <path d="M9 18l6-6-6-6" />
                        </svg>
                    </button>
                )}

                <div className={`w-full max-w-md rounded-3xl shadow-2xl p-8 flex flex-col items-center animate-fade-in ${questions[currentCardIndex].answerStatus === 0 ? 'bg-white/90' :
                    questions[currentCardIndex].answerStatus === 1 ? 'bg-yellow-200/95' :
                        questions[currentCardIndex].answerStatus === 2 ? 'bg-green-200/95' :
                            'bg-red-600/95'
                    }`}>
                    {/* Question display */}
                    <div className="flex flex-col items-center mb-6 w-full">
                        <div className="w-full rounded-xl p-6 shadow-sm mb-4 bg-white/80">
                            <h2 className="text-2xl font-bold text-gray-900 text-center leading-tight">
                                {questions[currentCardIndex].text}
                            </h2>
                            {questions[currentCardIndex].answerStatus === 1 && (
                                <div className="flex items-center justify-center mt-2">
                                    <span className="text-yellow-800 font-medium text-lg">⏳ AI Agent Checking Answer</span>
                                </div>
                            )}
                            {questions[currentCardIndex].answerStatus === 2 && (
                                <div className="flex items-center justify-center mt-2">
                                    <span className="text-green-800 font-medium text-xl animate-bounce">🎉 Answer approved!</span>
                                </div>
                            )}
                            {questions[currentCardIndex].answerStatus === 3 && (
                                <div className="flex items-center justify-center mt-2">
                                    <span className="text-red-800 font-medium text-lg">😔 Answer Rejected</span>
                                </div>
                            )}
                        </div>
                        <div className="flex items-center gap-2 mb-4">
                            <span className="text-sm text-gray-600">
                                Question {currentCardIndex + 1} of {questions.length}
                            </span>
                        </div>
                        <div className="flex items-center gap-2 mb-4">
                            {questions[currentCardIndex].answerStatus === 2 ? (
                                <span className="text-lg font-semibold text-green-800 animate-reward-received">
                                    💰 You have received {(questions[currentCardIndex].reward * 100000).toFixed(2)} USDC Reward
                                </span>
                            ) : questions[currentCardIndex].answerStatus === 3 ? null : (
                                <span className="text-lg font-semibold text-green-600">
                                    💰 {(questions[currentCardIndex].reward * 100000).toFixed(2)} USDC Reward
                                </span>
                            )}
                        </div>
                    </div>

                    {/* Big round Start Recording button or Stop button - only for unanswered questions */}
                    {questions[currentCardIndex].answerStatus === 0 && (
                        <div className="flex flex-col items-center w-full mb-6">
                            {!isRecording ? (
                                <button
                                    onClick={startRecording}
                                    disabled={uploading}
                                    className="start-recording-btn mb-2 animate-pop"
                                >
                                </button>
                            ) : (
                                <>
                                    <div className="flex flex-col items-center mb-4">
                                        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                                            <div
                                                className="bg-red-500 h-2 rounded-full transition-all duration-100"
                                                style={{ width: `${Math.min((recordingDuration / 60) * 100, 100)}%` }}
                                            ></div>
                                        </div>
                                        <span className="text-red-500 font-medium text-sm">
                                            Recording: {Math.floor(recordingDuration / 60)}:{(recordingDuration % 60).toString().padStart(2, '0')}
                                        </span>
                                    </div>
                                    <button
                                        onClick={stopRecording}
                                        disabled={uploading}
                                        className="stop-recording-btn mb-2 animate-pop"
                                    >
                                    </button>
                                </>
                            )}
                        </div>
                    )}

                    {questions[currentCardIndex].answerStatus === 0 && questionRecordings[currentCardIndex] && !isRecording && (
                        <div className="mb-6 w-full">
                            <audio controls src={URL.createObjectURL(questionRecordings[currentCardIndex])} className="w-full rounded-lg border border-gray-200 shadow-sm" />
                        </div>
                    )}

                    {uploadStatus && (
                        <p className={`mb-4 text-center text-base font-medium ${uploadStatus.startsWith('Upload successful') || uploadStatus.startsWith('Uploading to Walrus') || uploadStatus.startsWith('Transaction sent to World Chain')
                            ? 'text-green-600'
                            : 'text-red-600'
                            }`}>{uploadStatus}</p>
                    )}

                    {questions[currentCardIndex].answerStatus === 0 && questionRecordings[currentCardIndex] && !isRecording && (
                        <button
                            onClick={handleUpload}
                            disabled={!questionRecordings[currentCardIndex] || uploading}
                            className="transition-all flex items-center gap-2 px-6 py-2.5 rounded-full font-semibold shadow-md bg-gradient-to-r from-green-500 to-blue-500 text-white hover:from-green-600 hover:to-blue-600 focus:outline-none focus:ring-2 focus:ring-green-400 disabled:opacity-50 mb-4"
                        >
                            {uploading ? 'Submitting...' : 'Submit'}
                        </button>
                    )}

                    {/* Navigation buttons */}
                    {!isRecording && (
                        <div className="flex justify-center w-full">
                            <button
                                onClick={() => setShowRecorder(false)}
                                className="w-12 h-12 flex items-center justify-center rounded-full shadow-md bg-white text-purple-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-400"
                                aria-label="Home"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
                                    <path d="M3 12l9-9 9 9" />
                                    <path d="M4 10v10a1 1 0 001 1h5m4 0h5a1 1 0 001-1V10" />
                                </svg>
                            </button>
                        </div>
                    )}

                    {/* Toast for upload result */}
                    {showToast && (
                        <div className={`fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50 px-6 py-4 rounded-xl shadow-lg flex items-center gap-3 ${toastType === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'} animate-fade-in`}>
                            {toastType === 'success' ? (
                                <>
                                    <span role="img" aria-label="success">✅</span>
                                    <span>Upload successful!</span>
                                    {blobId && (
                                        <button onClick={copyBlobId} className="ml-2 px-2 py-1 bg-white/20 rounded text-xs hover:bg-white/30 transition-all">Copy Blob ID</button>
                                    )}
                                </>
                            ) : (
                                <>
                                    <span role="img" aria-label="error">❌</span>
                                    <span>Upload failed</span>
                                </>
                            )}
                        </div>
                    )}
                </div>
                <style jsx global>{`
                @keyframes fade-in {
                    0% { opacity: 0; transform: translateY(20px); }
                    100% { opacity: 1; transform: translateY(0); }
                }
                .animate-fade-in {
                    animation: fade-in 0.7s cubic-bezier(0.4,0,0.2,1);
                }
                @keyframes pop {
                    0% { transform: scale(0.7); }
                    80% { transform: scale(1.1); }
                    100% { transform: scale(1); }
                }
                .animate-pop {
                    animation: pop 0.5s cubic-bezier(0.4,0,0.2,1);
                }
                @keyframes reward-received {
                    0% { 
                        transform: scale(1); 
                        opacity: 1;
                        text-shadow: 0 0 0 rgba(34, 197, 94, 0);
                    }
                    25% { 
                        transform: scale(1.1); 
                        opacity: 1;
                        text-shadow: 0 0 10px rgba(34, 197, 94, 0.5);
                    }
                    50% { 
                        transform: scale(1.05); 
                        opacity: 1;
                        text-shadow: 0 0 15px rgba(34, 197, 94, 0.7);
                    }
                    75% { 
                        transform: scale(1.08); 
                        opacity: 1;
                        text-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
                    }
                    100% { 
                        transform: scale(1); 
                        opacity: 1;
                        text-shadow: 0 0 0 rgba(34, 197, 94, 0);
                    }
                }
                .animate-reward-received {
                    animation: reward-received 2s ease-in-out infinite;
                }
                .start-recording-btn {
                    width: 8rem;
                    height: 8rem;
                    border-radius: 9999px;
                    background: linear-gradient(135deg, #ff0000 0%, #cc0000 50%, #990000 100%);
                    box-shadow: 
                        0 0 0 6px rgba(255, 255, 255, 0.15),
                        0 0 0 12px rgba(255, 0, 0, 0.2),
                        0 12px 48px 0 rgba(255, 0, 0, 0.4), 
                        0 4px 16px 0 rgba(0,0,0,0.2),
                        inset 0 2px 0 rgba(255, 255, 255, 0.2),
                        inset 0 -2px 0 rgba(0, 0, 0, 0.3);
                    border: 3px solid rgba(255, 255, 255, 0.3);
                    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                    position: relative;
                    overflow: hidden;
                }
                .start-recording-btn::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: linear-gradient(45deg, 
                        rgba(255, 255, 255, 0.2) 0%, 
                        rgba(255, 255, 255, 0.3) 25%, 
                        rgba(0, 0, 0, 0.1) 50%, 
                        rgba(255, 255, 255, 0.2) 75%, 
                        rgba(0, 0, 0, 0.1) 100%);
                    border-radius: 9999px;
                    pointer-events: none;
                }
                .start-recording-btn::after {
                    content: '';
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    width: 2rem;
                    height: 2rem;
                    background: white;
                    border-radius: 50%;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
                    pointer-events: none;
                }
                .start-recording-btn:active {
                    transform: scale(0.95);
                    box-shadow: 
                        0 0 0 6px rgba(255, 255, 255, 0.1),
                        0 0 0 12px rgba(255, 0, 0, 0.15),
                        0 6px 24px 0 rgba(255, 0, 0, 0.3), 
                        0 2px 8px 0 rgba(0,0,0,0.15),
                        inset 0 2px 0 rgba(255, 255, 255, 0.1),
                        inset 0 -2px 0 rgba(0, 0, 0, 0.2);
                    filter: brightness(0.9);
                }
                .start-recording-btn:hover {
                    box-shadow: 
                        0 0 0 6px rgba(255, 255, 255, 0.2),
                        0 0 0 12px rgba(255, 0, 0, 0.25),
                        0 16px 64px 0 rgba(255, 0, 0, 0.5), 
                        0 6px 24px 0 rgba(0,0,0,0.25),
                        inset 0 2px 0 rgba(255, 255, 255, 0.25),
                        inset 0 -2px 0 rgba(0, 0, 0, 0.4);
                }
                .stop-recording-btn {
                    width: 8rem;
                    height: 8rem;
                    border-radius: 9999px;
                    background: linear-gradient(135deg, #ff0000 0%, #cc0000 50%, #990000 100%);
                    box-shadow: 
                        0 0 0 6px rgba(255, 255, 255, 0.15),
                        0 0 0 12px rgba(255, 0, 0, 0.2),
                        0 12px 48px 0 rgba(255, 0, 0, 0.4), 
                        0 4px 16px 0 rgba(0,0,0,0.2),
                        inset 0 2px 0 rgba(255, 255, 255, 0.2),
                        inset 0 -2px 0 rgba(0, 0, 0, 0.3);
                    border: 3px solid rgba(255, 255, 255, 0.3);
                    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                    position: relative;
                    overflow: hidden;
                }
                .stop-recording-btn::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: linear-gradient(45deg, 
                        rgba(255, 255, 255, 0.2) 0%, 
                        rgba(255, 255, 255, 0.3) 25%, 
                        rgba(0, 0, 0, 0.1) 50%, 
                        rgba(255, 255, 255, 0.2) 75%, 
                        rgba(0, 0, 0, 0.1) 100%);
                    border-radius: 9999px;
                    pointer-events: none;
                }
                .stop-recording-btn::after {
                    content: '';
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    width: 2rem;
                    height: 2rem;
                    background: black;
                    border-radius: 0.25rem;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                    pointer-events: none;
                }
                .stop-recording-btn:active {
                    transform: scale(0.95);
                    box-shadow: 
                        0 0 0 6px rgba(255, 255, 255, 0.1),
                        0 0 0 12px rgba(255, 0, 0, 0.15),
                        0 6px 24px 0 rgba(255, 0, 0, 0.3), 
                        0 2px 8px 0 rgba(0,0,0,0.15),
                        inset 0 2px 0 rgba(255, 255, 255, 0.1),
                        inset 0 -2px 0 rgba(0, 0, 0, 0.2);
                    filter: brightness(0.9);
                }
                .stop-recording-btn:hover {
                    box-shadow: 
                        0 0 0 6px rgba(255, 255, 255, 0.2),
                        0 0 0 12px rgba(255, 0, 0, 0.25),
                        0 16px 64px 0 rgba(255, 0, 0, 0.5), 
                        0 6px 24px 0 rgba(0,0,0,0.25),
                        inset 0 2px 0 rgba(255, 255, 255, 0.25),
                        inset 0 -2px 0 rgba(0, 0, 0, 0.4);
                }
            `}</style>
            </div>
        </>
    );
}