import api from "./services/api";
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
    // You can store response.data here if you want to preview it
  } catch (error) {
    console.error("Upload failed:", error);
    alert("Upload failed. Please check the console.");
  }
  
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <form
        onSubmit={handleSubmit}
        className="bg-white p-6 rounded-xl shadow-md w-full max-w-md space-y-4"
      >
        <h2 className="text-xl font-semibold text-gray-800">
          Upload Email CSV
        </h2>

        <div>
          <label className="block mb-1 font-medium text-gray-700">
            Select Brand
          </label>
          <select
  value={brand}
  onChange={(e) => setBrand(e.target.value)}
  className="w-full border border-gray-300 rounded px-3 py-2"
  required
>
  <option value="">-- Choose a brand --</option>
  <option value="Tony Romas">Tony Roma’s</option>
  <option value="The Manhattan Fish Market">The Manhattan FISH MARKET</option>
  <option value="New York Steak Shack">NY Steak Shack</option>
</select>

        </div>

        <div>
          <label className="block mb-1 font-medium text-gray-700">
            Choose CSV File
          </label>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files[0])}
            className="w-full border border-gray-300 rounded px-3 py-2"
            required
          />
        </div>

        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition"
        >
          Upload
        </button>
      </form>
    </div>
  );
}

export default UploadPage;
