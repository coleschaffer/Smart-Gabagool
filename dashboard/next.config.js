/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Render deployment
  output: process.env.NODE_ENV === 'production' ? 'standalone' : undefined,

  // Rewrites only for local development (proxying to local backend)
  // In production, frontend calls backend directly via NEXT_PUBLIC_API_URL
  async rewrites() {
    // Skip rewrites in production - frontend calls API directly
    if (process.env.NODE_ENV === 'production') {
      return [];
    }

    // Local development: proxy to local backend
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },

  // Allow external images if needed
  images: {
    domains: [],
  },
};

module.exports = nextConfig;
