"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
    ArrowLeft, 
    Sparkles, 
    Tag, 
    Palette, 
    Lightbulb, 
    RefreshCw, 
    ShoppingBag, 
    AlertTriangle, 
    Loader2,
    Shirt
} from "lucide-react";
import api, { getBackendRoot } from "@/lib/api";
import ImageUploader from "@/components/ImageUploade";

interface AnalysisData {
    description: string;
    items: string[];
    colors: string[];
    style_tags: string[];
    suggestions: string[];
    detected_category: string;
    brand: string;
    symbols: string[];
}

const LOADING_STEPS = [
    "Uploading visual assets...",
    "Scanning colors and patterns...",
    "Detecting main items...",
    "Consulting Gemini LLM...",
    "Structuring stylistic details...",
    "Generating product catalog mappings..."
];

function DescribeContent() {
    const params = useSearchParams();
    const router = useRouter();
    
    const imageUrlParam = params.get("imageUrl") ?? "";
    const imageHashParam = params.get("imageHash") ?? "";

    const [imageUrl, setImageUrl] = useState(imageUrlParam);
    const [imageHash, setImageHash] = useState(imageHashParam);
    const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
    const [loading, setLoading] = useState(false);
    const [loadingStep, setLoadingStep] = useState(0);
    const [error, setError] = useState<string | null>(null);

    // Dynamic loading text effect
    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (loading) {
            interval = setInterval(() => {
                setLoadingStep((prev) => (prev + 1) % LOADING_STEPS.length);
            }, 2000);
        } else {
            setLoadingStep(0);
        }
        return () => clearInterval(interval);
    }, [loading]);

    // Perform analysis when imageUrl changes
    const performAnalysis = async (url: string) => {
        setLoading(true);
        setError(null);
        setAnalysis(null);
        try {
            const { data } = await api.post<AnalysisData>("/analyze-image", { image_url: url });
            setAnalysis(data);
        } catch (err: any) {
            const errMsg = err?.response?.data?.detail ?? "Failed to analyze image. Please try again.";
            setError(errMsg);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (imageUrl) {
            performAnalysis(imageUrl);
        }
    }, [imageUrl]);

    const handleUploadComplete = (newUrl: string, newHash: string) => {
        // Update local state and URL query params without triggering full reload
        setImageUrl(newUrl);
        setImageHash(newHash);
        router.replace(`/describe?imageUrl=${encodeURIComponent(newUrl)}&imageHash=${encodeURIComponent(newHash)}`);
    };

    const handleReset = () => {
        setImageUrl("");
        setImageHash("");
        setAnalysis(null);
        setError(null);
        router.replace("/describe");
    };

    const getFullImageUrl = (path: string) => {
        if (!path) return "";
        return path.startsWith("http") ? path : `${getBackendRoot()}${path}`;
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* Header Navbar */}
            <header className="sticky top-0 z-50 glass border-b border-gray-200/50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                    <button 
                        onClick={() => router.push(imageUrl ? `/results?imageUrl=${encodeURIComponent(imageUrl)}&imageHash=${encodeURIComponent(imageHash)}` : "/")}
                        className="flex items-center text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors group"
                    >
                        <span className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center mr-2 group-hover:bg-gray-200 transition-colors">
                            <ArrowLeft className="w-4 h-4" />
                        </span>
                        {imageUrl ? "Back to Search" : "Home"}
                    </button>
                    
                    <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-primary-500 animate-pulse" />
                        <span className="font-bold text-lg text-gray-900 tracking-tight">SnapShap AI</span>
                    </div>
                </div>
            </header>

            <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8 sm:px-6 lg:px-8 flex flex-col justify-center">
                {!imageUrl ? (
                    // Upload View
                    <div className="max-w-xl w-full mx-auto space-y-8 py-12">
                        <div className="text-center space-y-4">
                            <span className="inline-block py-1 px-3 rounded-full bg-primary-50 text-primary-600 text-xs font-bold tracking-widest uppercase">
                                Multimodal LLM Analysis
                            </span>
                            <h1 className="text-4xl md:text-5xl font-black tracking-tight text-gray-900">
                                AI Image <span className="text-primary-600">Analyzer</span>
                            </h1>
                            <p className="text-gray-500 font-medium">
                                Upload a photo to extract stylistic details, colors, items, and fashion advice using Gemini.
                            </p>
                        </div>
                        <ImageUploader onUploadComplete={handleUploadComplete} />
                    </div>
                ) : (
                    // Analysis View
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                        
                        {/* Left Column: Image Preview */}
                        <div className="lg:col-span-5 space-y-6">
                            <motion.div 
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="relative rounded-3xl overflow-hidden bg-white shadow-xl border border-gray-100 p-3"
                            >
                                <div className="aspect-square w-full rounded-2xl overflow-hidden bg-gray-100 relative group">
                                    <img 
                                        src={getFullImageUrl(imageUrl)} 
                                        alt="Analyzed subject" 
                                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                                    />
                                    {loading && (
                                        <div className="absolute inset-0 bg-black/40 backdrop-blur-sm flex flex-col items-center justify-center text-white p-6 text-center">
                                            <Loader2 className="w-12 h-12 animate-spin text-primary-400 mb-4" />
                                            <h3 className="font-bold text-lg">AI is thinking...</h3>
                                            <p className="text-sm text-gray-300 mt-2 max-w-xs h-6 overflow-hidden">
                                                {LOADING_STEPS[loadingStep]}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </motion.div>

                            <div className="flex gap-4">
                                <button
                                    onClick={handleReset}
                                    className="flex-1 py-3.5 bg-white border border-gray-200 hover:border-gray-300 text-gray-700 hover:text-gray-900 rounded-2xl flex items-center justify-center gap-2 font-bold text-sm shadow-sm transition-all active:scale-[0.98]"
                                >
                                    <RefreshCw className="w-4 h-4" />
                                    New Analysis
                                </button>
                            </div>
                        </div>

                        {/* Right Column: Analysis Output */}
                        <div className="lg:col-span-7">
                            <AnimatePresence mode="wait">
                                {loading && (
                                    <motion.div
                                        key="loading"
                                        initial={{ opacity: 0, y: 15 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0 }}
                                        className="bg-white rounded-3xl border border-gray-200/50 p-8 shadow-xl flex flex-col items-center justify-center min-h-[400px] text-center space-y-6"
                                    >
                                        <div className="relative w-20 h-20">
                                            <div className="absolute inset-0 border-4 border-primary-100 rounded-full"></div>
                                            <div className="absolute inset-0 border-4 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
                                            <div className="absolute inset-4 bg-primary-50 rounded-full flex items-center justify-center">
                                                <Sparkles className="w-6 h-6 text-primary-600 animate-pulse" />
                                            </div>
                                        </div>
                                        <div>
                                            <h3 className="text-xl font-bold text-gray-900">Analyzing Image</h3>
                                            <p className="text-gray-500 text-sm mt-1">Reading style semantics with multimodal LLM</p>
                                        </div>
                                        <div className="w-full max-w-xs bg-gray-100 h-1.5 rounded-full overflow-hidden">
                                            <motion.div 
                                                className="bg-primary-600 h-full rounded-full"
                                                animate={{ 
                                                    width: ["10%", "90%"],
                                                }}
                                                transition={{ 
                                                    repeat: Infinity,
                                                    duration: 10,
                                                    ease: "easeInOut"
                                                }}
                                            />
                                        </div>
                                        <p className="text-sm font-medium text-primary-600 italic">
                                            "{LOADING_STEPS[loadingStep]}"
                                        </p>
                                    </motion.div>
                                )}

                                {error && (
                                    <motion.div
                                        key="error"
                                        initial={{ opacity: 0, y: 15 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0 }}
                                        className="bg-white rounded-3xl border border-red-100 p-8 shadow-xl space-y-6"
                                    >
                                        <div className="w-16 h-16 bg-red-50 text-red-500 rounded-2xl flex items-center justify-center">
                                            <AlertTriangle className="w-8 h-8" />
                                        </div>
                                        <div className="space-y-2">
                                            <h3 className="text-2xl font-bold text-gray-900">Analysis Halted</h3>
                                            <p className="text-gray-500 font-medium leading-relaxed">
                                                {error}
                                            </p>
                                        </div>
                                        {error.includes("GEMINI_API_KEY") && (
                                            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-sm text-amber-800 space-y-2">
                                                <span className="font-bold flex items-center gap-1.5">
                                                    💡 Configuration Guide:
                                                </span>
                                                <p className="font-medium">
                                                    1. Create a <code className="bg-amber-100 px-1.5 py-0.5 rounded font-mono text-xs">.env.local</code> file in the project root.
                                                    <br />
                                                    2. Add: <code className="bg-amber-100 px-1.5 py-0.5 rounded font-mono text-xs">GEMINI_API_KEY="AIzaSyYourKeyHere..."</code>
                                                    <br />
                                                    3. Restart the backend terminal.
                                                </p>
                                            </div>
                                        )}
                                        <button
                                            onClick={() => performAnalysis(imageUrl)}
                                            className="px-6 py-3 bg-gray-900 hover:bg-gray-800 text-white font-bold rounded-2xl text-sm transition-all active:scale-[0.98]"
                                        >
                                            Try Again
                                        </button>
                                    </motion.div>
                                )}

                                {analysis && (
                                    <motion.div
                                        key="results"
                                        initial={{ opacity: 0, y: 15 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0 }}
                                        className="space-y-6"
                                    >
                                        {/* Description Block */}
                                        <div className="bg-white rounded-3xl border border-gray-200/50 p-6 md:p-8 shadow-sm space-y-4">
                                            <div className="flex items-center justify-between gap-4 flex-wrap">
                                                <div className="flex items-center gap-2">
                                                    <Sparkles className="w-5 h-5 text-primary-500" />
                                                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">AI Description</span>
                                                </div>
                                                {analysis.brand && analysis.brand.toLowerCase() !== "unbranded" && (
                                                    <span className="inline-flex items-center gap-1 py-1 px-3 bg-primary-50 text-primary-700 text-[10px] font-extrabold rounded-full uppercase tracking-wider border border-primary-100/50">
                                                        🏷️ Brand: {analysis.brand}
                                                    </span>
                                                )}
                                            </div>
                                            <h2 className="text-2xl md:text-3xl font-black text-gray-900 tracking-tight leading-tight">
                                                Visual <span className="text-primary-600">Breakdown</span>
                                            </h2>
                                            <p className="text-gray-600 font-medium text-base md:text-lg leading-relaxed">
                                                {analysis.description}
                                            </p>
                                            
                                            {/* Render Brand/Symbols details if present */}
                                            {((analysis.brand && analysis.brand.toLowerCase() !== "unbranded") || (analysis.symbols && analysis.symbols.length > 0)) && (
                                                <div className="pt-4 border-t border-gray-100 flex flex-wrap items-center gap-x-6 gap-y-3 text-sm font-semibold text-gray-700">
                                                    {analysis.brand && analysis.brand.toLowerCase() !== "unbranded" && (
                                                        <div className="flex items-center gap-1.5">
                                                            <span className="text-gray-400 uppercase text-[10px] font-extrabold tracking-wider">Brand:</span>
                                                            <span className="text-gray-950 font-bold bg-gray-100 px-2.5 py-1 rounded-lg">{analysis.brand}</span>
                                                        </div>
                                                    )}
                                                    {analysis.symbols && analysis.symbols.length > 0 && (
                                                        <div className="flex items-center gap-1.5 flex-wrap">
                                                            <span className="text-gray-400 uppercase text-[10px] font-extrabold tracking-wider">Logos & Symbols:</span>
                                                            <div className="flex gap-1.5 flex-wrap">
                                                                {analysis.symbols.map((sym, i) => (
                                                                    <span key={i} className="text-xs text-purple-700 bg-purple-50 px-2 py-0.5 rounded-md border border-purple-100/50">
                                                                        🎯 {sym}
                                                                    </span>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>

                                        {/* Grid details */}
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            
                                            {/* Dominant Colors */}
                                            <div className="bg-white rounded-3xl border border-gray-200/50 p-6 shadow-sm space-y-4">
                                                <div className="flex items-center gap-2">
                                                    <Palette className="w-5 h-5 text-purple-500" />
                                                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Color Palette</span>
                                                </div>
                                                <div className="flex flex-wrap gap-4 pt-1">
                                                    {analysis.colors.map((color, i) => (
                                                        <div key={i} className="flex flex-col items-center gap-1.5">
                                                            <div 
                                                                className="w-12 h-12 rounded-full border border-gray-200 shadow-inner group relative cursor-pointer"
                                                                style={{ backgroundColor: color }}
                                                            >
                                                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2 py-1 bg-gray-900 text-white text-[10px] font-bold rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap shadow">
                                                                    {color}
                                                                </div>
                                                            </div>
                                                            <span className="text-xs font-semibold text-gray-500 font-mono">{color}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>

                                            {/* Style Vibes */}
                                            <div className="bg-white rounded-3xl border border-gray-200/50 p-6 shadow-sm space-y-4">
                                                <div className="flex items-center gap-2">
                                                    <Shirt className="w-5 h-5 text-pink-500" />
                                                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Aesthetic & Vibe</span>
                                                </div>
                                                <div className="flex flex-wrap gap-2 pt-1">
                                                    {analysis.style_tags.map((tag, i) => (
                                                        <span 
                                                            key={i} 
                                                            className="px-3.5 py-1.5 bg-pink-50 text-pink-700 border border-pink-100 text-xs font-bold rounded-xl uppercase tracking-wider"
                                                        >
                                                            {tag}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Items & Suggestions */}
                                        <div className="bg-white rounded-3xl border border-gray-200/50 p-6 md:p-8 shadow-sm grid grid-cols-1 md:grid-cols-2 gap-8">
                                            {/* Items */}
                                            <div className="space-y-4">
                                                <div className="flex items-center gap-2">
                                                    <Tag className="w-5 h-5 text-amber-500" />
                                                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Detected Items</span>
                                                </div>
                                                <ul className="space-y-2">
                                                    {analysis.items.map((item, i) => (
                                                        <li key={i} className="flex items-center gap-2 text-sm font-semibold text-gray-700">
                                                            <span className="w-1.5 h-1.5 bg-amber-500 rounded-full"></span>
                                                            {item}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>

                                            {/* Suggestions */}
                                            <div className="space-y-4">
                                                <div className="flex items-center gap-2">
                                                    <Lightbulb className="w-5 h-5 text-green-500" />
                                                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Styling Advice</span>
                                                </div>
                                                <ul className="space-y-2">
                                                    {analysis.suggestions.map((sug, i) => (
                                                        <li key={i} className="flex items-start gap-2 text-sm font-medium text-gray-600 leading-relaxed">
                                                            <span className="mt-1.5 w-1 h-1 bg-green-500 rounded-full shrink-0"></span>
                                                            {sug}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        </div>

                                        {/* Shop Catalog Link Action */}
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0.95 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            transition={{ delay: 0.1 }}
                                            className="bg-primary-600 text-white rounded-3xl p-6 md:p-8 shadow-lg shadow-primary-500/20 flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden"
                                        >
                                            {/* Glowing Blob */}
                                            <div className="absolute top-0 right-0 -mr-12 -mt-12 w-40 h-40 bg-white/10 rounded-full blur-2xl"></div>
                                            
                                            <div className="space-y-2 relative z-10">
                                                <span className="inline-block py-0.5 px-2.5 rounded-full bg-white/20 text-white text-[10px] font-extrabold uppercase tracking-wider">
                                                    Catalog Search Link
                                                </span>
                                                <h3 className="text-xl md:text-2xl font-black tracking-tight leading-tight">
                                                    Shop Similar Items Now
                                                </h3>
                                                <p className="text-primary-100 text-sm font-medium max-w-md">
                                                    Search our local store for visually matching products in the <span className="underline font-bold text-white">{analysis.detected_category}</span> category.
                                                </p>
                                            </div>

                                            <button
                                                onClick={() => {
                                                    router.push(`/results?imageUrl=${encodeURIComponent(imageUrl)}&imageHash=${encodeURIComponent(imageHash)}&category=${encodeURIComponent(analysis.detected_category)}`);
                                                }}
                                                className="shrink-0 py-3.5 px-6 bg-white hover:bg-gray-100 text-primary-700 font-extrabold rounded-2xl text-sm flex items-center justify-center gap-2 shadow-lg transition-all active:scale-[0.98] group relative z-10"
                                            >
                                                <ShoppingBag className="w-4 h-4 group-hover:animate-bounce" />
                                                Search Products
                                            </button>
                                        </motion.div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

export default function DescribePage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <Loader2 className="w-10 h-10 animate-spin text-primary-500" />
            </div>
        }>
            <DescribeContent />
        </Suspense>
    );
}
