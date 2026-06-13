import { sendBehavior } from '../api/tracking'
import { useUserStore } from '../stores/user'
import { useRecommendationStore } from '../stores/recommendation'

export const BEHAVIOR = {
  EXPOSURE: 0,
  CLICK: 1,
  FAVORITE: 2,
  CART: 3,
  PURCHASE: 4
}

export function useBehaviorTracker () {
  const user = useUserStore()
  const rec = useRecommendationStore()

  function track (itemId, behaviorType) {
    sendBehavior({
      userId: user.userId,
      itemId,
      behaviorType,
      timestamp: Date.now(),
      requestId: rec.requestId,
      scene: 'home'
    })
  }

  return { track, BEHAVIOR }
}
