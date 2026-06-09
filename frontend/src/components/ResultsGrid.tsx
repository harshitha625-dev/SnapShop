import React from "react";
import ProductCard from "./ProductCard";
import { motion } from "framer-motion";

interface ResultsGridProps {
    matches: any[];
}

export default function ResultsGrid({ matches }: ResultsGridProps) {
    if (!matches || matches.length === 0) return null;

    return (
        <motion.div 
            initial="hidden"
            animate="visible"
            variants={{
                hidden: { opacity: 0 },
                visible: {
                    opacity: 1,
                    transition: { staggerChildren: 0.05 }
                }
            }}
            className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6"
        >
            {matches.map((match, idx) => (
                <ProductCard key={idx} item={match} />
            ))}
        </motion.div>
    );
}
