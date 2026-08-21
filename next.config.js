/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  reactCompiler: true,
  output: 'export',
  images: {
    unoptimized: true
  }
};

module.exports = nextConfig;
