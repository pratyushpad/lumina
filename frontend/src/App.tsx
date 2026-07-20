import { Route, Routes } from "react-router-dom";
import { CommandPalette } from "@/components/ui/CommandPalette";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { Toaster } from "@/components/ui/Toaster";
import AppPage from "./pages/AppPage";
import AuthCallbackPage from "./pages/AuthCallbackPage";
import LandingPage from "./pages/LandingPage";
import NotFoundPage from "./pages/NotFoundPage";

export default function App() {
  return (
    <ErrorBoundary>
      <CommandPalette />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/app" element={<AppPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
        {/* vercel.json rewrites every path to index.html, so unknown URLs reach
            the router rather than a server 404 — they need a page here. */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      <Toaster />
    </ErrorBoundary>
  );
}
