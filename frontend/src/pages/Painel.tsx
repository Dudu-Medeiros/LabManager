import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, BellRing, Clock, Volume2, VolumeX } from 'lucide-react'
import { obterPainelRequest } from '../services/senhaService'
import { formatarHora, INFO_TIPO } from '../utils/senhas'
import { BrandLogo } from '../components/BrandLogo'
import type { PainelResponse } from '../types'

function tocarAlertaSonoro() {
  try {
    const AudioCtx =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
    const ctx = new AudioCtx()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(880, ctx.currentTime)
    osc.frequency.setValueAtTime(660, ctx.currentTime + 0.16)
    gain.gain.setValueAtTime(0.12, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.45)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start()
    osc.stop(ctx.currentTime + 0.45)
  } catch {
    return
  }
}

export function Painel() {
  const [painel, setPainel] = useState<PainelResponse | null>(null)
  const [erro, setErro] = useState(false)
  const [somAtivo, setSomAtivo] = useState(false)
  const [destaque, setDestaque] = useState(false)
  const [relogio, setRelogio] = useState(() =>
    new Date().toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }),
  )

  const ultimoEventoRef = useRef<number | null>(null)
  const somAtivoRef = useRef(somAtivo)
  somAtivoRef.current = somAtivo

  useEffect(() => {
    const timer = window.setInterval(() => {
      setRelogio(
        new Date().toLocaleTimeString('pt-BR', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        }),
      )
    }, 1000)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    let ativo = true

    async function atualizar() {
      try {
        const dados = await obterPainelRequest()
        if (!ativo) return
        setErro(false)
        setPainel(dados)

        const novoEventoId = dados.chamada_atual?.evento_id ?? null
        if (
          novoEventoId !== null &&
          ultimoEventoRef.current !== null &&
          novoEventoId !== ultimoEventoRef.current
        ) {
          setDestaque(true)
          if (somAtivoRef.current) tocarAlertaSonoro()
          window.setTimeout(() => setDestaque(false), 3000)
        }
        ultimoEventoRef.current = novoEventoId
      } catch {
        if (ativo) setErro(true)
      }
    }

    atualizar()
    const intervalo = window.setInterval(atualizar, 3000)
    return () => {
      ativo = false
      window.clearInterval(intervalo)
    }
  }, [])

  const atual = painel?.chamada_atual ?? null
  const historico = (painel?.ultimas_chamadas ?? []).filter(
    (item, idx, arr) =>
      item.senha_id !== atual?.senha_id &&
      arr.findIndex((outro) => outro.senha_id === item.senha_id) === idx,
  )

  return (
    <div className="min-h-screen bg-brand-950 text-white flex flex-col">
      <header className="border-b border-brand-800/50 bg-brand-900/50">
        <div className="max-w-7xl mx-auto px-6 h-18 flex items-center justify-between">
          <BrandLogo tema="escuro" subtitulo="Painel de Chamada" />

          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => setSomAtivo((v) => !v)}
              className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border transition cursor-pointer ${
                somAtivo
                  ? 'border-brand-400/50 bg-brand-800/60 text-brand-400'
                  : 'border-brand-800/70 text-slate-300 hover:text-white hover:border-brand-500/60'
              }`}
            >
              {somAtivo ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
              {somAtivo ? 'Som ativo' : 'Ativar som'}
            </button>

            <div className="hidden sm:flex items-center gap-2 text-sm font-mono text-brand-100 bg-brand-900/80 border border-brand-800/60 px-3 py-1.5 rounded-lg">
              <Clock className="h-4 w-4 text-brand-400" />
              {relogio}
            </div>

            <Link
              to="/"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-white transition"
            >
              <ArrowLeft className="h-4 w-4" />
              Início
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-12 gap-6">
        <section className="lg:col-span-8 flex flex-col justify-between gap-5">
          <div
            className={`flex-1 rounded-2xl border p-8 sm:p-12 flex flex-col justify-center items-center text-center transition duration-500 ${
              destaque
                ? 'bg-brand-800/80 border-brand-400 shadow-lg shadow-brand-400/15'
                : 'bg-brand-900/55 border-brand-800/60'
            }`}
          >
            {erro ? (
              <p className="text-red-300 text-sm">
                Sem comunicação com o servidor. Tentando reconectar...
              </p>
            ) : atual ? (
              <div className="space-y-8 w-full max-w-2xl">
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-md bg-brand-950/70 border border-brand-400/30 text-brand-400 text-xs font-mono font-semibold uppercase tracking-widest">
                  <BellRing className="h-4 w-4" />
                  {atual.estado_evento === 'CHAMADA_NOVAMENTE'
                    ? 'Chamando novamente'
                    : 'Senha chamada'}
                </div>

                <p className="text-5xl sm:text-7xl lg:text-[84px] font-bold tracking-tight font-mono text-white leading-none">
                  {atual.numero}
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 max-w-lg mx-auto">
                  <div className="rounded-xl bg-brand-400 text-brand-950 px-6 py-4 text-left">
                    <span className="block text-[11px] font-mono font-bold uppercase tracking-widest text-brand-900/80">
                      Guichê
                    </span>
                    <span className="text-3xl sm:text-4xl font-bold font-mono">{atual.guiche}</span>
                  </div>

                  <div className="rounded-xl bg-brand-950/70 border border-brand-800/80 px-6 py-4 text-left flex flex-col justify-center">
                    <span className="block text-[11px] font-mono font-semibold uppercase tracking-widest text-slate-400">
                      Categoria · {atual.tipo}
                    </span>
                    <span className="text-lg font-semibold text-white mt-0.5">
                      {INFO_TIPO[atual.tipo].nome}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-2xl font-bold text-brand-100">Aguardando próxima chamada</p>
                <p className="text-sm text-slate-400">
                  As senhas chamadas pelos guichês aparecerão automaticamente aqui.
                </p>
              </div>
            )}
          </div>

          <div className="grid grid-cols-3 gap-4">
            {(['SP', 'SE', 'SG'] as const).map((tipo) => (
              <div
                key={tipo}
                className="rounded-xl bg-brand-900/55 border border-brand-800/60 px-5 py-4 flex items-center justify-between"
              >
                <div>
                  <span className="font-mono text-xs font-bold text-brand-400 block">{tipo}</span>
                  <span className="text-xs sm:text-sm text-slate-300">{INFO_TIPO[tipo].nome}</span>
                </div>
                <span className="text-2xl font-bold font-mono text-white">
                  {painel?.aguardando[tipo] ?? 0}
                </span>
              </div>
            ))}
          </div>
        </section>

        <aside className="lg:col-span-4 rounded-2xl bg-brand-900/55 border border-brand-800/60 p-6 flex flex-col">
          <div className="flex items-center justify-between pb-4 border-b border-brand-800/60">
            <h2 className="text-xs font-mono font-semibold uppercase tracking-widest text-brand-400">
              Últimas chamadas
            </h2>
            <span className="font-mono text-xs text-slate-400">
              Na fila: {painel?.aguardando.total ?? 0}
            </span>
          </div>

          <div className="flex-1 divide-y divide-brand-800/50 mt-2">
            {historico.length === 0 ? (
              <p className="text-sm text-slate-400 py-10 text-center">
                Nenhuma chamada anterior hoje.
              </p>
            ) : (
              historico.map((item) => (
                <div key={item.evento_id} className="py-4 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xl font-bold font-mono text-white">{item.numero}</p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {INFO_TIPO[item.tipo].nome} · {formatarHora(item.data_hora)}
                    </p>
                  </div>
                  <div className="rounded-lg bg-brand-950/80 border border-brand-800/70 px-3 py-1.5 text-center min-w-[64px]">
                    <span className="text-[10px] font-mono uppercase text-slate-400 block">
                      Guichê
                    </span>
                    <span className="text-base font-bold font-mono text-brand-400">
                      {item.guiche}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </aside>
      </main>
    </div>
  )
}