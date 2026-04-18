export interface UserResponse {
  id: number
  username: string
  email: string | null
  role: string
  is_active: boolean
  created_at: string
  updated_at: string | null
}

export interface UserCreate {
  username: string
  email?: string
  password: string
  role: string
}

export interface UserUpdate {
  email?: string
  role?: string
  is_active?: boolean
  password?: string
}

export interface Token {
  access_token: string
  token_type: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TagResponse {
  id: number
  name: string
  color: string
  created_at: string
}

export interface TagCreate {
  name: string
  color?: string
}

export interface CaseResponse {
  id: number
  name: string
  description: string | null
  yaml_content: string
  file_path: string | null
  case_type: string | null
  folder_id: number | null
  is_template: boolean
  sort_order: number
  creator_id: number | null
  tags: TagResponse[]
  created_at: string
  updated_at: string | null
}

export interface CaseCreate {
  name: string
  description?: string
  yaml_content: string
  case_type?: string
  folder_id?: number
  is_template?: boolean
  tags?: string[]
}

export interface CaseUpdate {
  name?: string
  description?: string
  yaml_content?: string
  folder_id?: number
  is_template?: boolean
  tags?: string[]
}

export interface CaseCopyRequest {
  name?: string
  folder_id?: number
}

export interface CaseMoveRequest {
  folder_id?: number
  sort_order?: number
}

export interface CaseRenameRequest {
  name: string
}

export interface CaseListResponse {
  items: CaseResponse[]
  total: number
  page: number
  page_size: number
}

export interface CaseValidateRequest {
  yaml_content: string
}

export interface CaseValidateResponse {
  valid: boolean
  error: string | null
  case_type: string | null
}

export interface CaseImportRequest {
  file_path: string
  name?: string
  folder_id?: number
  tags?: string[]
}

export interface FolderResponse {
  id: number
  name: string
  parent_id: number | null
  creator_id: number | null
  sort_order: number
  created_at: string
  updated_at: string | null
  children: FolderResponse[]
  case_count: number
}

export interface FolderCreate {
  name: string
  parent_id?: number
}

export interface FolderUpdate {
  name?: string
  parent_id?: number
  sort_order?: number
}

export interface ExecutionResponse {
  id: number
  case_id: number | null
  case_name: string | null
  executor_id: number | null
  executor_name: string | null
  status: string
  start_time: string | null
  end_time: string | null
  duration: number | null
  result: Record<string, any> | null
  error_message: string | null
  report_path: string | null
  created_at: string
}

export interface ExecutionListResponse {
  items: ExecutionResponse[]
  total: number
  page: number
  page_size: number
}

export interface ExecutionLogResponse {
  id: number
  execution_id: number
  level: string
  message: string
  timestamp: string
}

export interface ExecutionDetailResponse extends ExecutionResponse {
  logs: ExecutionLogResponse[]
  yaml_content: string | null
}

export interface ExecutionCreate {
  case_id: number
}

export interface ScheduleResponse {
  id: number
  name: string
  case_id: number
  case_name: string | null
  cron_expr: string
  creator_id: number | null
  creator_name: string | null
  is_active: boolean
  next_run: string | null
  last_run: string | null
  last_status: string | null
  created_at: string
  updated_at: string | null
}

export interface ScheduleCreate {
  name: string
  case_id: number
  cron_expr: string
}

export interface ScheduleUpdate {
  name?: string
  cron_expr?: string
  is_active?: boolean
}

export interface ScheduleListResponse {
  items: ScheduleResponse[]
  total: number
  page: number
  page_size: number
}
