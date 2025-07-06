'use client';

import { useEffect, useState } from 'react';

interface ConfettiPiece {
    id: number;
    x: number;
    y: number;
    rotation: number;
    scale: number;
    color: string;
    velocity: { x: number; y: number };
}

const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff', '#5f27cd'];

export default function Confetti({ isActive }: { isActive: boolean }) {
    const [pieces, setPieces] = useState<ConfettiPiece[]>([]);

    useEffect(() => {
        if (!isActive) {
            setPieces([]);
            return;
        }

        // Create confetti pieces
        const newPieces: ConfettiPiece[] = Array.from({ length: 100 }, (_, i) => ({
            id: i,
            x: Math.random() * window.innerWidth,
            y: -10,
            rotation: Math.random() * 360,
            scale: Math.random() * 0.5 + 0.5,
            color: colors[Math.floor(Math.random() * colors.length)],
            velocity: {
                x: (Math.random() - 0.5) * 8,
                y: Math.random() * 3 + 2
            }
        }));

        setPieces(newPieces);

        // Animate confetti
        const interval = setInterval(() => {
            setPieces(prev =>
                prev.map(piece => ({
                    ...piece,
                    x: piece.x + piece.velocity.x,
                    y: piece.y + piece.velocity.y,
                    rotation: piece.rotation + 2
                })).filter(piece => piece.y < window.innerHeight + 100)
            );
        }, 50);

        return () => clearInterval(interval);
    }, [isActive]);

    if (!isActive) return null;

    return (
        <div className="fixed inset-0 pointer-events-none z-50">
            {pieces.map(piece => (
                <div
                    key={piece.id}
                    className="absolute w-2 h-2 rounded-full"
                    style={{
                        left: piece.x,
                        top: piece.y,
                        backgroundColor: piece.color,
                        transform: `rotate(${piece.rotation}deg) scale(${piece.scale})`,
                        transition: 'transform 0.1s ease-out'
                    }}
                />
            ))}
        </div>
    );
} 