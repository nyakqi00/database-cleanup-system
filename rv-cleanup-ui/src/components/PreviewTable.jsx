function PreviewTable({ data }) {
    const headers = Object.keys(data[0] || {});

    return (
        <div className="overflow-x-auto">
            <table className="min-w-full border border-gray-200 divide-y divide-gray-200 text-sm text-left">
                <thead className="bg-gray-100 text-gray-700 uppercase text-xs tracking-wider">
                    <tr>
                        {headers.map((header) => (
                            <th key={header} className="px-4 py-3 whitespace-nowrap">
                                {header.replace(/_/g, " ")}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-100">
                    {data.slice(0, 10).map((row, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                            {headers.map((key) => (
                                <td key={key} className="px-4 py-2 whitespace-nowrap text-gray-800">
                                    {row[key] === null || row[key] === undefined ? "-" : row[key]}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default PreviewTable;
