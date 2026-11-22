import { api } from './api'
import type { Usuario } from '../types'

interface LoginResponse {
  access_token: string
  usuario: Usuario
}

export async function loginRequest(email: string, senha: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/api/auth/login', { email, senha })
  return data
}