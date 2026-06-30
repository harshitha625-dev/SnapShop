"use client";
import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import useImageSearch from "@/hooks/useImageSearch";
import PlatformResultsList from "@/components/PlatformResultsList";
import ResultsGrid from "@/components/ResultsGrid";
import SearchSkeleton from "@/components/SearchSkeleton";
import { ArrowLeft, Sparkles, Image as ImageIcon, Tag, ShoppingBag, ExternalLink } from "lucide-react";
import { motion } from "framer-motion";
import { getBackendRoot } from "@/lib/api";

import { Suspense } from "react";

function ResultsContent() {
    const params = useSearchParams();
    const router = useRouter();
    const imageUrl = params.get("imageUrl") ?? "";
    const imageHash = params.get("imageHash") ?? "";
    const textQuery = params.get("q") ?? "";

    const [selectedCategory, setSelectedCategory] = useState("All");
    const [showOnlyBargains, setShowOnlyBargains] = useState(false);
    const categories = ["All", "Fashion", "Footwear", "Watches", "Electronics", "Bags", "Beauty", "Accessories", "Furniture"];

    const { results, loading, error, search, searchByText } = useImageSearch();

    useEffect(() => {
        if (textQuery) {
            searchByText(textQuery, selectedCategory);
        } else if (imageUrl && imageHash) {
            search({ image_url: imageUrl, image_hash: imageHash }, selectedCategory);
        }
    }, [imageUrl, imageHash, textQuery, selectedCategory]);

    if (loading) return <SearchSkeleton />;
    
    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
                <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full text-center border border-red-100">
                    <div className="w-16 h-16 bg-red-50 text-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h2 className="text-xl font-bold text-gray-900 mb-2">Search Failed</h2>
                    <p className="text-gray-500 mb-6">{error}</p>
                    <button onClick={() => router.push("/")} className="w-full py-3 bg-gray-900 text-white rounded-xl hover:bg-gray-800 transition-colors">
                        Try Another Search
                    </button>
                </div>
            </div>
        );
    }

    if (!results) return null;

    const filteredMatches = results.visual_matches
        ? results.visual_matches.filter((m: any) => {
              if (showOnlyBargains) {
                  return m.is_low_cost === true;
              }
              return true;
          })
        : [];

    const filteredPlatformResults = results.platform_results
        ? results.platform_results.filter((m: any) => {
              if (showOnlyBargains) {
                  return m.is_low_cost === true;
              }
              return true;
          })
        : [];

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header Navbar */}
            <header className="sticky top-0 z-50 glass border-b border-gray-200/50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                    <button 
                        onClick={() => router.push("/")}
                        className="flex items-center text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors group"
                    >
                        <span className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center mr-2 group-hover:bg-gray-200 transition-colors">
                            <ArrowLeft className="w-4 h-4" />
                        </span>
                        New Search
                    </button>
                    
                    <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-primary-500" />
                        <span className="font-bold text-lg text-gray-900 tracking-tight">SnapShap</span>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
                {/* Results Overview */}
                <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col md:flex-row gap-8 mb-12 items-start md:items-center"
                >
                    {/* Thumbnail or Text Query Badge */}
                    {textQuery ? (
                        <div className="w-32 h-32 md:w-auto md:h-auto md:py-6 md:px-8 shrink-0 rounded-2xl bg-white shadow-md border border-gray-100 flex flex-col items-center justify-center text-center">
                            <span className="text-sm text-gray-500 uppercase tracking-wider font-semibold mb-1">Search Query</span>
                            <span className="text-2xl font-bold text-primary-600 capitalize">"{textQuery}"</span>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center gap-3 shrink-0">
                            <div className="w-32 h-32 md:w-40 md:h-40 rounded-2xl overflow-hidden bg-white shadow-md border border-gray-100 p-2">
                                <img 
                                    src={imageUrl.startsWith("http") ? imageUrl : `${getBackendRoot()}${imageUrl}`} 
                                    alt="Uploaded item" 
                                    className="w-full h-full object-cover rounded-xl" 
                                />
                            </div>
                            <button
                                onClick={() => router.push(`/describe?imageUrl=${encodeURIComponent(imageUrl)}&imageHash=${encodeURIComponent(imageHash)}`)}
                                className="w-full py-2 bg-pink-50 hover:bg-pink-100 text-pink-700 text-xs font-bold rounded-xl border border-pink-200/50 shadow-sm flex items-center justify-center gap-1.5 transition-all hover:scale-105 active:scale-95 cursor-pointer"
                            >
                                <Sparkles className="w-3.5 h-3.5 text-pink-500" />
                                AI Describe Image
                            </button>
                        </div>
                    )}
                    
                    {/* Summary Text */}
                    <div className="flex-1 pt-2">
                        <h1 className="text-4xl font-black text-gray-900 mb-2 tracking-tight">
                            Search <span className="text-primary-600">Results</span>
                        </h1>
                        <div className="flex flex-wrap items-center gap-2 mb-4">
                            <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium">
                                Query: {textQuery || "Image Search"}
                            </span>
                            <span className="px-3 py-1 bg-primary-50 text-primary-600 rounded-lg text-sm font-medium">
                                Category: {selectedCategory}
                            </span>
                            {results && (
                                <span className="px-3 py-1 bg-green-50 text-green-600 rounded-lg text-sm font-medium">
                                    {results.total_results || 0} Matches Found
                                </span>
                            )}
                        </div>
                        <p className="text-lg text-gray-500">
                            {textQuery 
                                ? `Showing shopping results for "${textQuery}" filtered by ${selectedCategory}.`
                                : "We analyzed your image and found visually similar products in your catalog."}
                        </p>
                    </div>
                </motion.div>

                {/* Category Filter */}
                <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="mb-10"
                >
                    <div className="flex items-center gap-3 mb-4">
                        <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Filter by category</span>
                        <div className="h-px flex-1 bg-gray-100"></div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {categories.map((cat) => (
                            <button
                                key={cat}
                                onClick={() => setSelectedCategory(cat)}
                                className={`px-5 py-2.5 rounded-full text-sm font-semibold transition-all duration-200 border ${
                                    selectedCategory === cat
                                        ? "bg-primary-600 text-white border-primary-600 shadow-lg shadow-primary-200 scale-105"
                                        : "bg-white text-gray-600 border-gray-200 hover:border-primary-300 hover:text-primary-600"
                                }`}
                            >
                                {cat}
                            </button>
                        ))}
                    </div>
                </motion.div>

                {/* AI Cost Predictor Card */}
                {results.low_cost_prediction && results.low_cost_prediction.low_cost_threshold > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 15 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                        className="mb-10 bg-white/70 backdrop-blur-xl border border-white/50 shadow-lg rounded-3xl p-6 md:p-8 relative overflow-hidden"
                    >
                        {/* Glowing Background Blob */}
                        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-48 h-48 bg-green-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse"></div>

                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
                            <div className="flex-1 space-y-4">
                                <div className="flex items-center gap-2.5">
                                    <span className="flex items-center gap-1 py-1 px-3 rounded-full bg-green-50 text-green-700 text-xs font-bold uppercase border border-green-200/50">
                                        🧠 AI Cost Predictor
                                    </span>
                                    <span className={`py-1 px-3 rounded-full text-xs font-bold uppercase border ${
                                        results.low_cost_prediction.deal_rating.includes("Spectacular")
                                            ? "bg-purple-50 text-purple-700 border-purple-200/50"
                                            : results.low_cost_prediction.deal_rating.includes("Great")
                                            ? "bg-blue-50 text-blue-700 border-blue-200/50"
                                            : "bg-gray-50 text-gray-700 border-gray-200/50"
                                    }`}>
                                        {results.low_cost_prediction.deal_rating}
                                    </span>
                                </div>

                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-2">
                                    <div className="flex flex-col">
                                        <span className="text-[11px] text-gray-400 font-extrabold uppercase tracking-widest">Low-Cost Sweet Spot</span>
                                        <span className="text-3xl font-black text-green-600 mt-1">
                                            ₹{results.low_cost_prediction.low_cost_threshold.toLocaleString()}
                                        </span>
                                        <span className="text-[10px] text-gray-500 font-medium mt-0.5">Predicted bargain threshold</span>
                                    </div>
                                    <div className="flex flex-col sm:border-l sm:border-gray-100 sm:pl-6">
                                        <span className="text-[11px] text-gray-400 font-extrabold uppercase tracking-widest">Average Market Price</span>
                                        <span className="text-2xl font-bold text-gray-800 mt-1">
                                            ₹{results.low_cost_prediction.average_price.toLocaleString()}
                                        </span>
                                        <span className="text-[10px] text-gray-500 font-medium mt-0.5">Based on similar items</span>
                                    </div>
                                    <div className="flex flex-col sm:border-l sm:border-gray-100 sm:pl-6">
                                        <span className="text-[11px] text-gray-400 font-extrabold uppercase tracking-widest">Price Spectrum</span>
                                        <span className="text-base font-bold text-gray-700 mt-1.5 flex items-center gap-1">
                                            ₹{results.low_cost_prediction.min_price.toLocaleString()} 
                                            <span className="text-gray-400 font-normal text-xs">to</span> 
                                            ₹{results.low_cost_prediction.max_price.toLocaleString()}
                                        </span>
                                        <span className="text-[10px] text-gray-500 font-medium mt-0.5">Min & Max range</span>
                                    </div>
                                </div>

                                <p className="text-sm text-gray-600 leading-relaxed font-medium pt-2">
                                    {results.low_cost_prediction.prediction_reasoning}
                                </p>
                            </div>

                            {/* Toggle Bargains Control */}
                            <div className="shrink-0 md:pl-6 md:border-l md:border-gray-100 flex flex-col items-start md:items-end justify-center gap-2">
                                <label className="flex items-center gap-3 cursor-pointer group">
                                    <div className="flex flex-col items-start md:items-end select-none">
                                        <span className="text-sm font-bold text-gray-900 group-hover:text-primary-600 transition-colors">
                                            Filter Low Cost Deals
                                        </span>
                                        <span className="text-[11px] text-green-600 font-bold">
                                            {results.low_cost_prediction.bargain_count} bargain options
                                        </span>
                                    </div>
                                    <div className="relative">
                                        <input
                                            type="checkbox"
                                            checked={showOnlyBargains}
                                            onChange={(e) => setShowOnlyBargains(e.target.checked)}
                                            className="sr-only peer"
                                        />
                                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-500"></div>
                                    </div>
                                </label>
                            </div>
                        </div>

                        {/* Lowest Price Deal Alert */}
                        {results.lowest_price_deal && (
                            <div className="mt-6 p-4 bg-green-50 border border-green-200/60 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative z-10">
                                <div className="flex items-start gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-green-500 flex items-center justify-center text-white shrink-0 shadow-md shadow-green-500/20">
                                        <ShoppingBag className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h4 className="text-xs font-bold uppercase tracking-wider text-green-800">Absolute Lowest Price Deal Found!</h4>
                                        <p className="text-sm font-semibold text-gray-900 mt-0.5">
                                            {results.lowest_price_deal.title}
                                        </p>
                                        <p className="text-xs text-gray-500 mt-0.5">
                                            Available for <span className="font-bold text-green-600 text-sm">{results.lowest_price_deal.price}</span> on <span className="font-semibold text-gray-700">{results.lowest_price_deal.platform}</span>
                                        </p>
                                    </div>
                                </div>
                                <a
                                    href={results.lowest_price_deal.buy_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="px-5 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all shadow-md shadow-green-500/10 hover:shadow-green-500/20 hover:scale-102 shrink-0"
                                >
                                    Buy Lowest Price Product
                                    <ExternalLink className="w-3.5 h-3.5" />
                                </a>
                            </div>
                        )}
                    </motion.div>
                )}

                {/* Platforms Section */}
                {filteredPlatformResults && filteredPlatformResults.length > 0 && (
                    <motion.section 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.1 }}
                        className="mb-12"
                    >
                        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                            <span className="w-2 h-6 bg-primary-500 rounded-full"></span>
                            Available on these platforms
                        </h2>
                        <PlatformResultsList results={filteredPlatformResults} />
                    </motion.section>
                )}

                {/* Grid Section */}
                {filteredMatches && filteredMatches.length > 0 && (
                    <motion.section
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.2 }}
                    >
                        <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                            <span className="w-2 h-6 bg-purple-500 rounded-full"></span>
                            Visually Similar Products
                        </h2>
                        <ResultsGrid matches={filteredMatches} />
                    </motion.section>
                )}

                {/* Empty State for Bargain filter */}
                {showOnlyBargains && filteredMatches.length === 0 && results.visual_matches && results.visual_matches.length > 0 && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-center py-16 bg-white rounded-3xl border border-gray-100 shadow-sm"
                    >
                        <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4 text-gray-400">
                            <Tag className="w-8 h-8" />
                        </div>
                        <h3 className="text-lg font-bold text-gray-900 mb-1">No Bargains Found</h3>
                        <p className="text-gray-500 max-w-sm mx-auto text-sm">
                            None of the matches fall below the predicted low-cost sweet spot of ₹{results.low_cost_prediction?.low_cost_threshold?.toLocaleString()}.
                        </p>
                        <button 
                            onClick={() => setShowOnlyBargains(false)}
                            className="mt-4 px-5 py-2 bg-gray-900 hover:bg-gray-800 text-white rounded-xl text-xs font-bold transition-all"
                        >
                            Reset Filter
                        </button>
                    </motion.div>
                )}

                {/* Premium Empty State for No Matches at all */}
                {!showOnlyBargains && filteredMatches.length === 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                        className="max-w-2xl mx-auto text-center py-16 px-8 bg-white/70 backdrop-blur-xl rounded-3xl border border-gray-100 shadow-xl relative overflow-hidden mt-8"
                    >
                        {/* Glowing Background Blob */}
                        <div className="absolute -top-10 -left-10 w-40 h-40 bg-purple-100 rounded-full mix-blend-multiply filter blur-3xl opacity-50"></div>
                        <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-pink-100 rounded-full mix-blend-multiply filter blur-3xl opacity-50"></div>

                        <div className="relative z-10">
                            {/* Graphic Icon Container */}
                            <div className="w-20 h-20 bg-gradient-to-tr from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-purple-500/20 rotate-3 hover:rotate-12 transition-transform duration-300">
                                <ShoppingBag className="w-10 h-10 text-white" />
                            </div>

                            <h3 className="text-3xl font-black text-gray-900 mb-3 tracking-tight">
                                Product Not Found
                            </h3>
                            <p className="text-gray-500 text-base max-w-md mx-auto mb-8 font-medium leading-relaxed">
                                We couldn't find any visually similar products from <span className="text-primary-600 font-semibold">trusted, purchaseable e-commerce platforms</span> matching your search.
                            </p>

                            <div className="h-px bg-gray-100 w-full mb-8"></div>

                            {/* Options to proceed */}
                            <div className="space-y-6 text-left max-w-lg mx-auto">
                                <div>
                                    <h4 className="text-sm font-bold text-gray-800 uppercase tracking-wider mb-3 flex items-center gap-2">
                                        <Sparkles className="w-4 h-4 text-purple-500" />
                                        Option 1: Try natural language search
                                    </h4>
                                    <form
                                        onSubmit={(e) => {
                                            e.preventDefault();
                                            const q = new FormData(e.currentTarget).get("q");
                                            if (q) router.push(`/results?q=${encodeURIComponent(q.toString())}`);
                                        }}
                                        className="relative w-full"
                                    >
                                        <input
                                            type="text"
                                            name="q"
                                            placeholder="e.g. red ethnic women kurta under 2000..."
                                            className="w-full pl-5 pr-28 py-3.5 rounded-2xl border border-gray-200 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm transition-shadow hover:shadow-md bg-white"
                                        />
                                        <button
                                            type="submit"
                                            className="absolute right-1.5 top-1.5 bottom-1.5 px-4 bg-gray-900 hover:bg-primary-600 text-white rounded-xl flex items-center justify-center text-xs font-bold transition-all shadow-md group cursor-pointer"
                                        >
                                            AI Search
                                        </button>
                                    </form>
                                </div>

                                <div className="pt-2">
                                    <h4 className="text-sm font-bold text-gray-800 uppercase tracking-wider mb-3 flex items-center gap-2">
                                        <ImageIcon className="w-4 h-4 text-pink-500" />
                                        Option 2: Try another photo
                                    </h4>
                                    <div className="flex flex-col sm:flex-row gap-3">
                                        <button
                                            onClick={() => router.push("/")}
                                            className="flex-grow py-3 bg-white hover:bg-gray-50 text-gray-800 border border-gray-200 rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-sm transition-all hover:scale-102 cursor-pointer"
                                        >
                                            <ArrowLeft className="w-4 h-4" />
                                            Go Back & Upload Image
                                        </button>
                                        {imageUrl && (
                                            <button
                                                onClick={() => router.push(`/describe?imageUrl=${encodeURIComponent(imageUrl)}&imageHash=${encodeURIComponent(imageHash)}`)}
                                                className="flex-grow py-3 bg-pink-50 hover:bg-pink-100 text-pink-700 border border-pink-200/50 rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-sm transition-all hover:scale-102 cursor-pointer animate-pulse"
                                            >
                                                <Sparkles className="w-4 h-4 text-pink-500" />
                                                Analyze Image with AI
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </main>
        </div>
    );
}

export default function ResultsPage() {
    return (
        <Suspense fallback={<SearchSkeleton />}>
            <ResultsContent />
        </Suspense>
    );
}