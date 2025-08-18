import React, { useState, useEffect } from "react";
import axios from "axios";
import { FaFileUpload, FaEnvelope } from "react-icons/fa";
import SplitText from "../components/SplitText";
import Particles from "../components/Particles";

function InvalidEmailsPage() {
    const [invalidEmails, setInvalidEmails] = useState([]);
    const [csvFile, setCsvFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [brand, setBrand] = useState("Unknown");

    const fetchInvalidEmails = async () => {
        try {
            const res = await axios.get("http://localhost:8001/invalid-emails");
            setInvalidEmails(res.data.data);
        } catch (err) {
            console.error("Error fetching invalid emails", err);
        }
    };

    useEffect(() => {
        fetchInvalidEmails();
    }, []);

    const handleUpload = async () => {
        if (!csvFile) return;

        const formData = new FormData();
        formData.append("file", csvFile);
        formData.append("brand", brand);

        setUploading(true);
        try {
            await axios.post("http://localhost:8001/invalid-emails/upload", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            await fetchInvalidEmails();
            alert("Uploaded successfully!");
        } catch (err) {
            console.error("Upload failed", err);
            alert("Upload failed.");
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="relative w-full min-h-screen overflow-hidden bg-transparent">
            {/* Particle Background */}
            <div
                style={{
                    width: "100%",
                    height: "100%",
                    position: "absolute",
                    inset: 0,
                    zIndex: -1,
                }}
            >
                <Particles
                    particleColors={["#f87171", "#ef4444", "#dc2626"]}
                    particleCount={200}
                    particleSpread={10}
                    speed={0.1}
                    particleBaseSize={100}
                    moveParticlesOnHover={true}
                    alphaParticles={true}
                    disableRotation={false}
                />
            </div>

            {/* Page Content */}
            <div className="relative z-10 max-w-4xl mx-auto p-6 space-y-6 bg-white/80 backdrop-blur-md rounded-xl shadow-lg">
                <div className="flex items-center gap-2">
                    <FaEnvelope className="text-red-600" />
                    <SplitText text="Invalid Emails" delay={100} duration={0.6} />
                </div>

                {/* Upload Box */}
                <div className="bg-white shadow-md p-6 rounded-xl border border-gray-200 space-y-4">
                    <h2 className="text-lg font-semibold text-gray-700 flex items-center gap-2">
                        <FaFileUpload /> Upload CSV (1 column: `email`)
                    </h2>

                    <input
                        type="file"
                        accept=".csv"
                        onChange={(e) => setCsvFile(e.target.files[0])}
                        className="block w-full border rounded p-2 text-sm"
                    />
                    <input
                        type="text"
                        placeholder="Brand (optional)"
                        value={brand}
                        onChange={(e) => setBrand(e.target.value)}
                        className="block w-full border rounded p-2 text-sm"
                    />
                    <button
                        onClick={handleUpload}
                        disabled={uploading}
                        className="bg-red-600 text-white px-5 py-2 rounded hover:bg-red-700 text-sm"
                    >
                        {uploading ? "Uploading..." : "Upload CSV"}
                    </button>
                </div>

                {/* Display Existing Invalid Emails */}
                <div className="bg-white shadow-md p-6 rounded-xl border border-gray-200">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-lg font-semibold">Existing Invalid Emails</h2>
                        <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">
                            {invalidEmails.length} total
                        </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-64 overflow-y-auto text-sm">
                        {invalidEmails.map((item, index) => (
                            <div
                                key={index}
                                className="bg-gray-100 px-3 py-2 rounded-md text-gray-700"
                            >
                                {item.email}
                                {item.brand && (
                                    <span className="block text-xs text-gray-400 italic">
                                        {item.brand}
                                    </span>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default InvalidEmailsPage;
