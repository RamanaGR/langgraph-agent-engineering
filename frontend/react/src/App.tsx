import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { UploadPage } from "./pages/recruiter/UploadPage";
import { SearchChatPage } from "./pages/recruiter/SearchChatPage";
import { ApprovalsPage } from "./pages/recruiter/ApprovalsPage";
import { JobsPage } from "./pages/candidate/JobsPage";
import { ApplyPage } from "./pages/candidate/ApplyPage";
import { StatusPage } from "./pages/candidate/StatusPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/recruiter" replace />} />

      <Route path="/recruiter" element={<Layout mode="recruiter" />}>
        <Route index element={<Navigate to="search" replace />} />
        <Route path="upload" element={<UploadPage />} />
        <Route path="search" element={<SearchChatPage />} />
        <Route path="approvals" element={<ApprovalsPage />} />
      </Route>

      <Route path="/candidate" element={<Layout mode="candidate" />}>
        <Route index element={<Navigate to="jobs" replace />} />
        <Route path="jobs" element={<JobsPage />} />
        <Route path="apply/:jobId" element={<ApplyPage />} />
        <Route path="status" element={<StatusPage />} />
      </Route>
    </Routes>
  );
}
