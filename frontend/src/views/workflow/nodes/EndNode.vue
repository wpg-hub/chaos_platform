<template>
  <div class="end-node">
    <Handle type="target" :position="Position.Top" />
    <div class="node-content">
      <el-icon class="node-icon"><CircleClose /></el-icon>
      <span class="node-label">结束</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
</script>

<style scoped lang="scss">
.end-node {
  .node-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 80px;
    height: 80px;
    background: linear-gradient(135deg, #f56c6c 0%, #fa909a 100%);
    border-radius: 50%;
    color: #fff;
    box-shadow: 0 4px 12px rgba(245, 108, 108, 0.4);
    
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
