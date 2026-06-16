import type { CodegenConfig } from '@graphql-codegen/cli'

const config: CodegenConfig = {
  schema: './schema.graphql',
  documents: ['app/**/*.tsx', 'lib/**/*.ts', 'lib/**/*.tsx', '!app/**/*.d.ts'],
  generates: {
    './lib/gql/': {
      preset: 'client',
    },
  },
}

export default config
