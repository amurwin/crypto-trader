'use client'

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="bg-slate-800 rounded-xl p-6 text-center space-y-3">
      <div className="text-red-400 text-sm">Failed to load chart: {error.message}</div>
      <button
        onClick={reset}
        className="px-4 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-sm text-white"
      >
        Retry
      </button>
    </div>
  )
}
