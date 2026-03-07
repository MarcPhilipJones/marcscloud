import { BrowserRouter, Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import Home from "./pages/Home";
import CaseList from "./pages/CaseList";

export default function App() {
  return (
    <BrowserRouter>
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/cases" element={<CaseList />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
