import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Lock, Mail } from 'lucide-react'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import { BrandLogo } from '../components/BrandLogo'

export function Login() {
  const navigate = useNavigate()
  const { login, usuario } = useAuth()

  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [carregando, setCarregando] = useState(false)

  useEffect(() => {
    if (!usuario) return
    const destino = usuario.perfil === 'GESTOR' ? '/relatorios' : '/atendimento'
    navigate(destino, { replace: true })
  }, [usuario, navigate])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setErro('')
    setCarregando(true)

    try {
      await login(email.trim(), senha)
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.erro) {
        setErro(err.response.data.erro)
      } else {
        setErro('Não foi possível conectar ao servidor.')
      }
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-12 bg-canvas">
      <aside className="hidden lg:flex lg:col-span-5 bg-brand-950 text-white p-12 flex-col justify-between border-r border-brand-800/40">
        <BrandLogo tema="escuro" subtitulo="Acesso Restrito" />

        <div className="space-y-5 max-w-sm">
          <div className="h-1 w-12 bg-brand-400 rounded-full" />
          <h2 className="text-3xl font-bold tracking-tight leading-tight">
            Operação de guichês com prioridade automatizada.
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed">
            Gerencie chamadas, rechamadas e atendimentos com registro completo de auditoria em tempo real.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-3 pt-6 border-t border-brand-800/50 text-xs">
          <div>
            <span className="font-mono font-bold text-brand-400 block">SP</span>
            <span className="text-slate-400">Prioritária</span>
          </div>
          <div>
            <span className="font-mono font-bold text-brand-400 block">SE</span>
            <span className="text-slate-400">Exames</span>
          </div>
          <div>
            <span className="font-mono font-bold text-brand-400 block">SG</span>
            <span className="text-slate-400">Geral</span>
          </div>
        </div>
      </aside>

      <main className="lg:col-span-7 flex flex-col justify-center px-6 py-12">
        <div className="w-full max-w-md mx-auto space-y-8">
          <div className="flex items-center justify-between">
            <Link
              to="/"
              className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-brand-800 transition"
            >
              <ArrowLeft className="h-4 w-4" />
              Voltar ao início
            </Link>
            <div className="lg:hidden">
              <BrandLogo tamanho="sm" />
            </div>
          </div>

          <div className="rounded-xl border border-line bg-white p-8 space-y-6">
            <div className="space-y-1.5">
              <p className="text-xs font-mono font-semibold uppercase tracking-wider text-brand-800">
                Identificação
              </p>
              <h1 className="text-2xl font-bold tracking-tight text-ink">
                Entrar no painel
              </h1>
              <p className="text-sm text-slate-500">
                Informe suas credenciais de atendente ou gestor.
              </p>
            </div>

            {erro && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {erro}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label htmlFor="email" className="block text-sm font-semibold text-ink">
                  Email institucional
                </label>
                <div className="relative">
                  <Mail className="h-4 w-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    id="email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="atendente@labflow.com"
                    className="w-full rounded-lg border border-line bg-canvas/40 pl-10 pr-4 py-2.5 text-sm text-ink outline-none focus:bg-white focus:border-brand-800 focus:ring-2 focus:ring-brand-800/15 transition"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label htmlFor="senha" className="block text-sm font-semibold text-ink">
                  Senha
                </label>
                <div className="relative">
                  <Lock className="h-4 w-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    id="senha"
                    type="password"
                    required
                    value={senha}
                    onChange={(e) => setSenha(e.target.value)}
                    placeholder="••••••••"
                    className="w-full rounded-lg border border-line bg-canvas/40 pl-10 pr-4 py-2.5 text-sm text-ink outline-none focus:bg-white focus:border-brand-800 focus:ring-2 focus:ring-brand-800/15 transition"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={carregando}
                className="w-full rounded-lg bg-brand-800 py-3 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60 transition cursor-pointer mt-2"
              >
                {carregando ? 'Validando acesso...' : 'Acessar sistema'}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  )
}