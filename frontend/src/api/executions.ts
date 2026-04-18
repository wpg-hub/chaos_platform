import { request } from './request'
import type { 
  ExecutionCreate, ExecutionResponse, ExecutionListResponse, 
  ExecutionDetailResponse 
} from './types'

export const executionApi = {
  getList(params?: {
    page?: number
    page_size?: number
    status?: string
    case_id?: number
    executor_id?: number
  }): Promise<ExecutionListResponse> {
    return request.get('/executions', { params })
  },
  
  get(id: number): Promise<ExecutionDetailResponse> {
    return request.get(`/executions/${id}`)
  },
  
  create(data: ExecutionCreate): Promise<ExecutionResponse> {
    return request.post('/executions', data)
  },
  
  cancel(id: number): Promise<{ message: string }> {
    return request.post(`/executions/${id}/cancel`)
  },
  
  getLogs(id: number): Promise<Array<{ level: string; message: string; timestamp: string }>> {
    return request.get(`/executions/${id}/logs`)
  },
  
  downloadReport(id: number, format: string = 'html'): string {
    return `/api/executions/${id}/report?format=${format}`
  },
  
  delete(id: number): Promise<{ message: string }> {
    return request.delete(`/executions/${id}`)
  },
  
  deleteBatch(ids: number[]): Promise<{ message: string }> {
    return request.delete('/executions', { params: { execution_ids: ids.join(',') } })
  }
}
