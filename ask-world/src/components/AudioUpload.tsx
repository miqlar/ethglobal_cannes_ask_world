// src/components/AudioUpload.tsx
'use client';

import { MiniKit } from '@worldcoin/minikit-js';
import { ChangeEvent, useState } from 'react';

export default function AudioUpload() {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState<string>('');

    const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
        const selectedFile = event.target.files?.[0];
        if (selectedFile && selectedFile.type.startsWith('audio/')) {
            setFile(selectedFile);
            setUploadStatus('');
        } else {
            setFile(null);
            setUploadStatus('Please select an audio file');
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setUploadStatus('No file selected');
            return;
        }

        setUploading(true);
        const formData = new FormData();
        formData.append('audio', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                setUploadStatus('Upload successful!');
                setFile(null);
            } else {
                setUploadStatus('Upload failed. Try again.');
            }
        } catch (error) {
            setUploadStatus('Error uploading file.');
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="p-4 max-w-md mx-auto">
            <h1 className="text-2xl font-bold mb-4">Upload Audio</h1>
            <input
                type="file"
                accept="audio/*"
                onChange={handleFileChange}
                className="mb-4 p-2 border rounded w-full"
            />
            {uploadStatus && <p className="text-red-500 mb-4">{uploadStatus}</p>}
            <button
                onClick={handleUpload}
                disabled={!file || uploading}
                className="bg-blue-500 text-white px-4 py-2 rounded disabled:bg-gray-400"
            >
                {uploading ? 'Uploading...' : 'Upload Audio'}
            </button>
        </div>
    );
}