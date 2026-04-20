'use client'

import { useState } from 'react'
import { MessageCircle, Send, AlertCircle, RefreshCw } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

const EXAMPLE_QUESTIONS = [
  "What is the expense ratio of Navi Midcap 150 fund?",
  "What is the minimum SIP amount for Navi Flexi Cap fund?",
  "What is the exit load for Navi Large & Mid Cap fund?"
]

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [threadId, setThreadId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const createThread = async () => {
    try {
      const response = await fetch(`${API_URL}/threads`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      const data = await response.json()
      setThreadId(data.thread_id)
      return data.thread_id
    } catch (err) {
      console.error('Failed to create thread:', err)
      setError('Failed to initialize chat session')
      return null
    }
  }

  const sendMessage = async (content: string) => {
    if (!content.trim()) return

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setError(null)

    // Create thread if needed
    let currentThreadId = threadId
    if (!currentThreadId) {
      currentThreadId = await createThread()
      if (!currentThreadId) return
    }

    setIsLoading(true)

    try {
      const response = await fetch(`${API_URL}/threads/${currentThreadId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const data = await response.json()

      // Add assistant message
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      console.error('Failed to send message:', err)
      setError('Failed to get response. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleExampleQuestion = (question: string) => {
    sendMessage(question)
  }

  const handleNewChat = () => {
    setMessages([])
    setThreadId(null)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-950/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <MessageCircle className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-white">Navi Mutual Fund FAQ</h1>
              <p className="text-sm text-gray-400">Facts-only assistant</p>
            </div>
          </div>
          <button
            onClick={handleNewChat}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            New Chat
          </button>
        </div>
      </header>

      {/* Disclaimer Banner */}
      <div className="bg-amber-900/20 border-b border-amber-800/30">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0" />
          <p className="text-sm text-amber-200">
            <strong>Disclaimer:</strong> This assistant provides factual information only. No investment advice or recommendations.
          </p>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Welcome Message */}
        {messages.length === 0 && (
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-white mb-3">
              Welcome to FAQ Chatbot
            </h2>
            <p className="text-gray-400 mb-8">
              Ask factual questions about Navi Mutual Fund schemes. I can help with expense ratios, SIP amounts, exit loads, and more.
            </p>

            {/* Example Questions */}
            <div className="space-y-3">
              <p className="text-sm text-gray-500 mb-3">Try asking:</p>
              {EXAMPLE_QUESTIONS.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleExampleQuestion(question)}
                  className="block w-full max-w-2xl mx-auto px-4 py-3 text-left bg-gray-800/50 hover:bg-gray-800 border border-gray-700 hover:border-gray-600 rounded-lg transition-all text-gray-300 hover:text-white"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="space-y-4 mb-8">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-100 border border-gray-700'
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-800 border border-gray-700 rounded-2xl px-4 py-3">
                <div className="flex gap-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-4 bg-red-900/20 border border-red-800/50 rounded-lg flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <p className="text-sm text-red-200">{error}</p>
          </div>
        )}

        {/* Input Area */}
        <div className="fixed bottom-0 left-0 right-0 bg-gray-950/95 backdrop-blur-sm border-t border-gray-800">
          <div className="max-w-4xl mx-auto px-4 py-4">
            <div className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage(input)}
                placeholder="Ask a question about Navi Mutual Fund schemes..."
                className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                disabled={isLoading}
              />
              <button
                onClick={() => sendMessage(input)}
                disabled={isLoading || !input.trim()}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center gap-2"
              >
                <Send className="w-5 h-5" />
                Send
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
