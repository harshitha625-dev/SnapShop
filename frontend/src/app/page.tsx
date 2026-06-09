"use client";

import { useRouter } from "next/navigation";
import ImageUploader from "@/components/ImageUploade";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

export default function HomePage() {
    const router = useRouter();

    const handleUploadComplete = (imageUrl: string, imageHash: string) => {
        router.push(`/results?imageUrl=${encodeURIComponent(imageUrl)}&imageHash=${encodeURIComponent(imageHash)}`);
    };

    return (
        <main className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden bg-gray-50 selection:bg-primary-500/30">
            {/* Animated Background Blobs */}
            <div className="absolute top-0 -left-4 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-2xl opacity-70 animate-blob"></div>
            <div className="absolute top-0 -right-4 w-72 h-72 bg-yellow-300 rounded-full mix-blend-multiply filter blur-2xl opacity-70 animate-blob" style={{ animationDelay: "2s" }}></div>
            <div className="absolute -bottom-8 left-20 w-72 h-72 bg-pink-300 rounded-full mix-blend-multiply filter blur-2xl opacity-70 animate-blob" style={{ animationDelay: "4s" }}></div>

            <div className="relative z-10 w-full max-w-4xl px-6 flex flex-col items-center text-center">
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                    className="mb-12 space-y-4"
                >
                    <div className="flex items-center justify-center gap-2 mb-4 flex-wrap">
                        <span className="inline-block py-1 px-3 rounded-full bg-primary-100 text-primary-700 text-xs font-bold tracking-widest uppercase animate-pulse">
                            Offline AI Active
                        </span>
                        <span className="inline-block py-1 px-3 rounded-full bg-purple-100 text-purple-700 text-xs font-bold tracking-widest uppercase">
                            CLIP ViT-L-14
                        </span>
                        <button 
                            onClick={() => router.push("/describe")}
                            className="inline-flex items-center gap-1.5 py-1 px-3 rounded-full bg-pink-50 hover:bg-pink-100 text-pink-700 text-xs font-extrabold tracking-widest uppercase border border-pink-200/50 shadow-sm cursor-pointer transition-all hover:scale-105 active:scale-95"
                        >
                            <Sparkles className="w-3.5 h-3.5 text-pink-500" /> AI Image Analyzer
                        </button>
                    </div>
                    <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-gray-900 leading-[0.9]">
                        SnapShap <span className="text-primary-600 italic">AI.</span>
                    </h1>
                    <p className="mt-6 text-xl text-gray-600 max-w-2xl mx-auto font-medium leading-relaxed">
                        The world's most powerful <span className="text-gray-900 font-bold">local visual search engine.</span>
                        Upload an image or describe it—no internet needed.
                    </p>
                </motion.div>

                <div className="w-full max-w-xl mx-auto">
                    {/* Text Search Bar */}
                    <motion.form
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        onSubmit={(e) => {
                            e.preventDefault();
                            const q = new FormData(e.currentTarget).get("q");
                            if (q) router.push(`/results?q=${encodeURIComponent(q.toString())}`);
                        }}
                        className="relative w-full mb-8"
                    >
                        <input
                            type="text"
                            name="q"
                            placeholder="Describe what you are looking for..."
                            className="w-full pl-6 pr-14 py-4 rounded-full border border-gray-200 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-lg transition-shadow hover:shadow-md bg-white/80 backdrop-blur-md"
                        />
                        <button type="submit" className="absolute right-2 top-2 bottom-2 px-6 bg-primary-600 text-white rounded-full flex items-center justify-center gap-2 hover:bg-primary-700 transition-all hover:shadow-lg hover:shadow-primary-200 group">
                            <span className="font-bold text-sm hidden md:block">AI Search</span>
                            <svg className="w-4 h-4 group-hover:rotate-12 transition-transform" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2l2.4 7.2L22 12l-7.6 2.8L12 22l-2.4-7.2L2 12l7.6-2.8L12 2z" /></svg>
                        </button>
                    </motion.form>

                    <div className="flex items-center mb-8">
                        <div className="flex-1 border-t border-gray-200"></div>
                        <span className="px-4 text-gray-400 text-sm font-medium uppercase tracking-wider">or upload an image</span>
                        <div className="flex-1 border-t border-gray-200"></div>
                    </div>

                    <ImageUploader onUploadComplete={handleUploadComplete} />
                </div>
            </div>
        </main>
    );
}
