import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useEffect } from "react";
import Landing from "./app/landing";
import Practice from "./app/practice";
// import Result from "app/result"; // wire this in once result.tsx has content

export default function App() {
  useEffect(() => {
    // default theme on first load, before Landing/Practice mount
    if (!document.documentElement.getAttribute("data-theme")) {
      document.documentElement.setAttribute("data-theme", "dark");
    }
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/practice" element={<Practice />} />
        {/* <Route path="/result" element={<Result />} /> */}
      </Routes>
    </BrowserRouter>
  );
}