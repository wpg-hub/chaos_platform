<template>
  <div class="start-node">
    <div class="node-content">
      <el-icon class="node-icon"><VideoPlay /></el-icon>
      <span class="node-label">开始</span>
    </div>
    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
</script>

<style scoped lang="scss">
.start-node {
  .node-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 80px;
    height: 80px;
    background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
    border-radius: 50%;
    color: #fff;
    box-shadow: 0 4px 12px rgba(103, 194, 58, 0.4);
    
    .node-icon {
      font-size: 24px;
      margin-bottom: 4px;
    }
    
    .node-label {
      font-size: 12px;
      font-weight: 500;
    }
  }
}
</style>
