'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';

interface FeedItem {
    question: string;
    answer: string;
    reward: number;
    timestamp: string;
    questionId: number;
}

export default function FeedPage() {
    const [feedItems, setFeedItems] = useState<FeedItem[]>([]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchFeedData();
    }, []);

    const fetchFeedData = async () => {
        setError(null);

        // Fallback to sample data for demonstration
        const sampleItems: FeedItem[] = [
            {
                question: "What's your favorite way to spend a weekend?",
                answer: "I love hiking in the mountains and then having a cozy dinner with friends. The combination of nature and good company always recharges me.",
                reward: 50,
                timestamp: new Date(Date.now() - 86400000).toISOString(),
                questionId: 1
            },
            {
                question: "If you could have dinner with anyone, who would it be?",
                answer: "I would choose to have dinner with my grandmother who passed away when I was young. I'd love to hear her stories and wisdom.",
                reward: 75,
                timestamp: new Date(Date.now() - 172800000).toISOString(),
                questionId: 2
            },
            {
                question: "What's the most valuable lesson you've learned?",
                answer: "The most valuable lesson I've learned is that failure is not the opposite of success, it's part of the journey. Every setback teaches you something important.",
                reward: 100,
                timestamp: new Date(Date.now() - 259200000).toISOString(),
                questionId: 3
            }
        ];
        setFeedItems(sampleItems);
    };

    const formatTimestamp = (timestamp: string) => {
        const date = new Date(timestamp);
        const now = new Date();
        const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

        if (diffInHours < 1) return 'Just now';
        if (diffInHours < 24) return `${diffInHours}h ago`;
        if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
        return date.toLocaleDateString();
    };


    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-500">
            {/* Header */}
            <div className="bg-white/90 shadow-lg">
                <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Image src="/askworld-logo.png" alt="Ask World Logo" width={40} height={40} className="rounded-full" />
                        <h1 className="text-xl font-bold text-gray-900">Ask World Feed</h1>
                    </div>
                    <Link
                        href="/"
                        className="w-12 h-12 flex items-center justify-center rounded-full bg-gradient-to-r from-purple-500 to-indigo-500 text-white hover:from-purple-600 hover:to-indigo-600 transition-all shadow-lg"
                        aria-label="Back to Home"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
                            <path d="M3 12l9-9 9 9" />
                            <path d="M4 10v10a1 1 0 001 1h5m4 0h5a1 1 0 001-1V10" />
                        </svg>
                    </Link>
                </div>
            </div>

            {/* Feed Content */}
            <div className="max-w-2xl mx-auto px-4 py-6">
                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6">
                        {error}
                    </div>
                )}

                {feedItems.length === 0 ? (
                    <div className="bg-white/90 rounded-3xl shadow-2xl p-8 text-center">
                        <Image src="/askworld-logo.png" alt="Ask World Logo" width={120} height={120} className="mx-auto mb-4" />
                        <h2 className="text-xl font-bold text-gray-900 mb-2">No Questions Yet</h2>
                        <p className="text-gray-600 mb-4">Be the first to ask a question and see answers here!</p>
                        <Link
                            href="/"
                            className="px-6 py-3 rounded-full bg-gradient-to-r from-green-500 to-blue-500 text-white font-semibold hover:from-green-600 hover:to-blue-600 transition-all"
                        >
                            Ask a Question
                        </Link>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {feedItems.map((item, index) => (
                            <div key={index} className="bg-white/90 rounded-3xl shadow-2xl p-6 animate-fade-in" style={{ animationDelay: `${index * 0.1}s` }}>
                                {/* Question Header */}
                                <div className="flex items-start gap-3 mb-4">
                                    <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                                        Q
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="text-lg font-semibold text-gray-900 mb-1">
                                            {item.question}
                                        </h3>
                                        <div className="flex items-center gap-2 text-sm text-gray-500">
                                            <span>Question #{item.questionId}</span>
                                            <span>•</span>
                                            <span>{formatTimestamp(item.timestamp)}</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Answer */}
                                <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-2xl p-4 mb-4">
                                    <div className="flex items-start gap-3">
                                        <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                                            A
                                        </div>
                                        <div className="flex-1">
                                            <p className="text-gray-800 leading-relaxed">
                                                {item.answer}
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                {/* Reward Badge */}
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <span className="text-green-600 font-semibold">💰</span>
                                        <span className="text-green-600 font-semibold">
                                            {item.reward.toFixed(2)} USDC Reward
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-green-500">✅</span>
                                        <span className="text-green-600 font-medium text-sm">Validated</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <style jsx global>{`
                @keyframes fade-in {
                    0% { 
                        opacity: 0; 
                        transform: translateY(20px); 
                    }
                    100% { 
                        opacity: 1; 
                        transform: translateY(0); 
                    }
                }
                .animate-fade-in {
                    animation: fade-in 0.6s ease-out forwards;
                    opacity: 0;
                }
            `}</style>
        </div>
    );
}