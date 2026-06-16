import { query } from '../../lib/apollo-client'
import { OHLCV_QUERY, ASSETS_QUERY, type OhlcvBar, type Asset } from '../../lib/queries'
import { ChartView } from './ChartView'

export const dynamic = 'force-dynamic'

export default async function ChartPage() {
  const { data: assetsData } = await query<{ assets: Asset[] }>({ query: ASSETS_QUERY })
  const assets = assetsData!.assets
  const defaultAsset = assets[0]?.symbol ?? ''

  const { data } = await query<{ ohlcv: OhlcvBar[] }>({
    query: OHLCV_QUERY,
    variables: { asset: defaultAsset, limit: 288 },
  })
  return <ChartView initial={data!.ohlcv} initialAsset={defaultAsset} initialAssets={assets} />
}
