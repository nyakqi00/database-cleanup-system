import React from "react";

const LoadingModal = ({ timeLeft, progress }) => {
    return (
        <div className="mt-4 w-full max-w-md bg-white border border-gray-300 shadow-md rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold text-gray-700">
                    Uploading your file...
                </h4>
                <span className="text-xs text-gray-500">
                    Estimated time left: {timeLeft}s
                </span>
            </div>

            <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
                <div
                    className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-in-out"
                    style={{ width: `${progress}%` }}
                />
            </div>

            <button
                disabled
                className="mt-2 w-full text-xs text-blue-600 border border-blue-600 rounded py-1 hover:bg-blue-50 transition"
            >
                View Full Results
            </button>
        </div>
    );
};

export default LoadingModal;
