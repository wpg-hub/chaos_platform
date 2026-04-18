import { request } from './request'
import type { Token, UserResponse, LoginRequest } from './types'

export const authApi = {
  login(data: LoginRequest): Promise<Token> {
    return request.post('/auth/login', data)
  },
  
  logout(): Promise<{ message: string }> {
    return request.post('/auth/logout')
  },
  
  getMe(): Promise<UserResponse> {
    return request.get('/auth/me')
  }
}
