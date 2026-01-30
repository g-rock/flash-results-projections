<template>
  <div
    v-if="modelValue"
    class="modal-backdrop"
    @click.self="close"
  >
    <div class="modal">
      <div class="modal-header">
        <h3>Point allocation</h3>
        <button class="modal-close" @click="close">×</button>
      </div>

      <div class="modal-body">
        <ul class="status-list">
          <li v-for="status in statuses" :key="status.key">
            <span class="status-name">
              <span
                class="status-dot"
                :class="`status-${status.key}`"
              ></span>
              {{ status.label }}
            </span>

            <span class="status-desc">
              {{ status.description }}
            </span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: { type: Boolean, required: true }
})

const emit = defineEmits(['update:modelValue'])

function close() {
  emit('update:modelValue', false)
}

const statuses = [
  {
    key: 'scored',
    label: 'Scored',
    description:
      'Points are based on place because the event has been scored.'
  },
  {
    key: 'scored-under-review',
    label: 'Scored (Under Review | Protest)',
    description:
      'Points are based on place, but the event is currently being evaluated by officials. It will be finalized soon.'
  },
  {
    key: 'in-progress',
    label: 'In-progress',
    description:
      'Points are based on athlete season best (SB)'
  },
  {
    key: 'projected',
    label: 'Projected',
    description:
      'Points are based on athlete season best (SB)'
  }
]
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal {
  background: #fff;
  border-radius: 6px;
  width: 90%;
  max-width: 480px;
  max-height: 80vh;
  overflow: auto;
  box-shadow: 0 20px 40px rgba(0,0,0,0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #ddd;
}

.modal-body {
  padding: 16px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
}

.status-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.status-list li {
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.status-list li:last-child {
  border-bottom: none;
}

.status-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin-bottom: 4px;
}

.status-desc {
  display: block;
  font-size: 0.9rem;
  color: #555;
  line-height: 1.4;
  margin-left: 38px;
}

.status-dot {
  width: 30px;
  height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}

.status-dot.status-scored {
  border: 1px solid #1D6F42;
  background-color: #63BE7B;
}

.status-dot.status-scored-under-review {
  background-color: #B30000;
}

.status-dot.status-projected {
  background-color: #E5F7FF;
  border: 1px solid #007ac6;
}

.status-dot.status-in-progress {
  background-color: #FFFF99;
  border: 1px solid #ad9100;
}
</style>
