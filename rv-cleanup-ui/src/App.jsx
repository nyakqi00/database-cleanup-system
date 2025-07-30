import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import InvalidEmails from "./pages/InvalidEmails";
import DashboardLayout from "./layouts/DashboardLayout";
import MasterEmailsPage from "./pages/MasterEmails";




function App() {
  return (
    <DashboardLayout>


      <Routes>
        <Route path="/" element={<Navigate to="/upload" />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/master" element={<MasterEmailsPage />} />
        <Route path="/invalid" element={<InvalidEmails />} />
      </Routes>
    </DashboardLayout>
  );
}

export default App;
