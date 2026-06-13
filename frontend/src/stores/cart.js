import { defineStore } from 'pinia'

export const useCartStore = defineStore('cart', {
  state: () => ({ items: [] }),
  actions: {
    add (item) {
      const existing = this.items.find((i) => i.itemId === item.itemId)
      if (existing) {
        existing.qty += 1
      } else {
        this.items.push({ ...item, qty: 1 })
      }
    },
    remove (itemId) {
      this.items = this.items.filter((i) => i.itemId !== itemId)
    },
    clear () { this.items = [] }
  }
})
