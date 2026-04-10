import React from "react";
import ReactDOM from "react-dom/client";
import { MsalProvider } from "@azure/msal-react";

import { App } from "@/App";
import { initializeMsal, msalInstance } from "@/auth/client";
import { AuthGate } from "@/components/AuthGate";
import "@/index.css";


void initializeMsal().then(() => {
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <MsalProvider instance={msalInstance}>
        <AuthGate>
          <App />
        </AuthGate>
      </MsalProvider>
    </React.StrictMode>,
  );
});
