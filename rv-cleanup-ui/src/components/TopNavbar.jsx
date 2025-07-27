import { FaUserCircle } from "react-icons/fa";
import { HiOutlineMenuAlt2 } from "react-icons/hi";
import React from "react";

const TopNavbar = () => {
    return (
        <header className="w-full bg-white shadow-md px-6 py-3 flex items-center justify-between">
            {/* Logo or Brand */}
            <div className="flex items-center gap-3">
                <HiOutlineMenuAlt2 className="text-2xl text-gray-700 cursor-pointer" />
                <h1 className="text-xl font-bold text-red-700">Revenue Valley</h1>
            </div>

            {/* Right Side */}
            <div className="flex items-center gap-4">
                <span className="text-sm text-gray-500 hidden sm:inline">Welcome back 👋</span>
                <FaUserCircle className="text-2xl text-gray-500 cursor-pointer" />
            </div>
        </header>
    );
};

export default TopNavbar;
