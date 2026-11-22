import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Accessibility,
  ArrowLeft,
  Check,
  ClipboardCheck,
  Users,
} from 'lucide-react'
import axios from 'axios'
import { emitirSenhaRequest } from '../services/senhaService'
import { formatarHora, INFO_TIPO } from '../utils/senhas'
import { BrandLogo } from '../components/BrandLogo'
import type { Senha, TipoSenha } from '../types'

const OPCOES_TOTEM: { tipo: TipoSenha; icone: typeof Users }[] = [
  { tipo: 'SP', icone: Accessibility },
  { tipo: 'SE', icone: ClipboardCheck },
  { tipo: 'SG', icone: Users },
]

export function Totem() {
  const [emitindo, setEmitindo] = useState<TipoSenha | null>(null)
  const [senhaEmitida, setSenhaEmitida] = useState<Senha | null>(null)
  const [erro, setErro] = useState('')
  const [segundos, setSegundos] = useState(0)

  useEffect(() => {
    if (!senhaEmitida) return
    setSegundos(8)

    const intervalo = window.setInterval(() => {
      setSegundos((atual) => {
        if (atual <= 1) {
          window.clearInterval(intervalo)
          setSenhaEmitida(null)
          return 0
        }
        return atual - 1
      })
    }, 1000)

    return () => window.clearInterval(intervalo)
  }, [senhaEmitida])

  async function handleEmitir(tipo: TipoSenha) {
    setErro('')
    setEmitindo(tipo)

    try {
      const novaSenha = await emitirSenhaRequest(tipo)
      setSenhaEmitida(novaSenha)
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.erro) {
        setErro(err.response.data.erro)
      } else {
        setErro('Não foi possível emitir a senha. Tente novamente.')
      }
    } finally {
      setEmitindo(null)
    }
  }

  return (
    <div className="min-h-screen bg-canvas flex flex-col">
      <header className="border-b border-line bg-white">
        <div className="max-w-5xl mx-auto px-6 h-18 flex items-center justify-between">
          <BrandLogo subtitulo="Totem de Autoatendimento" />

          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-brand-800 transition"
          >
            <ArrowLeft className="h-4 w-4" />
            Início
          </Link>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-6 py-10">
        {senhaEmitida ? (
          <div className="w-full max-w-md">
            <div className="rounded-xl border border-line bg-white overflow-hidden shadow-sm">
              <div className="bg-brand-800 text-white px-6 py-5 flex items-center justify-between">
                <div>
                  <p className="text-[11px] font-mono uppercase tracking-widest text-brand-400">
                    Comprovante de Fila
                  </p>
                  <p className="text-sm font-semibold mt-0.5">LabManager · Recepção</p>
                </div>
                <div className="h-9 w-9 rounded-lg bg-brand-700 flex items-center justify-center">
                  <Check className="h-5 w-5 text-brand-400" />
                </div>
              </div>

              <div className="px-6 py-8 text-center space-y-3">
                <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">
                  Sua senha
                </p>
                <p className="text-4xl sm:text-5xl font-bold tracking-tight text-ink font-mono">
                  {senhaEmitida.numero}
                </p>
                <span
                  className={`inline-block text-xs font-semibold px-3 py-1 rounded-md border ${
                    INFO_TIPO[senhaEmitida.tipo].badge
                  }`}
                >
                  {senhaEmitida.tipo} · {INFO_TIPO[senhaEmitida.tipo].nome}
                </span>
              </div>

              <div className="relative border-t border-dashed border-line">
                <span className="h-5 w-5 rounded-full bg-canvas border border-line absolute -left-2.5 -top-2.5" />
                <span className="h-5 w-5 rounded-full bg-canvas border border-line absolute -right-2.5 -top-2.5" />
              </div>

              <div className="px-6 py-6 bg-brand-50/40 space-y-5">
                <div className="flex items-center justify-between text-xs text-slate-600">
                  <span>Emitida às</span>
                  <span className="font-mono font-semibold text-ink">
                    {formatarHora(senhaEmitida.data_emissao)}
                  </span>
                </div>

                <p className="text-xs text-center text-slate-600">
                  Acompanhe o número no painel da sala de espera.
                </p>

                <button
                  type="button"
                  onClick={() => setSenhaEmitida(null)}
                  className="w-full rounded-lg bg-brand-800 py-3 text-sm font-semibold text-white hover:bg-brand-700 transition cursor-pointer"
                >
                  Emitir nova senha ({segundos}s)
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="w-full max-w-4xl space-y-9">
            <div className="text-center space-y-2">
              <p className="text-xs font-mono font-semibold uppercase tracking-widest text-brand-800">
                Autoatendimento
              </p>
              <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-ink">
                Selecione o atendimento
              </h1>
              <p className="text-slate-600 text-base">
                Toque na categoria desejada para retirar sua senha.
              </p>
            </div>

            {erro && (
              <div className="max-w-xl mx-auto rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 text-center">
                {erro}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {OPCOES_TOTEM.map(({ tipo, icone: Icone }) => {
                const info = INFO_TIPO[tipo]
                const carregando = emitindo === tipo

                return (
                  <button
                    key={tipo}
                    type="button"
                    disabled={emitindo !== null}
                    onClick={() => handleEmitir(tipo)}
                    className={`group text-left rounded-xl border border-line border-t-4 ${info.accent} bg-white p-7 transition hover:border-brand-800 hover:shadow-md active:scale-[0.99] disabled:opacity-60 cursor-pointer flex flex-col justify-between min-h-[220px]`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="h-12 w-12 rounded-lg bg-brand-50 text-brand-800 flex items-center justify-center group-hover:bg-brand-800 group-hover:text-white transition">
                        <Icone className="h-6 w-6" />
                      </div>
                      <span
                        className={`font-mono text-xs font-bold px-2.5 py-1 rounded-md border ${info.badge}`}
                      >
                        {tipo}
                      </span>
                    </div>

                    <div className="mt-7 space-y-1.5">
                      <h2 className="text-xl font-bold text-ink">
                        {carregando ? 'Emitindo...' : info.nome}
                      </h2>
                      <p className="text-sm text-slate-600 leading-relaxed">{info.descricao}</p>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}