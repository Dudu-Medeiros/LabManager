import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight, Headphones, Monitor, Ticket } from 'lucide-react'
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { BrandLogo } from '../components/BrandLogo'

type ApiStatus = 'verificando' | 'online' | 'offline'

export function Home() {
  const [status, setStatus] = useState<ApiStatus>('verificando')
  const { autenticado, usuario } = useAuth()

  useEffect(() => {
    api
      .get('/health')
      .then(() => setStatus('online'))
      .catch(() => setStatus('offline'))
  }, [])

  const modulos = [
    {
      codigo: '01',
      titulo: 'Totem de Senhas',
      ambiente: 'Recepção · Público',
      descricao: 'Autoatendimento para retirada de senhas prioritárias, exames e atendimento geral.',
      rota: '/totem',
      icone: Ticket,
    },
    {
      codigo: '02',
      titulo: 'Painel de Chamada',
      ambiente: 'Sala de Espera · TV',
      descricao: 'Exibição em tela cheia das chamadas ativas, guichês e fila por categoria.',
      rota: '/painel',
      icone: Monitor,
    },
    {
      codigo: '03',
      titulo: autenticado ? 'Operação de Guichê' : 'Acesso Interno',
      ambiente: autenticado ? `${usuario?.perfil} · Ativo` : 'Equipe · Restrito',
      descricao: autenticado
        ? `Sessão aberta como ${usuario?.nome}. Retomar chamadas no guichê.`
        : 'Autenticação para atendentes e gestores controlarem a fila de atendimento.',
      rota: autenticado ? '/atendimento' : '/login',
      icone: Headphones,
    },
  ]

  return (
    <div className="min-h-screen flex flex-col bg-canvas text-ink">
      <header className="border-b border-line bg-white">
        <div className="max-w-5xl mx-auto px-6 h-18 flex items-center justify-between">
          <BrandLogo subtitulo="Unidade Laboratorial" />

          <div
            className={`inline-flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-lg border ${
              status === 'online'
                ? 'bg-brand-50 text-brand-800 border-brand-500/30'
                : status === 'offline'
                  ? 'bg-red-50 text-red-700 border-red-200'
                  : 'bg-slate-100 text-slate-600 border-line'
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                status === 'online'
                  ? 'bg-brand-500'
                  : status === 'offline'
                    ? 'bg-red-500'
                    : 'bg-slate-400'
              }`}
            />
            {status === 'online' && 'Sistema operacional'}
            {status === 'offline' && 'API indisponível'}
            {status === 'verificando' && 'Conectando...'}
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-5xl w-full mx-auto px-6 py-14 flex flex-col justify-between gap-12">
        <section className="space-y-10">
          <div className="border-l-2 border-brand-800 pl-5 max-w-2xl space-y-2">
            <p className="text-xs font-mono uppercase tracking-widest text-brand-800 font-semibold">
              Central de Operações
            </p>
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-ink">
              Controle de filas e atendimento clínico
            </h1>
            <p className="text-slate-600 text-sm sm:text-base">
              Escolha o terminal que deseja iniciar neste equipamento.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {modulos.map((modulo) => {
              const Icone = modulo.icone
              return (
                <Link
                  key={modulo.rota}
                  to={modulo.rota}
                  className="group flex flex-col justify-between rounded-xl border border-line bg-white p-6 transition hover:border-brand-800 hover:shadow-sm"
                >
                  <div className="space-y-5">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-semibold text-brand-800 bg-brand-50 border border-brand-500/20 px-2 py-1 rounded-md">
                        {modulo.codigo}
                      </span>
                      <Icone className="h-5 w-5 text-slate-400 group-hover:text-brand-800 transition" />
                    </div>

                    <div className="space-y-1.5">
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                        {modulo.ambiente}
                      </p>
                      <h2 className="text-lg font-bold text-ink">{modulo.titulo}</h2>
                      <p className="text-sm text-slate-600 leading-relaxed pt-1">
                        {modulo.descricao}
                      </p>
                    </div>
                  </div>

                  <div className="mt-7 pt-4 border-t border-line/70 flex items-center justify-between text-sm font-semibold text-brand-800">
                    <span>Abrir módulo</span>
                    <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                  </div>
                </Link>
              )
            })}
          </div>
        </section>

        <footer className="border-t border-line pt-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs text-slate-500">
          <span>LabManager · Fluxo de Atendimento e Triagem</span>
          <span className="font-mono">SP · SE · SG</span>
        </footer>
      </main>
    </div>
  )
}