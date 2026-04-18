import { defineStore } from 'pinia'
import { ref } from 'vue'
import { caseApi, folderApi } from '@/api/cases'
import type { CaseResponse, CaseListResponse, FolderResponse, TagResponse } from '@/api/types'

export const useCaseStore = defineStore('cases', () => {
  const cases = ref<CaseResponse[]>([])
  const total = ref(0)
  const folders = ref<FolderResponse[]>([])
  const tags = ref<TagResponse[]>([])
  const loading = ref(false)

  async function fetchCases(params?: {
    page?: number
    page_size?: number
    folder?: string
    tag?: string
    keyword?: string
    is_template?: boolean
  }) {
    loading.value = true
    try {
      const response: CaseListResponse = await caseApi.getList(params)
      cases.value = response.items
      total.value = response.total
      return response
    } finally {
      loading.value = false
    }
  }

  async function fetchFolders() {
    folders.value = await folderApi.getList()
  }

  async function fetchTags() {
    tags.value = await caseApi.getTags()
  }

  return {
    cases,
    total,
    folders,
    tags,
    loading,
    fetchCases,
    fetchFolders,
    fetchTags
  }
})
