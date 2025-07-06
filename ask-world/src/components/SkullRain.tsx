'use client';

import { useEffect, useState } from 'react';

interface SkullPiece {
    id: number;
    x: number;
    y: number;
    rotation: number;
    scale: number;
    velocity: { x: number; y: number };
}

export default function SkullRain({ isActive }: { isActive: boolean }) {
    const [skulls, setSkulls] = useState<SkullPiece[]>([]);

    useEffect(() => {
        if (!isActive) {
            setSkulls([]);
            return;
        }

        // Create skull pieces
        const newSkulls: SkullPiece[] = Array.from({ length: 20 }, (_, i) => ({
            id: i,
            x: Math.random() * window.innerWidth,
            y: -50,
            rotation: Math.random() * 360,
            scale: Math.random() * 0.8 + 0.6,
            velocity: {
                x: (Math.random() - 0.5) * 4,
                y: Math.random() * 4 + 3
            }
        }));

        setSkulls(newSkulls);

        // Animate skulls
        const interval = setInterval(() => {
            setSkulls(prev =>
                prev.map(skull => ({
                    ...skull,
                    x: skull.x + skull.velocity.x,
                    y: skull.y + skull.velocity.y,
                    rotation: skull.rotation + 1
                })).filter(skull => skull.y < window.innerHeight + 100)
            );
        }, 50);

        return () => clearInterval(interval);
    }, [isActive]);

    if (!isActive) return null;

    return (
        <div className="fixed inset-0 pointer-events-none z-50">
            {skulls.map(skull => (
                <div
                    key={skull.id}
                    className="absolute"
                    style={{
                        left: skull.x,
                        top: skull.y,
                        transform: `rotate(${skull.rotation}deg) scale(${skull.scale})`,
                        transition: 'transform 0.1s ease-out'
                    }}
                >
                    <span className="text-2xl">💀</span>
                </div>
            ))}
        </div>
    );
} 