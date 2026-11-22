import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Home } from '../pages/Home'
import { PlaceholderPage } from '../pages/PlaceholderPage'

export function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/totem" element={<PlaceholderPage titulo="Totem de Senhas" />} />
        <Route path="/painel" element={<PlaceholderPage titulo="Painel de Chamada" />} />
        <Route path="/login" element={<PlaceholderPage titulo="Login" />} />
        <Route path="/atendimento" element={<PlaceholderPage titulo="Atendimento" />} />
        <Route path="/relatorios" element={<PlaceholderPage titulo="Relatórios" />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}