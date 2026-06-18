'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

export function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  const pathname = usePathname()
  const active = pathname === href
  return (
    <Link
      href={href}
      className={`px-4 py-1.5 rounded-lg text-sm transition-colors ${
        active
          ? 'bg-slate-700 text-white'
          : 'text-slate-400 hover:text-white hover:bg-slate-800'
      }`}
    >
      {children}
    </Link>
  )
}
