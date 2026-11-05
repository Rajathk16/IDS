import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DEVRAKSHAK // AI Intrusion & DDoS Defense System",
  description: "DEVRAKSHAK: AI-Based Intrusion and DDoS Detection System for IoT Networks (CICIoT2023)",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // Suppress third-party browser extension errors (e.g. MetaMask inpage.js) from triggering Next.js dev overlay
              if (typeof window !== "undefined") {
                window.addEventListener("unhandledrejection", function(event) {
                  var reason = event && event.reason;
                  var msg = (reason && reason.message) || String(reason || "");
                  var stack = (reason && reason.stack) || "";
                  if (
                    msg.indexOf("MetaMask") !== -1 ||
                    msg.indexOf("inpage.js") !== -1 ||
                    stack.indexOf("chrome-extension") !== -1 ||
                    stack.indexOf("inpage.js") !== -1
                  ) {
                    event.preventDefault();
                    event.stopImmediatePropagation();
                  }
                }, true);

                window.addEventListener("error", function(event) {
                  var msg = (event && event.message) || "";
                  var filename = (event && event.filename) || "";
                  if (
                    msg.indexOf("MetaMask") !== -1 ||
                    filename.indexOf("chrome-extension") !== -1 ||
                    filename.indexOf("inpage.js") !== -1
                  ) {
                    event.preventDefault();
                    event.stopImmediatePropagation();
                  }
                }, true);
              }
            `,
          }}
        />
      </head>
      <body className="bg-[#0b0f19] text-slate-100 min-h-screen antialiased overflow-x-hidden">
        {children}
      </body>
    </html>
  );
}
