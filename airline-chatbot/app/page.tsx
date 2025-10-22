"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"

interface Message {
  role: "user" | "assistant"
  content: string
}

interface BookingInfo {
  id: string
  passenger: string
  flight: string
  seat: string
  class: string
  from: string
  to: string
  departure: string
  arrival: string
  status: string
  baggage: string
}

export default function ChatbotPage() {
  const [mode, setMode] = useState<"general" | "specific">("general")
  const [bookingId, setBookingId] = useState("")
  const [bookingInfo, setBookingInfo] = useState<BookingInfo | null>(null)
  const [loadingBooking, setLoadingBooking] = useState(false)
  const [bookingError, setBookingError] = useState("")
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleBookingLookup = async () => {
    if (!bookingId.trim()) return

    setLoadingBooking(true)
    setBookingError("")
    setBookingInfo(null)

    try {
      const response = await fetch("/api/booking", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bookingId: bookingId.toUpperCase() }),
      })

      const data = await response.json()

      if (!response.ok) {
        setBookingError(data.error || "Booking not found")
      } else {
        setBookingInfo(data)
      }
    } catch (error) {
      setBookingError("Failed to fetch booking information")
    } finally {
      setLoadingBooking(false)
    }
  }

  const handleSendMessage = async () => {
    if (!input.trim()) return

    const userMessage = input.trim()
    setInput("")
    setMessages((prev) => [...prev, { role: "user", content: userMessage }])
    setLoading(true)

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage,
          mode,
          bookingInfo,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "Error: " + (data.error || "Failed to get response") },
        ])
      } else {
        setMessages((prev) => [...prev, { role: "assistant", content: data.reply }])
      }
    } catch (error) {
      setMessages((prev) => [...prev, { role: "assistant", content: "Error: Failed to connect to the assistant" }])
    } finally {
      setLoading(false)
    }
  }

  const canChat = mode === "general" || (mode === "specific" && bookingInfo)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg text-white font-bold text-lg">
            ✈️
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Singapore Airlines</h1>
            <p className="text-sm text-slate-400">Customer Support Assistant</p>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Mode Selection */}
        <div className="mb-8">
          <div className="flex gap-3 mb-6">
            <Button
              onClick={() => {
                setMode("general")
                setBookingInfo(null)
                setMessages([])
              }}
              variant={mode === "general" ? "default" : "outline"}
              className={mode === "general" ? "bg-blue-600 hover:bg-blue-700" : ""}
            >
              General Inquiry
            </Button>
            <Button
              onClick={() => {
                setMode("specific")
                setMessages([])
              }}
              variant={mode === "specific" ? "default" : "outline"}
              className={mode === "specific" ? "bg-blue-600 hover:bg-blue-700" : ""}
            >
              Booking Lookup
            </Button>
          </div>

          {/* Booking Lookup Section */}
          {mode === "specific" && (
            <Card className="p-6 bg-slate-800 border-slate-700 mb-6">
              <label className="block text-sm font-medium text-slate-200 mb-3">
                Enter your 6-digit booking reference
              </label>
              <div className="flex gap-2">
                <Input
                  placeholder="e.g., A1B2C3"
                  value={bookingId}
                  onChange={(e) => {
                    setBookingId(e.target.value.toUpperCase())
                    setBookingError("")
                  }}
                  maxLength={6}
                  className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                  disabled={loadingBooking}
                />
                <Button
                  onClick={handleBookingLookup}
                  disabled={loadingBooking || bookingId.length !== 6}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {loadingBooking ? "..." : "Lookup"}
                </Button>
              </div>

              {bookingError && (
                <div className="mt-4 p-3 bg-red-900/20 border border-red-700 rounded-lg flex gap-2 text-red-300 text-sm">
                  ⚠️ {bookingError}
                </div>
              )}

              {bookingInfo && (
                <div className="mt-4 p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                  <div className="flex items-start gap-2 mb-3">
                    <span className="text-green-400 text-lg">✓</span>
                    <div>
                      <p className="font-semibold text-white">Booking Found</p>
                      <p className="text-sm text-slate-400">Ready to assist with your booking</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-slate-400">Passenger</p>
                      <p className="text-white font-medium">{bookingInfo.passenger}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Flight</p>
                      <p className="text-white font-medium">{bookingInfo.flight}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Route</p>
                      <p className="text-white font-medium">
                        {bookingInfo.from} → {bookingInfo.to}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-400">Status</p>
                      <p className="text-white font-medium">{bookingInfo.status}</p>
                    </div>
                  </div>
                </div>
              )}
            </Card>
          )}
        </div>

        {/* Chat Area */}
        <Card className="bg-slate-800 border-slate-700 flex flex-col h-[600px]">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && (
              <div className="h-full flex items-center justify-center text-center">
                <div>
                  <div className="text-5xl mb-3">✈️</div>
                  <p className="text-slate-400">
                    {mode === "general"
                      ? "Ask me anything about Singapore Airlines flights, bookings, or policies"
                      : bookingInfo
                        ? "Your booking is loaded. Ask me anything about your flight"
                        : "Enter your booking reference to get started"}
                  </p>
                </div>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white rounded-br-none"
                      : "bg-slate-700 text-slate-100 rounded-bl-none"
                  }`}
                >
                  <p className="text-sm leading-relaxed">{msg.content}</p>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-700 text-slate-100 px-4 py-3 rounded-lg rounded-bl-none">
                  <div className="flex gap-2 items-center">
                    <span className="animate-spin">⏳</span>
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-slate-700 p-4">
            {!canChat && (
              <p className="text-sm text-slate-400 mb-3 text-center">
                {mode === "specific" && !bookingInfo ? "Please enter a valid booking reference to start chatting" : ""}
              </p>
            )}
            <div className="flex gap-2">
              <Input
                placeholder="Type your message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault()
                    handleSendMessage()
                  }
                }}
                disabled={!canChat || loading}
                className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
              />
              <Button
                onClick={handleSendMessage}
                disabled={!canChat || loading || !input.trim()}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {loading ? "..." : "→"}
              </Button>
            </div>
          </div>
        </Card>
      </main>
    </div>
  )
}
