import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import { Login } from "./pages/Login";
import { PatientForm } from "./pages/PatientForm";
import { PredictionDashboard } from "./pages/PredictionDashboard";
import { PatientTimeline } from "./pages/PatientTimeline";
import { AdminPanel } from "./pages/AdminPanel";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,
      retry: 1,
    },
  },
});

const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#1976d2" },
    error: { main: "#d32f2f" },
    warning: { main: "#f57c00" },
    success: { main: "#388e3c" },
  },
  typography: {
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/patients/new" element={<PatientForm />} />
            <Route path="/patients/:token" element={<PatientTimeline />} />
            <Route
              path="/patients/:token/predict"
              element={<PredictionDashboard />}
            />
            <Route path="/admin" element={<AdminPanel />} />
            <Route path="*" element={<Navigate to="/login" />} />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

if (document.getElementById("root")) {
  ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
