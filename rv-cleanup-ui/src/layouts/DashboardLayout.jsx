import { NavLink } from "react-router-dom";
import { FaUpload, FaEnvelopeOpenText, FaTimesCircle } from "react-icons/fa";
import TopNavbar from "../components/TopNavbar";
import React from "react";


function DashboardLayout({ children }) {
    return (
        <div className="flex min-h-screen bg-gray-100 font-sans text-gray-800">
            {/* Sidebar */}
            <aside className="w-64 bg-white border-r shadow-lg flex flex-col">
                <div className="h-16 px-6 flex items-center border-b font-bold text-xl text-teal-600">
                    <img src="/logo.jpeg" alt="RV Cleanup Logo" className="w-14 mx-auto" />
                </div>
                <nav className="flex-1 px-6 py-4 space-y-2 text-gray-700">
                    <NavLink
                        to="/upload"
                        className={({ isActive }) =>
                            `flex items-center gap-3 px-4 py-2 rounded-md transition ${isActive
                                ? "bg-teal-100 text-teal-700 font-semibold"
                                : "hover:bg-gray-100"
                            }`
                        }
                    >
                        <FaUpload />
                        Upload CSV
                    </NavLink>
                    <NavLink
                        to="/master"
                        className={({ isActive }) =>
                            `flex items-center gap-3 px-4 py-2 rounded-md transition ${isActive
                                ? "bg-teal-100 text-teal-700 font-semibold"
                                : "hover:bg-gray-100"
                            }`
                        }
                    >
                        <FaEnvelopeOpenText />
                        Master Emails
                    </NavLink>
                    <NavLink
                        to="/invalid"
                        className={({ isActive }) =>
                            `flex items-center gap-3 px-4 py-2 rounded-md transition ${isActive
                                ? "bg-teal-100 text-teal-700 font-semibold"
                                : "hover:bg-gray-100"
                            }`
                        }
                    >
                        <FaTimesCircle />
                        Invalid Emails
                    </NavLink>
                </nav>
                <div className="px-6 py-4 text-xs text-gray-400 border-t">
                    © 2025 RV Tools
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col">
                {/* 👇 Replace this line */}
                <TopNavbar />

                {/* Page Content */}
                <main className="flex-1 p-6 bg-gray-50">{children}</main>
            </div>
        </div>
    );
}

export default DashboardLayout;
