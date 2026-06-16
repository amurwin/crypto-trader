import { NextRequest, NextResponse } from 'next/server'
import { apiKey } from '../../../lib/api-key'

// Proxies browser GraphQL requests to the backend, attaching the API key
// server-side so it never ships to client JS.
export async function POST(req: NextRequest) {
  const body = await req.text()
  const upstream = await fetch(process.env.GRAPHQL_URL ?? 'http://localhost:8000/graphql', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey(),
    },
    body,
    cache: 'no-store',
  })
  const data = await upstream.text()
  return new NextResponse(data, {
    status: upstream.status,
    headers: { 'Content-Type': 'application/json' },
  })
}
