import { BrowserRouter, Routes, Route } from "react-router-dom";

import Sidebar from "./components/Sidebar";
import Header from "./components/Header";

import Dashboard from "./pages/Dashboard";
import BOMExplorer from "./pages/BOMExplorer";
import Anomalies from "./pages/Anomalies";
import Reconciliation from "./pages/Reconciliation";
import ImpactAnalysis from "./pages/ImpactAnalysis";
import Copilot from "./pages/Copilot";
import Lineage from "./pages/Lineage";

import "./App.css";


function App() {

  return (
    <BrowserRouter>

      <div className="app">

        <Sidebar />

        <div className="main">

          <Header />

          <Routes>

            <Route
              path="/"
              element={<Dashboard />}
            />

            <Route
              path="/bom"
              element={<BOMExplorer />}
            />

            <Route
              path="/anomalies"
              element={<Anomalies />}
            />

            <Route
              path="/reconciliation"
              element={<Reconciliation />}
            />

            <Route
              path="/impact"
              element={<ImpactAnalysis />}
            />

            <Route
              path="/lineage"
              element={<Lineage />}
            />

            <Route
              path="/copilot"
              element={<Copilot />}
            />

          </Routes>

        </div>

      </div>

    </BrowserRouter>
  );
}

export default App;