import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DEVRAKSHAK | IDS Console",
  description: "Offline evaluation console for network intrusion and DDoS detection on CICIoT2023.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" style={{ overflowX: "clip" }}>
      <body>{children}</body>
    </html>
  );
}
