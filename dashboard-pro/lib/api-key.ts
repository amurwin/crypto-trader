import { readFileSync, existsSync } from 'fs'
import { join } from 'path'

// Mirrors api/auth.py's load_api_key(): systemd credential first, env var fallback.
export function apiKey(): string {
  const credsDir = process.env.CREDENTIALS_DIRECTORY
  if (credsDir) {
    const path = join(credsDir, 'api_key')
    if (existsSync(path)) {
      return readFileSync(path, 'utf-8').trim()
    }
  }
  const key = process.env.API_KEY
  if (!key) {
    throw new Error('API_KEY is not set — see dashboard-pro/.env.local.example')
  }
  return key
}
