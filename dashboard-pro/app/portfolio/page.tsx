import { query } from '../../lib/apollo-client'
import { PORTFOLIO_QUERY, type Portfolio } from '../../lib/queries'
import { PortfolioView } from './PortfolioView'

export const dynamic = 'force-dynamic'

export default async function PortfolioPage() {
  const { data } = await query<{ portfolio: Portfolio }>({ query: PORTFOLIO_QUERY })
  return <PortfolioView initial={data!.portfolio} />
}
