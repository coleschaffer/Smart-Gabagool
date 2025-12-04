/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Render deployment
  output: process.env.NODE_ENV === 'production' ? 'standalone' : undefined,

  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
      {
        source: '/ws',
        destination: `${apiUrl.replace('http', 'ws')}/ws`,
      },
    ];
  },

  // Allow external images if needed
  images: {
    domains: [],
  },
};

module.exports = nextConfig;
