import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'

type ApiStatus = 'verificando' | 'online' | 'offline'

const MODULOS = [
  {
    titulo: 'Totem de Senhas',
    descricao: 'Emissão pública de senhas prioritárias, exames e gerais.',
    rota: '/totem',
  },
  {
    titulo: 'Painel de Chamada',
    descricao: 'Visualização em tempo real das senhas chamadas nos guichês.',
    rota: '/painel',
  },
  {
    titulo: 'Acesso Interno',
    descricao: 'Login para atendentes e gestores do laboratório.',
    rota: '/login',
  },
]

export function Home() {
  const [status, setStatus] = useState<ApiStatus>('verificando')

  useEffect(() => {
    api
      .get('/health')
      .then(() => setStatus('online'))
      .catch(() => setStatus('offline'))
  }, [])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 py-12">
      <div className="w-full max-w-3xl space-y-10">
        <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-6">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
              LabManager
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Sistema de gestão de filas e atendimento laboratorial
            </p>
          </div>

          <span
            className={`inline-flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full border w-fit ${
              status === 'online'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : status === 'offline'
                  ? 'bg-red-50 text-red-700 border-red-200'
                  : 'bg-slate-100 text-slate-600 border-slate-200'
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                status === 'online'
                  ? 'bg-emerald-500'
                  : status === 'offline'
                    ? 'bg-red-500'
                    : 'bg-slate-400'
              }`}
            />
            {status === 'online' && 'API conectada'}
            {status === 'offline' && 'API offline'}
            {status === 'verificando' && 'Verificando API...'}
          </span>
        </header>

        <main className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {MODULOS.map((modulo) => (
            <Link
              key={modulo.rota}
              to={modulo.rota}
              className="group block rounded-xl border border-slate-200 bg-white p-6 transition hover:border-slate-400 hover:shadow-sm"
            >
              <h2 className="text-base font-semibold text-slate-900 group-hover:text-slate-700">
                {modulo.titulo}
              </h2>
              <p className="text-sm text-slate-500 mt-2 leading-relaxed">
                {modulo.descricao}
              </p>
            </Link>
          ))}
        </main>
      </div>
    </div>
  )
}