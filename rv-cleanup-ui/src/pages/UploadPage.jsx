import api from "../services/api";
import { useState } from "react";

function UploadPage() {
  const [brand, setBrand] = useState("");
  const [file, setFile] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file || !brand) {
      alert("Please select a brand and a file.");
      return;
    }

    const formData = new FormData();
    formData.append("brand", brand);
    formData.append("file", file);

    try {
      const response = await api.post("/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      console.log("Upload successful:", response.data);
      alert("Upload successful!");
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Upload failed. Please check the console.");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center p-6">
      <form
        onSubmit={handleSubmit}
        className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-lg space-y-6 border border-gray-200"
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
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files[0])}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 text-sm file:bg-blue-50 file:text-blue-700 file:border-0 file:rounded file:px-4 file:py-1 hover:file:bg-blue-100"
            required
          />
          <p className="text-xs text-gray-500">Only <code>.csv</code> files are allowed.</p>
        </div>

        <button
          type="submit"
          className="w-full bg-blue-600 text-white font-medium py-2.5 px-4 rounded-lg shadow hover:bg-blue-700 transition duration-200"
        >
          Upload
        </button>
      </form>
    </div>
  );
}

export default UploadPage;
