import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'
import { loginRequest } from '../services/authService'
import type { Usuario } from '../types'

interface AuthContextData {
  usuario: Usuario | null
  token: string | null
  autenticado: boolean
  login: (email: string, senha: string) => Promise<void>
  logout: () => void
}

const TOKEN_KEY = 'labmanager_token'
const USER_KEY = 'labmanager_user'

const AuthContext = createContext<AuthContextData | undefined>(undefined)

function carregarUsuarioSalvo(): Usuario | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as Usuario
  } catch {
    localStorage.removeItem(USER_KEY)
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [usuario, setUsuario] = useState<Usuario | null>(() => carregarUsuarioSalvo())

  async function login(email: string, senha: string) {
    const resposta = await loginRequest(email, senha)
    localStorage.setItem(TOKEN_KEY, resposta.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(resposta.usuario))
    setToken(resposta.access_token)
    setUsuario(resposta.usuario)
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setToken(null)
    setUsuario(null)
  }

  return (
    <AuthContext.Provider
      value={{
        usuario,
        token,
        autenticado: Boolean(token && usuario),
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth deve ser usado dentro de AuthProvider')
  return ctx
}