import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRecommendationStore } from '../stores/recommendation'
import { useBehaviorTracker, BEHAVIOR } from './useBehaviorTracker'

/**
 * Watches a list of card refs; once a card is >=50% visible the exposure is
 * tracked (Kafka + backend confirm) exactly once per requestId.
 */
export function useExposureTracker () {
  const observed = new Set()
  const tracker = useBehaviorTracker()
  const rec = useRecommendationStore()
  const observer = ref(null)
  const pendingFlush = ref([])
  let flushTimer = null

  function scheduleFlush () {
    if (flushTimer) return
    flushTimer = setTimeout(() => {
      const ids = pendingFlush.value
      pendingFlush.value = []
      flushTimer = null
      if (ids.length) rec.reportExposed(ids)
    }, 500)
  }

  function observe (el, itemId) {
    if (!el || !observer.value) return
    el.dataset.itemId = itemId
    observer.value.observe(el)
  }

  function unobserve (el) {
    if (el && observer.value) observer.value.unobserve(el)
  }

  onMounted(() => {
    observer.value = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue
        if (e.intersectionRatio < 0.5) continue
        const itemId = e.target.dataset.itemId
        const dedupKey = `${rec.requestId}:${itemId}`
        if (observed.has(dedupKey)) continue
        observed.add(dedupKey)
        tracker.track(itemId, BEHAVIOR.EXPOSURE)
        pendingFlush.value.push(itemId)
        scheduleFlush()
      }
    }, { threshold: [0.5] })
  })

  onBeforeUnmount(() => {
    observer.value?.disconnect()
    if (flushTimer) { clearTimeout(flushTimer); flushTimer = null }
  })

  return { observe, unobserve }
}
