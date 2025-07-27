import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import MasterEmails from "./pages/MasterEmails";
import InvalidEmails from "./pages/InvalidEmails";
import DashboardLayout from "./layouts/DashboardLayout";




function App() {
  return (
    <DashboardLayout>


      <Routes>
        <Route path="/" element={<Navigate to="/upload" />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/master" element={<MasterEmails />} />
        <Route path="/invalid" element={<InvalidEmails />} />
      </Routes>
    </DashboardLayout>
  );
}

export default App;
