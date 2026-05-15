import { Route, Routes } from "react-router-dom";

import { AppShell } from "@/components/layout/app-shell";
import { RedirectToHome } from "@/components/route-redirect";
import { AssistantPage } from "@/pages/assistant-page";
import { DashboardPage } from "@/pages/dashboard-page";
import { WorkflowSimulatorPage } from "@/pages/workflow-simulator-page";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/assistant" element={<AssistantPage />} />
        <Route path="/workflow" element={<WorkflowSimulatorPage />} />
        <Route path="/" element={<DashboardPage />} />
        <Route path=":slug" element={<RedirectToHome />} />
      </Route>
    </Routes>
  );
}
