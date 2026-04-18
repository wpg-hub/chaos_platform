import { request } from './request'
import type { 
  ScheduleCreate, ScheduleUpdate, ScheduleResponse, ScheduleListResponse 
} from './types'

export const scheduleApi = {
  getList(params?: {
    page?: number
    page_size?: number
    is_active?: boolean
  }): Promise<ScheduleListResponse> {
    return request.get('/schedules', { params })
  },
  
  get(id: number): Promise<ScheduleResponse> {
    return request.get(`/schedules/${id}`)
  },
  
  create(data: ScheduleCreate): Promise<ScheduleResponse> {
    return request.post('/schedules', data)
  },
  
  update(id: number, data: ScheduleUpdate): Promise<ScheduleResponse> {
    return request.put(`/schedules/${id}`, data)
  },
  
  toggle(id: number): Promise<{ message: string }> {
    return request.post(`/schedules/${id}/toggle`)
  },
  
  delete(id: number): Promise<{ message: string }> {
    return request.delete(`/schedules/${id}`)
  }
}
