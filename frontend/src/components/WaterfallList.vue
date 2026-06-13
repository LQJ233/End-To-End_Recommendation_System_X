<template>
  <div class="waterfall">
    <ProductCard
      v-for="item in items"
      :key="item.itemId"
      :item="item"
      :register-exposure="registerExposure"
    />
  </div>
</template>

<script setup>
import ProductCard from './ProductCard.vue'
defineProps({
  items: { type: Array, default: () => [] },
  registerExposure: { type: Function, default: null }
})
</script>

<style scoped>
.waterfall {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}
</style>
