import { Route, Routes } from "react-router-dom";
import { CommandPalette } from "@/components/ui/CommandPalette";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { Toaster } from "@/components/ui/Toaster";
import AppPage from "./pages/AppPage";
import LandingPage from "./pages/LandingPage";

export default function App() {
  return (
    <ErrorBoundary>
      <CommandPalette />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/app" element={<AppPage />} />
      </Routes>
      <Toaster />
    </ErrorBoundary>
  );
}
