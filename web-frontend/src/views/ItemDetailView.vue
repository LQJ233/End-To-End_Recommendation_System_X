<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { mockProducts } from '../mock/products'
import { fetchItem, mapApiItemToProduct } from '../services/api'
import { trackDetailView } from '../services/tracking'

const route = useRoute()
const router = useRouter()

const item = ref(null)

onMounted(async () => {
  const itemId = Number(route.params.id)
  try {
    item.value = mapApiItemToProduct(await fetchItem(itemId))
  } catch {
    item.value = mockProducts.find((product) => product.id === itemId) || null
  }
  if (item.value) {
    trackDetailView(item.value, {
      page: 'item_detail',
      source: 'home_click',
      request_id: `req-${Date.now()}`,
      recommendation_id: `rec-${Date.now()}`,
    })
  }
})
</script>

<template>
  <div class="detail-page">
    <header class="topbar">
      <el-button @click="router.push('/')">返回首页</el-button>
    </header>
    <el-card v-if="item" class="detail-card">
      <div class="detail-emoji">{{ item.emoji }}</div>
      <div class="detail-title">{{ item.title }}</div>
      <div class="detail-meta">{{ item.category }} · {{ item.brand }}</div>
      <div class="detail-price">¥{{ item.price.toFixed(2) }}</div>
      <p class="detail-desc">这是 Phase 1 的静态商品详情页，用于验证曝光、点击和详情浏览埋点。</p>
    </el-card>
    <el-empty v-else description="商品不存在" />
  </div>
</template>

<style scoped>
.detail-page {
  min-height: 100vh;
  background: #f8fafc;
}

.topbar {
  padding: 18px 24px;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
}

.detail-card {
  max-width: 720px;
  margin: 32px auto;
  text-align: center;
}

.detail-emoji {
  font-size: 92px;
  margin: 20px 0;
}

.detail-title {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
}

.detail-meta {
  margin-top: 8px;
  color: #64748b;
}

.detail-price {
  margin-top: 16px;
  color: #dc2626;
  font-size: 24px;
  font-weight: 700;
}

.detail-desc {
  margin-top: 20px;
  color: #475569;
  line-height: 1.7;
}
</style>
