import { Navigate } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useAuth } from '../contexts/AuthContext'
import type { PerfilUsuario } from '../types'

interface ProtectedRouteProps {
  children: ReactNode
  perfis?: PerfilUsuario[]
}

export function ProtectedRoute({ children, perfis }: ProtectedRouteProps) {
  const { autenticado, usuario } = useAuth()

  if (!autenticado || !usuario) {
    return <Navigate to="/login" replace />
  }

  if (perfis && !perfis.includes(usuario.perfil)) {
    return <Navigate to="/atendimento" replace />
  }

  return <>{children}</>
}