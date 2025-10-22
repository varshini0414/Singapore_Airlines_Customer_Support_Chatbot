import { type NextRequest, NextResponse } from "next/server"
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3"
import Database from "better-sqlite3"

const s3Client = new S3Client({
  region: "us-east-1",
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID || "",
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || "",
  },
})

const S3_BUCKET = "dtfs-system"
const S3_KEY = "santhoshtk/singapore_airlines_bookings.db"

async function queryDatabase(query: string, params: any[] = []) {
  try {
    console.log("[v0] Starting S3 download from:", `s3://${S3_BUCKET}/${S3_KEY}`)

    if (!process.env.AWS_ACCESS_KEY_ID || !process.env.AWS_SECRET_ACCESS_KEY) {
      throw new Error(
        "AWS credentials not configured. Please add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to environment variables in the Vars section.",
      )
    }

    // Download database from S3
    const command = new GetObjectCommand({
      Bucket: S3_BUCKET,
      Key: S3_KEY,
    })

    const response = await s3Client.send(command)
    const buffer = await response.Body?.transformToByteArray()

    console.log("[v0] Downloaded database, size:", buffer?.length, "bytes")

    if (!buffer) {
      throw new Error("Failed to download database from S3")
    }

    // Create in-memory database from buffer
    const db = new Database(Buffer.from(buffer))
    const stmt = db.prepare(query)
    const result = stmt.all(...params)
    db.close()

    console.log("[v0] Query successful, rows returned:", result.length)
    return result
  } catch (error) {
    console.error("[v0] Database query error:", error)
    throw error
  }
}

export async function POST(request: NextRequest) {
  try {
    const { bookingId } = await request.json()

    if (!bookingId || !/^[A-Z0-9]{6}$/.test(bookingId)) {
      return NextResponse.json({ error: "Invalid booking reference format" }, { status: 400 })
    }

    const rows = await queryDatabase("SELECT * FROM bookings WHERE id = ?", [bookingId])

    if (!rows || rows.length === 0) {
      return NextResponse.json({ error: "No booking found for this reference" }, { status: 404 })
    }

    const row = rows[0] as any

    return NextResponse.json({
      id: row.id,
      passenger: row.passenger_name,
      flight: row.flight_number,
      seat: row.seat_number,
      class: row.cabin_class,
      from: row.departure_airport,
      to: row.arrival_airport,
      departure: row.departure_time,
      arrival: row.arrival_time,
      status: row.booking_status,
      baggage: row.baggage_allowance,
    })
  } catch (error) {
    console.error("[v0] Booking API error:", error)
    const errorMessage = error instanceof Error ? error.message : "Database error"
    return NextResponse.json({ error: errorMessage }, { status: 500 })
  }
}
