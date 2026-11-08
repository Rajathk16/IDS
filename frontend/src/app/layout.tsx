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
              // Suppress noisy third-party browser extension collisions and stream errors
              (function() {
                if (typeof window === "undefined") return;

                // 1. Suppress unhandled promise rejections from extensions (MetaMask, inpage.js)
                window.addEventListener("unhandledrejection", function(event) {
                  var reason = event && event.reason;
                  var msg = (reason && reason.message) || String(reason || "");
                  if (
                    msg.indexOf("MetaMask") !== -1 ||
                    msg.indexOf("inpage.js") !== -1 ||
                    msg.indexOf("Receiving end does not exist") !== -1
                  ) {
                    event.preventDefault();
                    event.stopImmediatePropagation();
                  }
                }, true);

                // 2. Intercept and silence extension-injected console spam
                var originalWarn = console.warn;
                var originalError = console.error;
                var noisyPatterns = [
                  "MaxListenersExceededWarning",
                  "Resetting the streams",
                  "contentscript.js",
                  "Receiving end does not exist",
                  "MetaMask",
                  "inpage.js"
                ];

                function shouldFilter(args) {
                  for (var i = 0; i < args.length; i++) {
                    var str = typeof args[i] === "object" ? JSON.stringify(args[i]) : String(args[i]);
                    for (var j = 0; j < noisyPatterns.length; j++) {
                      if (str && str.indexOf(noisyPatterns[j]) !== -1) return true;
                    }
                  }
                  return false;
                }

                console.warn = function() {
                  if (shouldFilter(arguments)) return;
                  originalWarn.apply(console, arguments);
                };

                console.error = function() {
                  if (shouldFilter(arguments)) return;
                  originalError.apply(console, arguments);
                };
              })();
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
