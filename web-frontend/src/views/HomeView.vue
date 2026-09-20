<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { mockProducts } from '../mock/products'
import { fetchHome, mapApiItemToProduct } from '../services/api'
import { trackClick, trackExposure, trackRefreshHome } from '../services/tracking'

const router = useRouter()
const products = ref([])
const requestId = ref(`req-${Date.now()}`)
const recommendationId = ref(`rec-${Date.now()}`)
let exposureObserver = null
const exposedItems = new Set()

const userName = computed(() => localStorage.getItem('mock_user_id') || 'anonymous')

function setupExposureObserver() {
  exposureObserver?.disconnect()
  exposedItems.clear()

  exposureObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) {
        return
      }

      const itemId = Number(entry.target.dataset.itemId)
      const item = products.value.find((product) => product.id === itemId)

      if (!item || exposedItems.has(item.id)) {
        return
      }

      exposedItems.add(item.id)
      trackExposure(item, {
        page: 'home',
        source: 'card_exposure',
        request_id: requestId.value,
        recommendation_id: recommendationId.value,
      })
    })
  }, {
    threshold: 0.5,
  })

  document.querySelectorAll('[data-item-id]').forEach((element) => {
    exposureObserver.observe(element)
  })
}

async function refresh() {
  requestId.value = `req-${Date.now()}`
  recommendationId.value = `rec-${Date.now()}`
  trackRefreshHome({
    request_id: requestId.value,
    recommendation_id: recommendationId.value,
  })
  try {
    const home = await fetchHome(userName.value)
    if (!home.items?.length) {
      throw new Error('empty recommendation response')
    }
    requestId.value = home.requestId || requestId.value
    recommendationId.value = home.recommendationId || recommendationId.value
    products.value = home.items.map(mapApiItemToProduct)
  } catch {
    products.value = [...mockProducts].sort(() => Math.random() - 0.5)
  }
  await nextTick()
  setupExposureObserver()
}

function openItem(item, index) {
  trackClick(item, {
    page: 'home',
    position: index + 1,
    source: 'home_card',
    request_id: requestId.value,
    recommendation_id: recommendationId.value,
  })
  router.push(`/items/${item.id}`)
}

onMounted(() => {
  refresh()
})

onBeforeUnmount(() => {
  exposureObserver?.disconnect()
})
</script>

<template>
  <div class="home-page">
    <header class="topbar">
      <div>
        <div class="app-title">电商广告推荐系统</div>
        <div class="user-name">当前用户：{{ userName }}</div>
      </div>
      <el-button type="primary" @click="refresh">刷新推荐</el-button>
    </header>

    <main class="product-grid">
      <el-card v-for="(item, index) in products" :key="item.id" :data-item-id="item.id" shadow="hover" class="product-card" @click="openItem(item, index)">
        <div class="product-emoji">{{ item.emoji }}</div>
        <div class="product-title">{{ item.title }}</div>
        <div class="product-meta">
          <span>{{ item.category }}</span>
          <span>{{ item.brand }}</span>
        </div>
        <div class="product-price">¥{{ item.price.toFixed(2) }}</div>
      </el-card>
    </main>
  </div>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
  background: #f8fafc;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 28px;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
}

.app-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.user-name {
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 18px;
  padding: 24px 28px;
}

.product-card {
  cursor: pointer;
}

.product-emoji {
  height: 110px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 56px;
  background: #f1f5f9;
  border-radius: 12px;
  margin-bottom: 14px;
}

.product-title {
  font-size: 14px;
  color: #0f172a;
  margin-bottom: 8px;
}

.product-meta {
  display: flex;
  justify-content: space-between;
  color: #64748b;
  font-size: 12px;
  margin-bottom: 8px;
}

.product-price {
  color: #dc2626;
  font-weight: 700;
}
</style>
