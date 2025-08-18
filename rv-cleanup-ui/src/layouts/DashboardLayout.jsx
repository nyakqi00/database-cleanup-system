import { NavLink } from "react-router-dom";
import { FaUpload, FaEnvelopeOpenText, FaTimesCircle } from "react-icons/fa";
import TopNavbar from "../components/TopNavbar";
import Particles from "../components/Particles";
import React from "react";

function DashboardLayout({ children }) {
    return (
        <div className="flex min-h-screen bg-gray-100 font-sans text-gray-800 relative overflow-hidden">
            {/* 🔴 Global Particle Background */}
            <div className="absolute inset-0 -z-10">
                <Particles
                    particleColors={["#f87171", "#ef4444", "#dc2626"]}
                    particleCount={200}
                    particleSpread={10}
                    speed={0.1}
                    particleBaseSize={80}
                    moveParticlesOnHover={true}
                    alphaParticles={true}
                    disableRotation={false}
                />
            </div>

            {/* Sidebar */}
            <aside className="w-64 bg-white border-r shadow-lg flex flex-col relative z-10">
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
            <div className="flex-1 flex flex-col relative z-10">
                <TopNavbar />

                {/* Transparent main so particles show behind */}
                <main className="flex-1 p-6 bg-transparent">{children}</main>
            </div>
        </div>
    );
}

export default DashboardLayout;
