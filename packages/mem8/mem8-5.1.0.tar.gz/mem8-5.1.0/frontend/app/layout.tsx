import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/lib/providers";
import { AuthGuard } from "@/components/AuthGuard";
import { getAppName, getVersion } from "@/lib/version";

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["100", "200", "300", "400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: `${getAppName()} | Terminal IDE for Thoughts & Knowledge`,
  description: "A terminal-style IDE for managing thoughts, research, and plans with YAML frontmatter",
  icons: {
    icon: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${jetbrainsMono.variable} bg-grid bg-scanlines`}
      >
        <Providers>
          <AuthGuard>
            <div className="min-h-screen flex flex-col">
              {children}
            </div>
          </AuthGuard>
        </Providers>
      </body>
    </html>
  );
}
