<template>
  <div class="workflow-node" :class="{ selected }">
    <Handle type="target" :position="Position.Top" />
    <div class="node-header">
      <el-icon class="node-type-icon"><Share /></el-icon>
      <span class="node-type">Workflow</span>
    </div>
    <div class="node-body">
      <div class="node-name">{{ data.label || '未命名' }}</div>
      <div class="node-meta">
        <el-tag v-if="data.onFailure === 'stop'" size="small" type="danger">失败停止</el-tag>
        <el-tag v-else size="small" type="success">失败继续</el-tag>
        <el-tag v-if="data.timeout && data.timeout > 0" size="small" type="info">{{ data.timeout }}s</el-tag>
      </div>
    </div>
    <div class="node-actions">
      <el-button size="small" link @click="$emit('edit', id)">
        <el-icon><Edit /></el-icon>
      </el-button>
      <el-button size="small" link @click="$emit('copy', id)">
        <el-icon><CopyDocument /></el-icon>
      </el-button>
      <el-button size="small" link type="danger" @click="$emit('delete', id)">
        <el-icon><Delete /></el-icon>
      </el-button>
    </div>
    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'

defineProps<{
  id: string
  data: {
    label?: string
    yaml_content?: string
    onFailure?: string
    timeout?: number
  }
  selected?: boolean
}>()

defineEmits<{
  edit: [id: string]
  copy: [id: string]
  delete: [id: string]
}>()
</script>

<style scoped lang="scss">
.workflow-node {
  background: #fff;
  border: 2px solid #e6a23c;
  border-radius: 8px;
  min-width: 180px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
  
  &.selected {
    border-color: #409eff;
    box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.2);
  }
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    
    .node-actions {
      opacity: 1;
    }
  }
  
  .node-header {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    background: linear-gradient(135deg, #e6a23c 0%, #f0c78a 100%);
    border-radius: 6px 6px 0 0;
    color: #fff;
    
    .node-type-icon {
      margin-right: 6px;
    }
    
    .node-type {
      font-size: 12px;
      font-weight: 500;
    }
  }
  
  .node-body {
    padding: 12px;
    
    .node-name {
      font-weight: 500;
      margin-bottom: 8px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    
    .node-meta {
      display: flex;
      gap: 4px;
      flex-wrap: wrap;
    }
  }
  
  .node-actions {
    display: flex;
    justify-content: flex-end;
    padding: 8px 12px;
    border-top: 1px solid #ebeef5;
    opacity: 0;
    transition: opacity 0.2s;
  }
}
</style>
