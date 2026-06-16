import { HttpLink } from '@apollo/client'
import {
  ApolloClient,
  InMemoryCache,
  registerApolloClient,
} from '@apollo/client-integration-nextjs'
import { apiKey } from './api-key'

export const { getClient, query, PreloadQuery } = registerApolloClient(() => {
  return new ApolloClient({
    cache: new InMemoryCache(),
    link: new HttpLink({
      uri: process.env.GRAPHQL_URL ?? 'http://localhost:8000/graphql',
      headers: { 'X-API-Key': apiKey() },
      fetchOptions: { cache: 'no-store' },
    }),
  })
})
