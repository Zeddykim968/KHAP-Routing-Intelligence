import "./globals.css";

export const metadata = {
  title: "KHAP — Find health facilities near you",
  description:
    "Search nearby health facilities in Kenya, see services and insurance accepted, and get live turn-by-turn directions.",
  applicationName: "KHAP",
  appleWebApp: { capable: true, statusBarStyle: "default", title: "KHAP" },
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

const themeInit = `try {
  var t = localStorage.getItem('khap-theme');
  if (!t) t = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  document.documentElement.dataset.theme = t;
} catch (e) {}`;

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
        <meta
          name="theme-color"
          media="(prefers-color-scheme: light)"
          content="#ffffff"
        />
        <meta
          name="theme-color"
          media="(prefers-color-scheme: dark)"
          content="#1f1f1f"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
