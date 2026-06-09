import React, { useState } from "react";
import { ExternalLink, ChevronDown, ChevronUp, Tag } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface ProductCardProps {
    item: any;
}

const PLATFORM_COLORS: Record<string, { bg: string; text: string; border: string }> = {
    "Amazon India": { bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-200" },
    "Flipkart": { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200" },
    "Myntra": { bg: "bg-pink-50", text: "text-pink-700", border: "border-pink-200" },
    "Ajio": { bg: "bg-gray-100", text: "text-gray-700", border: "border-gray-300" },
    "Meesho": { bg: "bg-rose-50", text: "text-rose-700", border: "border-rose-200" },
    "Nykaa": { bg: "bg-fuchsia-50", text: "text-fuchsia-700", border: "border-fuchsia-200" },
};

export default function ProductCard({ item }: ProductCardProps) {
    const [expanded, setExpanded] = useState(false);
    
    const originalPlatform = item.source || "Local Catalog";
    const colors = PLATFORM_COLORS[originalPlatform] || { bg: "bg-indigo-50", text: "text-indigo-700", border: "border-indigo-200" };

    const handleMainClick = (e: React.MouseEvent) => {
        const target = e.target as HTMLElement;
        if (target.closest(".prevent-main-click")) {
            return;
        }
        window.open(item.link, "_blank", "noopener,noreferrer");
    };

    return (
        <motion.div
            variants={{
                hidden: { opacity: 0, y: 20 },
                visible: { opacity: 1, y: 0 }
            }}
            whileHover={{ y: -4 }}
            onClick={handleMainClick}
            className={`group block relative bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 border cursor-pointer flex flex-col h-full ${item.is_low_cost ? "border-green-200/80 bg-gradient-to-b from-green-50/10 to-white shadow-green-50/20" : "border-gray-100"}`}
        >
            <div className="aspect-square w-full overflow-hidden bg-gray-100 relative shrink-0">
                {/* AI Low Cost Badge */}
                {item.is_low_cost && (
                    <div className="absolute top-3 left-3 z-10 flex items-center gap-1 px-2 py-0.5 bg-green-500 text-white rounded-full text-[9px] font-black uppercase tracking-wider shadow-md shadow-green-500/20 border border-green-400">
                        <Tag className="w-2.5 h-2.5 shrink-0" />
                        AI Low Cost
                    </div>
                )}
                <img
                    src={item.thumbnail}
                    alt={item.title}
                    className="w-full h-full object-cover group-hover:scale-102 transition-transform duration-500 ease-out"
                    loading="lazy"
                />
                
                {/* Hover Overlay */}
                <div className="absolute inset-0 bg-linear-to-t from-black/40 via-black/0 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-4">
                    <div className="flex items-center text-white text-xs font-semibold">
                        View Product Details <ExternalLink className="w-3.5 h-3.5 ml-1" />
                    </div>
                </div>
            </div>

            <div className="p-4 flex flex-col flex-grow">
                {/* Score & Category */}
                <div className="flex items-center gap-2 mb-2 shrink-0">
                    {item.similarity_score !== undefined && (
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            item.similarity_score > 0.7 
                                ? "bg-green-50 text-green-700 border border-green-100" 
                                : item.similarity_score > 0.4
                                ? "bg-amber-50 text-amber-700 border border-amber-100"
                                : "bg-gray-50 text-gray-600 border border-gray-100"
                        }`}>
                            {Math.round(item.similarity_score * 100)}% Match
                        </span>
                    )}
                    {item.category && item.category !== "unknown" && (
                        <span className="px-2 py-0.5 rounded bg-primary-50 text-primary-600 border border-primary-100 text-[10px] font-bold uppercase tracking-wider">
                            {item.category}
                        </span>
                    )}
                </div>

                {/* Title */}
                <h3 className="text-sm font-semibold text-gray-900 line-clamp-2 leading-snug group-hover:text-primary-600 transition-colors flex-grow">
                    {item.title}
                </h3>

                {/* Best Deal Highlights */}
                {item.lowest_price && item.lowest_price_platform && (
                    <div className="mt-3 py-1.5 px-2.5 bg-green-50/60 rounded-xl border border-green-100/50 flex items-center justify-between gap-1 text-[11px] font-semibold text-green-700 shrink-0">
                        <span className="flex items-center gap-1">
                            <Tag className="w-3 h-3 text-green-600 shrink-0" />
                            Best Deal
                        </span>
                        <span className="font-bold text-[12px]">
                            {item.lowest_price} on {item.lowest_price_platform}
                        </span>
                    </div>
                )}
                
                {/* Main Price & Action */}
                <div className="mt-3 pt-3 border-t border-gray-50 flex items-center justify-between shrink-0">
                    <div className="flex flex-col">
                        <span className="text-[10px] text-gray-400 uppercase font-bold tracking-tight">Price ({originalPlatform})</span>
                        <div className="flex items-center gap-1">
                            <span className="text-base font-bold text-gray-900 leading-none">
                                {item.price || "Check Price"}
                            </span>
                            {item.is_low_cost && (
                                <span className="text-[9px] font-extrabold text-green-600 bg-green-50 border border-green-200/50 px-1 py-0.2 rounded uppercase tracking-tighter">
                                    Bargain
                                </span>
                            )}
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-1 py-1.5 px-3 bg-gray-900 text-white rounded-lg text-[11px] font-bold transition-all group-hover:bg-primary-600 group-hover:shadow-md group-hover:shadow-primary-100">
                        Buy Now
                        <ExternalLink className="w-3 h-3" />
                    </div>
                </div>

                {/* Comparison Accordion Trigger */}
                {item.comparison_prices && item.comparison_prices.length > 1 && (
                    <div className="mt-3 shrink-0 prevent-main-click">
                        <button
                            type="button"
                            onClick={(e) => {
                                e.stopPropagation();
                                setExpanded(!expanded);
                            }}
                            className="w-full flex items-center justify-between py-1 px-1.5 text-[11px] font-bold text-gray-500 hover:text-primary-600 transition-colors rounded-lg bg-gray-50 hover:bg-primary-50/30"
                        >
                            <span className="flex items-center gap-1">
                                📊 Compare across platforms ({item.comparison_prices.length})
                            </span>
                            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </button>

                        <AnimatePresence initial={false}>
                            {expanded && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: "auto", opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="overflow-hidden mt-2"
                                >
                                    <div className="py-2.5 px-2 bg-gray-50/55 border border-gray-100 rounded-xl space-y-2 text-xs">
                                        {item.comparison_prices.map((cp: any, idx: number) => {
                                            return (
                                                <div 
                                                    key={idx} 
                                                    className="flex items-center justify-between p-2 rounded-lg bg-white border border-gray-100/80 transition-all hover:border-primary-100"
                                                >
                                                    <div className="flex flex-col min-w-0">
                                                        <div className="flex items-center gap-1.5">
                                                            <span className={`w-2 h-2 rounded-full ${
                                                                cp.platform === "Amazon India" ? "bg-orange-400" :
                                                                cp.platform === "Flipkart" ? "bg-blue-400" :
                                                                cp.platform === "Myntra" ? "bg-pink-400" :
                                                                cp.platform === "Ajio" ? "bg-gray-400" :
                                                                cp.platform === "Meesho" ? "bg-rose-400" :
                                                                cp.platform === "Nykaa" ? "bg-fuchsia-400" : "bg-indigo-400"
                                                            }`} />
                                                            <span className="font-semibold text-gray-800 truncate text-[11px] max-w-[80px]">
                                                                {cp.platform}
                                                            </span>
                                                            {cp.is_lowest && (
                                                                <span className="px-1.5 py-0.2 bg-green-100 text-green-800 text-[9px] font-bold rounded uppercase tracking-wide shrink-0">
                                                                    Lowest
                                                                </span>
                                                            )}
                                                        </div>
                                                        {cp.discount && (
                                                            <span className="text-[9px] text-green-600 font-bold mt-0.5 leading-none">
                                                                {cp.discount}
                                                            </span>
                                                        )}
                                                    </div>
                                                    <div className="flex items-center gap-2 shrink-0">
                                                        <span className={`font-bold ${cp.is_lowest ? "text-green-600 text-[13px]" : "text-gray-700 text-xs"}`}>
                                                            {cp.price}
                                                        </span>
                                                        <a
                                                            href={cp.buy_url}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className={`p-1 rounded-md text-white ${cp.is_lowest ? "bg-green-600 hover:bg-green-700" : "bg-gray-900 hover:bg-primary-600"} transition-all flex items-center justify-center`}
                                                        >
                                                            <ExternalLink className="w-3 h-3" />
                                                        </a>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                )}
            </div>
        </motion.div>
    );
}
