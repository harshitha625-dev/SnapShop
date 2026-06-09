import React from "react";
import { ExternalLink, ShoppingBag } from "lucide-react";
import { motion } from "framer-motion";

interface PlatformResultsListProps {
    results: any[];
}

export default function PlatformResultsList({ results }: PlatformResultsListProps) {
    if (!results || results.length === 0) return null;

    return (
        <div className="flex flex-wrap gap-3">
            {results.map((item, idx) => (
                <motion.a
                    key={idx}
                    href={item.affiliate_url || item.product_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: idx * 0.05 }}
                    whileHover={{ scale: 1.05, y: -2 }}
                    whileTap={{ scale: 0.95 }}
                    className="flex items-center gap-3 px-4 py-2 bg-white border border-gray-100 shadow-sm rounded-2xl text-sm font-medium text-gray-700 hover:text-primary-600 hover:border-primary-100 hover:shadow-md transition-all group"
                >
                    <div className="w-8 h-8 rounded-lg overflow-hidden bg-gray-100 shrink-0 border border-gray-50">
                        <img 
                            src={item.thumbnail} 
                            alt={item.platform} 
                            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300" 
                        />
                    </div>
                    <div className="flex flex-col items-start leading-tight">
                        <span className="text-[10px] text-gray-400 uppercase font-bold tracking-tighter">Available on</span>
                        <span className="truncate max-w-[100px]">{item.platform}</span>
                    </div>
                    {item.price && (
                        <div className="ml-auto pl-2 border-l border-gray-100 flex flex-col items-end">
                            <span className="text-[10px] text-gray-400 font-bold uppercase tracking-tighter">Price</span>
                            <span className="text-primary-600 font-bold text-sm">
                                {item.price}
                            </span>
                        </div>
                    )}
                    <ExternalLink className="w-3 h-3 ml-1 opacity-50 group-hover:opacity-100 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                </motion.a>
            ))}
        </div>
    );
}
