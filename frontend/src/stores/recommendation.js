import { defineStore } from 'pinia'
import { confirmExposure, getHomeFeed, refreshRecommendations } from '../api/recommendation'
import { useUserStore } from './user'

const PAGE_SIZE = 20

export const useRecommendationStore = defineStore('recommendation', {
  state: () => ({
    items: [],
    displayedItemIds: new Set(),
    requestId: '',
    modelVersion: '',
    cursor: 0,
    candidateSize: 0,
    hasMore: true,
    loading: false,
    refreshing: false
  }),
  actions: {
    reset () {
      this.items = []
      this.displayedItemIds = new Set()
      this.requestId = ''
      this.modelVersion = ''
      this.cursor = 0
      this.candidateSize = 0
      this.hasMore = true
    },
    async refresh (triggerType = 'manual') {
      if (this.refreshing) return
      this.refreshing = true
      try {
        const user = useUserStore()
        const r = await refreshRecommendations({
          userId: user.userId,
          scene: 'home',
          triggerType,
          excludeItemIds: Array.from(this.displayedItemIds)
        })
        if (r.code !== 0) throw new Error(r.message || 'refresh_failed')
        this.requestId = r.requestId
        this.modelVersion = r.data.modelVersion
        this.candidateSize = r.data.candidateSize
        const incoming = r.data.items || []
        this.items = incoming
        this.cursor = incoming.length
        // Keep tail of recent exposures only, so the excludeItemIds payload stays small.
        const recent = Array.from(this.displayedItemIds).slice(-1500)
        this.displayedItemIds = new Set([...recent, ...incoming.map((it) => it.itemId)])
        this.hasMore = this.cursor < this.candidateSize
      } finally {
        this.refreshing = false
      }
    },
    async loadNextPage () {
      if (this.loading || !this.hasMore) return
      this.loading = true
      try {
        const user = useUserStore()
        const r = await getHomeFeed({ userId: user.userId, scene: 'home', cursor: this.cursor, size: PAGE_SIZE })
        if (r.code !== 0) throw new Error(r.message || 'page_failed')
        const incoming = (r.data.items || []).filter((it) => !this.displayedItemIds.has(it.itemId))
        for (const it of incoming) this.displayedItemIds.add(it.itemId)
        this.items.push(...incoming)
        this.cursor = r.data.cursor
        this.hasMore = r.data.hasMore
        if (!r.data.hasMore && incoming.length === 0) {
          await this.refresh('exhausted')
        }
      } finally {
        this.loading = false
      }
    },
    async reportExposed (itemIds) {
      const user = useUserStore()
      if (!this.requestId || !itemIds.length) return
      try {
        const r = await confirmExposure({
          userId: user.userId,
          requestId: this.requestId,
          itemIds,
          timestamp: Date.now()
        })
        if (r?.data?.allExposed) {
          await this.refresh('exhausted')
        }
      } catch {}
    }
  }
})
