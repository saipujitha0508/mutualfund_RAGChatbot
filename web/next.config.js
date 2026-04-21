/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://sai68-RAGfaq-chatbot-api.hf.space',
  },
  output: 'standalone',
}

module.exports = nextConfig
