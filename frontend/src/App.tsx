import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { MailAccountsPage } from "./pages/MailAccountsPage";
import { RegisterPage } from "./pages/RegisterPage";
import { StatisticsPage } from "./pages/StatisticsPage";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout>
              <DashboardPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/statistics"
        element={
          <ProtectedRoute>
            <AppLayout>
              <StatisticsPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/mailboxes"
        element={
          <ProtectedRoute>
            <AppLayout>
              <MailAccountsPage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
