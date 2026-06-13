import { onBeforeUnmount, onMounted } from 'vue'

export function useInfiniteScroll (onReachBottom, distance = 200) {
  function handler () {
    const scrolled = window.innerHeight + window.scrollY
    if (scrolled + distance >= document.body.offsetHeight) {
      onReachBottom()
    }
  }
  onMounted(() => window.addEventListener('scroll', handler, { passive: true }))
  onBeforeUnmount(() => window.removeEventListener('scroll', handler))
}
