import { request } from './request'
import type { UserCreate, UserUpdate, UserResponse } from './types'

export const userApi = {
  getList(): Promise<UserResponse[]> {
    return request.get('/users')
  },
  
  create(data: UserCreate): Promise<UserResponse> {
    return request.post('/users', data)
  },
  
  update(id: number, data: UserUpdate): Promise<UserResponse> {
    return request.put(`/users/${id}`, data)
  },
  
  delete(id: number): Promise<{ message: string }> {
    return request.delete(`/users/${id}`)
  }
}
