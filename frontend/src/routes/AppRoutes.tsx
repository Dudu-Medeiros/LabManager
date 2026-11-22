import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Home } from '../pages/Home'
import { Totem } from '../pages/Totem'
import { Painel } from '../pages/Painel'
import { Login } from '../pages/Login'
import { Atendimento } from '../pages/Atendimento'
import { PlaceholderPage } from '../pages/PlaceholderPage'
import { ProtectedRoute } from '../components/ProtectedRoute'

export function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/totem" element={<Totem />} />
        <Route path="/painel" element={<Painel />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/atendimento"
          element={
            <ProtectedRoute perfis={['ATENDENTE', 'GESTOR']}>
              <Atendimento />
            </ProtectedRoute>
          }
        />
        <Route
          path="/relatorios"
          element={
            <ProtectedRoute perfis={['GESTOR']}>
              <PlaceholderPage titulo="Relatórios" />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}