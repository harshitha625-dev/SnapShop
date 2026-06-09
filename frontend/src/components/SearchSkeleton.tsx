import React from "react";

export default function SearchSkeleton() {
    return (
        <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8 w-full">
            {/* Header Skeleton */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                    <div className="h-10 w-48 bg-gray-200 rounded-lg animate-shimmer bg-[linear-gradient(90deg,#f3f4f6,25%,#e5e7eb,50%,#f3f4f6,75%)] bg-size-[200%_100%]"></div>
                    <div className="h-4 w-32 bg-gray-200 rounded mt-2 animate-shimmer bg-[linear-gradient(90deg,#f3f4f6,25%,#e5e7eb,50%,#f3f4f6,75%)] bg-size-[200%_100%]"></div>
                </div>
                <div className="h-10 w-32 bg-gray-200 rounded-full animate-shimmer bg-[linear-gradient(90deg,#f3f4f6,25%,#e5e7eb,50%,#f3f4f6,75%)] bg-size-[200%_100%]"></div>
            </div>

            {/* Platforms Skeleton */}
            <div className="mb-12">
                <div className="h-6 w-40 bg-gray-200 rounded mb-4"></div>
                <div className="flex flex-wrap gap-3">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="h-10 w-32 rounded-full bg-gray-200 animate-shimmer bg-[linear-gradient(90deg,#f3f4f6,25%,#e5e7eb,50%,#f3f4f6,75%)] bg-size-[200%_100%]"></div>
                    ))}
                </div>
            </div>

            {/* Grid Skeleton */}
            <div>
                <div className="h-6 w-40 bg-gray-200 rounded mb-6"></div>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                        <div key={i} className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
                            <div className="aspect-square w-full rounded-xl bg-gray-200 mb-4 animate-shimmer bg-[linear-gradient(90deg,#f3f4f6,25%,#e5e7eb,50%,#f3f4f6,75%)] bg-size-[200%_100%]"></div>
                            <div className="h-4 w-3/4 bg-gray-200 rounded mb-2 animate-shimmer bg-[linear-gradient(90deg,#f3f4f6,25%,#e5e7eb,50%,#f3f4f6,75%)] bg-size-[200%_100%]"></div>
                            <div className="h-4 w-1/2 bg-gray-200 rounded mb-4 animate-shimmer bg-[linear-gradient(90deg,#f3f4f6,25%,#e5e7eb,50%,#f3f4f6,75%)] bg-size-[200%_100%]"></div>
                            <div className="flex justify-between items-center">
                                <div className="h-4 w-1/3 bg-gray-200 rounded animate-shimmer bg-[linear-gradient(90deg,#f3f4f6,25%,#e5e7eb,50%,#f3f4f6,75%)] bg-size-[200%_100%]"></div>
                                <div className="h-6 w-16 bg-gray-200 rounded-md animate-shimmer bg-[linear-gradient(90deg,#f3f4f6,25%,#e5e7eb,50%,#f3f4f6,75%)] bg-size-[200%_100%]"></div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
