/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    // ESLint runs in CI via next lint; skip the duplicate check inside next build
    // to avoid interactive prompts on Vercel when no eslintrc was detected.
    ignoreDuringBuilds: false,
  },
};

module.exports = nextConfig;

