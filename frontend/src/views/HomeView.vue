<template>
  <div class="home">
    <RefreshBar
      :shown="rec.items.length"
      :candidate="rec.candidateSize"
      :request-id="rec.requestId"
      :model-version="rec.modelVersion"
      :refreshing="rec.refreshing"
      @refresh="onManualRefresh"
    />
    <WaterfallList :items="rec.items" :register-exposure="observe" />
    <div v-if="rec.loading" class="loading">加载中...</div>
    <div v-else-if="!rec.hasMore && rec.items.length" class="loading">已到底部</div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import RefreshBar from '../components/RefreshBar.vue'
import WaterfallList from '../components/WaterfallList.vue'
import { useRecommendationStore } from '../stores/recommendation'
import { useExposureTracker } from '../composables/useExposureTracker'
import { useInfiniteScroll } from '../composables/useInfiniteScroll'

const rec = useRecommendationStore()
const { observe } = useExposureTracker()

useInfiniteScroll(() => rec.loadNextPage(), 200)

onMounted(async () => {
  rec.reset()
  await rec.refresh('auto')
})

async function onManualRefresh () {
  rec.reset()
  await rec.refresh('manual')
}
</script>

<style scoped>
.home { max-width: 1200px; margin: 0 auto; }
.loading { text-align: center; color: #909399; padding: 16px 0; }
</style>
