import { request } from './request'
import type { 
  CaseCreate, CaseUpdate, CaseResponse, CaseListResponse,
  CaseValidateRequest, CaseValidateResponse, CaseImportRequest,
  FolderResponse, FolderCreate, FolderUpdate, TagCreate, TagResponse,
  CaseCopyRequest, CaseMoveRequest, CaseRenameRequest
} from './types'

export const caseApi = {
  getList(params?: {
    page?: number
    page_size?: number
    folder_id?: number
    tag?: string
    keyword?: string
    is_template?: boolean
  }): Promise<CaseListResponse> {
    return request.get('/cases', { params })
  },
  
  get(id: number): Promise<CaseResponse> {
    return request.get(`/cases/${id}`)
  },
  
  create(data: CaseCreate): Promise<CaseResponse> {
    return request.post('/cases', data)
  },
  
  update(id: number, data: CaseUpdate): Promise<CaseResponse> {
    return request.put(`/cases/${id}`, data)
  },
  
  delete(id: number): Promise<{ message: string }> {
    return request.delete(`/cases/${id}`)
  },
  
  validate(data: CaseValidateRequest): Promise<CaseValidateResponse> {
    return request.post('/cases/validate', data)
  },
  
  import(data: CaseImportRequest): Promise<CaseResponse> {
    return request.post('/cases/import', data)
  },
  
  getTags(): Promise<TagResponse[]> {
    return request.get('/cases/tags')
  },
  
  createTag(data: TagCreate): Promise<TagResponse> {
    return request.post('/cases/tags', data)
  },
  
  copy(id: number, data?: CaseCopyRequest): Promise<CaseResponse> {
    return request.post(`/cases/${id}/copy`, data || {})
  },
  
  rename(id: number, data: CaseRenameRequest): Promise<CaseResponse> {
    return request.put(`/cases/${id}/rename`, data)
  },
  
  move(id: number, data: CaseMoveRequest): Promise<CaseResponse> {
    return request.put(`/cases/${id}/move`, data)
  }
}

export const folderApi = {
  getList(): Promise<FolderResponse[]> {
    return request.get('/folders')
  },
  
  get(id: number): Promise<FolderResponse> {
    return request.get(`/folders/${id}`)
  },
  
  create(data: FolderCreate): Promise<FolderResponse> {
    return request.post('/folders', data)
  },
  
  update(id: number, data: FolderUpdate): Promise<FolderResponse> {
    return request.put(`/folders/${id}`, data)
  },
  
  delete(id: number): Promise<{ message: string }> {
    return request.delete(`/folders/${id}`)
  }
}
