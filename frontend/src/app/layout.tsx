import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgriClutch — AI Agricultural Market Intelligence & Optimal Selling Platform",
  description:
    "Decision-support intelligence engine solving optimal selling, price forecasting, buyer matching, and storage perishability for farmers and FPOs. SIH26132.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-zinc-950 text-zinc-100 antialiased selection:bg-emerald-500/30 selection:text-emerald-200">
        {children}
      </body>
    </html>
  );
}
