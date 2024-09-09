import React from "react";
import ReactDOM from "react-dom/client";
import {BrowserRouter, Route, Routes} from "react-router-dom";
import App from "./App";

const root = ReactDOM.createRoot(document.getElementById("root"));

// Allow injecting prefix path at runtime
// but default to empty prefix
const runtimePrefixPath = "%%RUNTIME_PREFIX_PATH%%";
const prefixPath = runtimePrefixPath.includes("RUNTIME_PREFIX_PATH") ? "" : runtimePrefixPath.substring(1);

root.render(
  <React.StrictMode>
    <BrowserRouter basename={prefixPath}>
      <Routes>
	<Route path='/' element={<App />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
