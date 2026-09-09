import type { NextConfig } from "next";
const nextConfig: NextConfig = { reactStrictMode: true, productionBrowserSourceMaps: false, images: { formats: ["image/avif", "image/webp"] } };
export default nextConfig;
