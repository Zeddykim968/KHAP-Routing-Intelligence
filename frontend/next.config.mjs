const API_URL = process.env.API_URL || "http://localhost:8000";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Django endpoints use trailing slashes; don't let the dev server strip them.
  skipTrailingSlashRedirect: true,
  // Allow the Freebuff preview origin to reach the dev server.
  allowedDevOrigins: [
    "https://pv-bc75b78a968d-81a37ebf-24a9-4525-83b3-6e89a716d62a.style.dev",
  ],
  async rewrites() {
    // Proxy /api/* to the Django backend so the browser stays same-origin.
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
};

export default nextConfig;
