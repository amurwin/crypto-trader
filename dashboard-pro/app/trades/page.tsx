import { query } from '../../lib/apollo-client'
import { TRADES_QUERY, type Trade } from '../../lib/queries'
import { TradesView } from './TradesView'

export const dynamic = 'force-dynamic'

export default async function TradesPage() {
  const { data } = await query<{ trades: Trade[] }>({
    query: TRADES_QUERY,
    variables: { limit: 50 },
  })
  return <TradesView initial={data!.trades} />
}
