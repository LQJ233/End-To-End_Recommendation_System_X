<template>
  <div class="product-card" :ref="bindRef">
    <div class="img-wrap" @click="onClick">
      <img :src="item.imageUrl || placeholder" :alt="item.title" />
    </div>
    <div class="info">
      <div class="title" @click="onClick">{{ item.title }}</div>
      <div class="meta">
        <span class="price">¥{{ item.price?.toFixed ? item.price.toFixed(2) : item.price }}</span>
        <span v-if="item.brand" class="brand">{{ item.brand }}</span>
      </div>
      <div class="actions">
        <el-button size="small" :type="favored ? 'warning' : 'default'" @click.stop="onFavorite">{{ favored ? '已收藏' : '收藏' }}</el-button>
        <el-button size="small" @click.stop="onCart">加购</el-button>
        <el-button size="small" type="primary" @click.stop="onBuy">购买</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useBehaviorTracker, BEHAVIOR } from '../composables/useBehaviorTracker'
import { useCartStore } from '../stores/cart'
import { mockOrder } from '../api/item'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'

const props = defineProps({
  item: { type: Object, required: true },
  registerExposure: { type: Function, default: null }
})

const tracker = useBehaviorTracker()
const cart = useCartStore()
const user = useUserStore()
const favored = ref(false)
const placeholder = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHdpZHRoPScyMDAnIGhlaWdodD0nMjAwJz48cmVjdCB3aWR0aD0nMjAwJyBoZWlnaHQ9JzIwMCcgZmlsbD0nI2VlZSc+PC9yZWN0Pjx0ZXh0IHg9JzUwJScgeT0nNTAlJyB0ZXh0LWFuY2hvcj0nbWlkZGxlJyBmaWxsPScjOTk5JyBmb250LWZhbWlseT0nc2Fucy1zZXJpZic+SU1HPC90ZXh0Pjwvc3ZnPg=='

function bindRef (el) {
  if (el && props.registerExposure) {
    props.registerExposure(el, props.item.itemId)
  }
}

function onClick () { tracker.track(props.item.itemId, BEHAVIOR.CLICK) }
function onFavorite () {
  favored.value = !favored.value
  tracker.track(props.item.itemId, BEHAVIOR.FAVORITE)
}
function onCart () {
  cart.add(props.item)
  tracker.track(props.item.itemId, BEHAVIOR.CART)
  ElMessage.success('已加入购物车')
}
async function onBuy () {
  tracker.track(props.item.itemId, BEHAVIOR.PURCHASE)
  try {
    const r = await mockOrder({ userId: user.userId, itemId: props.item.itemId })
    if (r.code === 0) ElMessage.success(`已模拟下单 ${r.data.orderId}`)
  } catch {
    ElMessage.warning('模拟下单失败')
  }
}
</script>

<style scoped>
.product-card { background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 2px rgba(0,0,0,0.04); display: flex; flex-direction: column; }
.img-wrap { aspect-ratio: 1 / 1; background: #f0f1f3; cursor: pointer; }
.img-wrap img { width: 100%; height: 100%; object-fit: cover; display: block; }
.info { padding: 8px 10px 12px; display: flex; flex-direction: column; gap: 6px; }
.title { font-size: 14px; color: #303133; line-height: 1.3; min-height: 36px; cursor: pointer; }
.meta { display: flex; align-items: baseline; gap: 6px; }
.price { color: #f56c6c; font-weight: 600; }
.brand { color: #909399; font-size: 12px; }
.actions { display: flex; gap: 4px; }
.actions .el-button { flex: 1; }
</style>
