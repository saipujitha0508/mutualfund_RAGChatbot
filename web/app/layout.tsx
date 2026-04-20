import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Navi Mutual Fund FAQ Assistant',
  description: 'Facts-only RAG-based FAQ assistant for Navi Mutual Fund schemes',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-gray-950 text-gray-100">
        {children}
      </body>
    </html>
  )
}
