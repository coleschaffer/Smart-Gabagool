import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Gabagool - Volatility Arbitrage Dashboard",
  description: "Real-time dashboard for Gabagool volatility arbitrage trading bot",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
