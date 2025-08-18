import api from "../services/api";
import { useState, useRef } from "react";
import LoadingModal from "../components/LoadingModal";
import Particles from "../components/Particles";


function UploadPage() {
  const [brand, setBrand] = useState("");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [timeLeft, setTimeLeft] = useState(0);
  const [uploadComplete, setUploadComplete] = useState(false);
  const [uploadStats, setUploadStats] = useState(null);
  const fileInputRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file || !brand) {
      alert("Please select a brand and a file.");
      return;
    }

    const formData = new FormData();
    formData.append("brand", brand);
    formData.append("file", file);

    setUploading(true);
    setProgress(0);
    let estSeconds = 8;
    setTimeLeft(estSeconds);

    const timer = setInterval(() => {
      estSeconds -= 1;
      setTimeLeft(estSeconds);
      setProgress((prev) => Math.min(prev + 100 / 8, 100));
      if (estSeconds <= 0) clearInterval(timer);
    }, 1000);

    try {
      const response = await api.post("/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      console.log("Upload successful:", response.data);
      setUploadStats(response.data);
      setUploadComplete(true);
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Upload failed. Please check the console.");
    }

    clearInterval(timer);
    setUploading(false);
    setProgress(0);
    setTimeLeft(0);
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = null;
    }
  };

  return (
    <div className="min-h-screen relative flex flex-col items-center justify-center p-6">
      {/* 🔴 Particle background */}
      <div className="absolute inset-0 -z-10">
        <Particles
          particleColors={["#3b82f6", "#60a5fa", "#1e40af"]}
          particleCount={150}
          particleSpread={10}
          speed={0.15}
          particleBaseSize={80}
          moveParticlesOnHover={true}
          alphaParticles={true}
          disableRotation={false}
        />
      </div>

      {uploading && (
        <div className="absolute z-10 bg-black bg-opacity-30 inset-0 flex items-center justify-center">
          <LoadingModal timeLeft={timeLeft} progress={progress} />
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-lg space-y-6 border border-gray-200 relative z-0"
      >
        <h2 className="text-2xl font-bold text-gray-800 text-center flex items-center justify-center gap-2">
          📤 Upload Email CSV
        </h2>

        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Select Brand
          </label>
          <select
            value={brand}
            onChange={(e) => setBrand(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
            required
          >
            <option value="" disabled hidden>
              -- Choose a brand --
            </option>
            <option value="Tony Romas">Tony Roma’s</option>
            <option value="The Manhattan Fish Market">The Manhattan FISH MARKET</option>
            <option value="New York Steak Shack">NY Steak Shack</option>
          </select>
        </div>

        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Choose CSV File
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files[0])}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm file:bg-blue-50 file:text-blue-700 file:border-0 file:rounded file:px-4 file:py-1 hover:file:bg-blue-100"
            required
          />
          <p className="text-xs text-gray-500">
            Only <code>.csv</code> files are allowed.
          </p>
        </div>

        <button
          type="submit"
          disabled={uploading}
          className="w-full bg-blue-600 text-white font-medium py-2.5 px-4 rounded-lg shadow hover:bg-blue-700 transition duration-200 disabled:opacity-50"
        >
          Upload
        </button>
      </form>

      {uploadComplete && uploadStats && (
        <div className="mt-6 w-full max-w-lg bg-white border border-gray-200 shadow-lg rounded-xl p-6 text-sm text-gray-700 space-y-2 text-left">
          <h3 className="text-lg font-semibold text-green-700 mb-2">
            ✅ Upload Complete
          </h3>
          <ul className="space-y-1">
            <li><strong>Brand:</strong> {uploadStats.brand}</li>
            <li><strong>Total Rows Uploaded:</strong> {uploadStats.rows_uploaded}</li>
            <li><strong>Rows After Invalid Removal:</strong> {uploadStats.rows_after_invalid_removal}</li>
            <li><strong>Invalid Emails:</strong> {uploadStats.invalid_count}</li>
            <li><strong>Inserted to Brand Table:</strong> {uploadStats.inserted_to_brand}</li>
            <li><strong>Rows Updated in Master:</strong> {uploadStats.merge_result?.updated}</li>
            <li><strong>Rows Inserted in Master:</strong> {uploadStats.merge_result?.inserted}</li>
          </ul>
          <button
            onClick={() => {
              setUploadComplete(false);
              window.location.href = "/master-emails";
            }}
            className="mt-4 w-full bg-blue-600 text-white text-sm py-2 rounded-lg hover:bg-blue-700 transition"
          >
            View Full Results
          </button>
        </div>
      )}
    </div>
  );
}

export default UploadPage;
