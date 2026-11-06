import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DEVRAKSHAK // AI Network Intrusion & DDoS Defense System",
  description: "AI-Based Network Intrusion and DDoS Detection Platform (CICIoT2023, offline)",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" style={{ overflowX: "clip" }}>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // Suppress browser extension collisions
              if (typeof window !== "undefined") {
                window.addEventListener("unhandledrejection", function(event) {
                  var reason = event && event.reason;
                  var msg = (reason && reason.message) || String(reason || "");
                  if (msg.indexOf("MetaMask") !== -1 || msg.indexOf("inpage.js") !== -1) {
                    event.preventDefault();
                    event.stopImmediatePropagation();
                  }
                }, true);
              }
            `,
          }}
        />
      </head>
      <body className="bg-base-bg text-content-primary min-h-screen antialiased overflow-x-clip">
        {children}
      </body>
    </html>
  );
}
