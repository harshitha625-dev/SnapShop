"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import toast from "react-hot-toast";
import api from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, Loader2, Image as ImageIcon } from "lucide-react";

interface Props {
    onUploadComplete: (imageUrl: string, imageHash: string) => void;
}

export default function ImageUploader({ onUploadComplete }: Props) {
    const [preview, setPreview] = useState<string | null>(null);
    const [uploading, setUploading] = useState(false);

    const handleFile = useCallback(async (file: File) => {
        setPreview(URL.createObjectURL(file));
        setUploading(true);
        try {
            const form = new FormData();
            form.append("file", file);
            const { data } = await api.post("/upload", form);
            toast.success("AI search initiated...");
            onUploadComplete(data.image_url, data.image_hash);
        } catch {
            toast.error("Upload failed. Try again.");
            setPreview(null);
        } finally {
            setUploading(false);
        }
    }, [onUploadComplete]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop: (files) => files[0] && handleFile(files[0]),
        accept: { "image/*": [".jpg", ".jpeg", ".png", ".webp"] },
        maxFiles: 1,
        disabled: uploading,
    });

    return (
        <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="w-full max-w-xl mx-auto"
        >
            <div 
                {...getRootProps()} 
                className={`
                    relative group cursor-pointer overflow-hidden rounded-3xl border-2 border-dashed
                    transition-all duration-300 ease-in-out p-12 flex flex-col items-center justify-center
                    min-h-[320px] bg-white/50 backdrop-blur-sm
                    ${isDragActive ? "border-primary-500 bg-primary-50/50 scale-[1.02] shadow-xl shadow-primary-500/10" : "border-gray-200 hover:border-primary-400 hover:bg-gray-50"}
                    ${uploading ? "opacity-75 pointer-events-none" : ""}
                `}
            >
                <input {...getInputProps()} />
                
                <AnimatePresence mode="wait">
                    {preview ? (
                        <motion.div 
                            key="preview"
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            className="absolute inset-0 z-10 p-2"
                        >
                            <div className="relative w-full h-full rounded-2xl overflow-hidden shadow-lg border border-gray-100">
                                <img src={preview} alt="preview" className="w-full h-full object-cover" />
                                {uploading && (
                                    <div className="absolute inset-0 bg-black/40 backdrop-blur-sm flex flex-col items-center justify-center text-white">
                                        <Loader2 className="w-10 h-10 animate-spin mb-3 text-primary-400" />
                                        <span className="font-medium tracking-wide">Analyzing Image...</span>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    ) : (
                        <motion.div 
                            key="placeholder"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="flex flex-col items-center justify-center text-center space-y-4"
                        >
                            <div className={`p-4 rounded-full transition-colors duration-300 ${isDragActive ? "bg-primary-100 text-primary-600" : "bg-gray-100 text-gray-400 group-hover:bg-primary-50 group-hover:text-primary-500"}`}>
                                <UploadCloud className="w-10 h-10" />
                            </div>
                            <div>
                                <p className="text-lg font-semibold text-gray-700">
                                    {isDragActive ? "Drop the image here" : "Click or drag an image"}
                                </p>
                                <p className="text-sm text-gray-500 mt-2">
                                    Supports JPG, JPEG, PNG, WEBP
                                </p>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
}