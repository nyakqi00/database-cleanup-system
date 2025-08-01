import React, { useEffect, useState } from "react";
import axios from "axios";
import { FaDatabase } from "react-icons/fa";
import { HiOutlineDocumentText } from "react-icons/hi";

function MasterEmailsPage() {
    const [emails, setEmails] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [total, setTotal] = useState(0);

    const [limit] = useState(100);
    const [offset, setOffset] = useState(0);

    const [search, setSearch] = useState("");
    const [brandFilter, setBrandFilter] = useState("");
    const [segmentFilter, setSegmentFilter] = useState("");

    const fetchEmails = async () => {
        setLoading(true);
        try {
            const res = await axios.get("http://localhost:8001/master-emails", {
                params: {
                    limit,
                    offset,
                    search: search || undefined,
                    brand: brandFilter || undefined,
                    segment: segmentFilter || undefined,
                },
            });
            setEmails(res.data.data);
            setTotal(res.data.total);
            setError(null);
        } catch (err) {
            setError("Failed to load master emails");
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchEmails();
    }, [offset]);

    const nextPage = () => {
        if (offset + limit < total) {
            setOffset(offset + limit);
        }
    };

    const prevPage = () => {
        if (offset > 0) {
            setOffset(offset - limit);
        }
    };

    return (
        <div className="px-4 py-6">
            <h2 className="text-3xl font-bold text-teal-700 mb-4 flex items-center gap-2">
                <HiOutlineDocumentText className="text-teal-700" /> Master Emails
            </h2>

            {/* Filters */}
            <div className="flex flex-wrap items-end gap-4 mb-4">
                <div>
                    <label className="block text-sm text-gray-600">Search Email</label>
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="example@email.com"
                        className="px-3 py-1.5 border rounded-md text-sm"
                    />
                </div>

                <div>
                    <label className="block text-sm text-gray-600">Brand</label>
                    <select
                        value={brandFilter}
                        onChange={(e) => setBrandFilter(e.target.value)}
                        className="px-3 py-1.5 border rounded-md text-sm"
                    >
                        <option value="">All</option>
                        <option value="TR">TR</option>
                        <option value="MFM">MFM</option>
                        <option value="NYSS">NYSS</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm text-gray-600">Segment</label>
                    <select
                        value={segmentFilter}
                        onChange={(e) => setSegmentFilter(e.target.value)}
                        className="px-3 py-1.5 border rounded-md text-sm"
                    >
                        <option value="">All</option>
                        <option value="Champions">Champions</option>
                        <option value="Loyal">Loyal</option>
                        <option value="Promising">Promising</option>
                        <option value="Need Attention">Need Attention</option>
                        <option value="Can't Lose Them">Can't Lose Them</option>
                        <option value="About To Sleep">About To Sleep</option>
                        <option value="Hibernating">Hibernating</option>
                    </select>
                </div>

                <button
                    onClick={() => {
                        setOffset(0);
                        fetchEmails();
                    }}
                    className="bg-teal-600 text-white px-4 py-1.5 rounded text-sm hover:bg-teal-700"
                >
                    Apply
                </button>

                <button
                    className="ml-auto text-sm border border-teal-600 text-teal-700 px-4 py-1.5 rounded hover:bg-teal-50"
                    onClick={() => alert("Export to CSV coming soon")}
                >
                    Export to CSV
                </button>
            </div>

            {/* Table */}
            {loading ? (
                <p className="text-gray-500">Loading...</p>
            ) : error ? (
                <p className="text-red-600 font-medium">{error}</p>
            ) : (
                <div className="overflow-auto border border-gray-200 rounded-xl shadow-sm">
                    <table className="min-w-full text-sm text-left text-gray-700">
                        <thead className="bg-teal-600 text-white text-xs uppercase">
                            <tr>
                                <th className="py-3 px-4">Email</th>
                                <th className="py-3 px-4">Card No</th>
                                <th className="py-3 px-4">Name</th>
                                <th className="py-3 px-4">Phone</th>
                                <th className="py-3 px-4">TR Segment</th>
                                <th className="py-3 px-4">MFM Segment</th>
                                <th className="py-3 px-4">NYSS Segment</th>
                                <th className="py-3 px-4">Brands</th>
                                <th className="py-3 px-4">Updated</th>
                            </tr>
                        </thead>
                        <tbody>
                            {emails.map((email, idx) => (
                                <tr key={idx} className="border-t hover:bg-teal-50">
                                    <td className="py-2 px-4 whitespace-nowrap">{email.email}</td>
                                    <td className="py-2 px-4 font-mono">{email.card_no?.toString()}</td>
                                    <td className="py-2 px-4">{email.name}</td>
                                    <td className="py-2 px-4 font-mono">{email.phone?.toString()}</td>
                                    <td className="py-2 px-4">{email.segment_tr}</td>
                                    <td className="py-2 px-4">{email.segment_mfm}</td>
                                    <td className="py-2 px-4">{email.segment_nyss}</td>
                                    <td className="py-2 px-4">
                                        {email.is_tr && <span className="inline-block bg-red-100 text-red-700 rounded px-2 mr-1">TR</span>}
                                        {email.is_mfm && <span className="inline-block bg-blue-100 text-blue-700 rounded px-2 mr-1">MFM</span>}
                                        {email.is_nyss && <span className="inline-block bg-green-100 text-green-700 rounded px-2">NYSS</span>}
                                    </td>
                                    <td className="py-2 px-4 text-gray-500">{email.last_updated}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Pagination */}
            <div className="flex justify-between items-center mt-6">
                <button
                    onClick={prevPage}
                    className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-sm rounded-md disabled:opacity-50"
                    disabled={offset === 0}
                >
                    ← Previous
                </button>
                <p className="text-sm text-gray-600">
                    Showing {offset + 1} - {Math.min(offset + limit, total)} of {total}
                </p>
                <button
                    onClick={nextPage}
                    className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-sm rounded-md disabled:opacity-50"
                    disabled={offset + limit >= total}
                >
                    Next →
                </button>
            </div>
        </div>
    );
}

export default MasterEmailsPage;
