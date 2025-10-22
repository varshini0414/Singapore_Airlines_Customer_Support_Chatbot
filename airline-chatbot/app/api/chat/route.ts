import { type NextRequest, NextResponse } from "next/server"

const SYSTEM_TEMPLATE = `You are a customer-support assistant for Singapore Airlines.
Your tone should be human-like with empathy, not robotic.

Purpose:
- Understand any customer message about flights, bookings, cancellations, check-in, baggage, or refunds.
- Respond naturally, politely, and concisely.
- Stay strictly on airline topics. 
- If the message is unrelated to air travel, reply: "I can only help with airline-related questions such as flight status, bookings, or baggage."
- Do not engage in off-topic chat, math, jokes, or personal questions.

Behavior and policy:
1. Be factual and professional. 
2. Never invent or assume data not confirmed by the system or database.
3. If required data (flight number, date, booking reference) is missing, ask for it instead of guessing.
4. Do not confirm a refund, booking, or payment unless an API or database result explicitly confirms it.
5. Never output full credit-card numbers, phone numbers, or email addresses.
6. Be brief (1–3 sentences) and in a helpful airline-agent tone.

Context handling:
- Use any context provided in the "Context:" section to keep the conversation coherent.
- If the context is empty or irrelevant, continue normally.

Output format:
Return only a plain, natural sentence to the customer—no code or JSON.`

async function callNebius(messages: any[]) {
  const apiKey = process.env.NEBIUS_API_KEY
  const model = process.env.NEBIUS_MODEL || "meta-llama/Llama-3.3-70B-Instruct-LoRa:singapore-airline-support-bSbK"
  const url = "https://api.studio.nebius.com/v1/chat/completions"

  if (!apiKey) {
    throw new Error("NEBIUS_API_KEY not configured")
  }

  const response = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model,
      messages,
      temperature: 0.2,
      top_p: 0.95,
      stream: false,
    }),
  })

  if (!response.ok) {
    throw new Error(`LLM API error: ${response.statusText}`)
  }

  const data = await response.json()
  return data.choices[0].message.content.trim()
}

export async function POST(request: NextRequest) {
  try {
    const { message, mode, bookingInfo } = await request.json()

    if (!message || !message.trim()) {
      return NextResponse.json({ error: "Message is required" }, { status: 400 })
    }

    const messages: any[] = [{ role: "system", content: SYSTEM_TEMPLATE }]

    // Add booking context if in specific mode
    if (mode === "specific" && bookingInfo) {
      const context = `Context: Booking ID ${bookingInfo.id}; Passenger ${bookingInfo.passenger}; Flight ${bookingInfo.flight}; Seat ${bookingInfo.seat}; Class ${bookingInfo.class}; From ${bookingInfo.from} to ${bookingInfo.to}; Departure ${bookingInfo.departure}; Arrival ${bookingInfo.arrival}; Status ${bookingInfo.status}; Baggage ${bookingInfo.baggage}.`
      messages.push({ role: "system", content: context })
    }

    messages.push({ role: "user", content: message.trim() })

    const reply = await callNebius(messages)

    return NextResponse.json({ reply })
  } catch (error) {
    console.error("Chat error:", error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed to process request" },
      { status: 500 },
    )
  }
}
