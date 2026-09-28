import type { KianaApi } from '../data/types'

declare global {
  interface Window { kiana?: KianaApi }
}

export {}
