<template>
  <div
    class="context-menu-item"
    :class="{ 'is-divided': divided }"
    @click="handleClick"
  >
    <el-icon v-if="icon" class="menu-icon">
      <component :is="icon" />
    </el-icon>
    <span class="menu-label">
      <slot></slot>
    </span>
  </div>
</template>

<script setup lang="ts">
import { ElIcon } from 'element-plus'
import type { Component } from 'vue'

interface Props {
  icon?: Component
  divided?: boolean
}

withDefaults(defineProps<Props>(), {
  icon: undefined,
  divided: false
})
const emit = defineEmits<{
  click: []
}>()

const handleClick = () => {
  emit('click')
}
</script>

<style scoped>
.context-menu-item {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.context-menu-item:hover {
  background-color: #f5f7fa;
}

.context-menu-item.is-divided {
  border-top: 1px solid #ebeef5;
  margin-top: 4px;
  padding-top: 12px;
}

.menu-icon {
  margin-right: 8px;
  font-size: 14px;
  color: #606266;
}

.menu-label {
  font-size: 14px;
  color: #303133;
}
</style>
