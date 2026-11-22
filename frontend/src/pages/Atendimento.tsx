import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  CheckCircle2,
  LogOut,
  Megaphone,
  Play,
  RefreshCw,
  Repeat,
  UserX,
} from 'lucide-react'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import {
  atualizarEstadoRequest,
  chamarProximaRequest,
  obterFilaRequest,
} from '../services/senhaService'
import { formatarHora, INFO_TIPO, LABEL_ESTADO } from '../utils/senhas'
import { BrandLogo } from '../components/BrandLogo'
import type { EstadoSenha, FilaAtendimentoResponse, Senha } from '../types'

const GUICHES = ['G01', 'G02', 'G03', 'G04']
const GUICHE_KEY = 'labmanager_guiche'

export function Atendimento() {
  const { usuario, logout } = useAuth()
  const navigate = useNavigate()

  const [guiche, setGuiche] = useState(() => localStorage.getItem(GUICHE_KEY) || 'G01')
  const [fila, setFila] = useState<FilaAtendimentoResponse>({ aguardando: [], em_andamento: [] })
  const [senhaAtual, setSenhaAtual] = useState<Senha | null>(null)
  const [ocupado, setOcupado] = useState(false)
  const [feedback, setFeedback] = useState<{ tipo: 'erro' | 'sucesso'; texto: string } | null>(null)

  function extrairErro(err: unknown, padrao: string): string {
    if (axios.isAxiosError(err) && err.response?.data?.erro) {
      return err.response.data.erro
    }
    return padrao
  }

  const carregarFila = useCallback(async () => {
    try {
      const dados = await obterFilaRequest()
      setFila(dados)

      if (usuario) {
        const minhaSenha = dados.em_andamento.find((s) => s.usuario_id === usuario.id) ?? null
        setSenhaAtual(minhaSenha)
      }
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        logout()
        navigate('/login', { replace: true })
      }
    }
  }, [usuario, logout, navigate])

  useEffect(() => {
    carregarFila()
    const intervalo = window.setInterval(carregarFila, 4000)
    return () => window.clearInterval(intervalo)
  }, [carregarFila])

  function handleTrocarGuiche(novo: string) {
    setGuiche(novo)
    localStorage.setItem(GUICHE_KEY, novo)
  }

  async function handleChamarProxima() {
    setFeedback(null)
    setOcupado(true)

    try {
      const chamada = await chamarProximaRequest(guiche)
      setSenhaAtual(chamada)
      setFeedback({ tipo: 'sucesso', texto: `Senha ${chamada.numero} chamada no guichê ${guiche}.` })
      await carregarFila()
    } catch (err) {
      setFeedback({ tipo: 'erro', texto: extrairErro(err, 'Erro ao chamar próxima senha.') })
    } finally {
      setOcupado(false)
    }
  }

  async function handleTransicao(novoEstado: EstadoSenha) {
    if (!senhaAtual) return
    setFeedback(null)
    setOcupado(true)

    try {
      const atualizada = await atualizarEstadoRequest(senhaAtual.id, novoEstado, guiche)
      if (novoEstado === 'ATENDIDA' || novoEstado === 'NAO_COMPARECEU') {
        setSenhaAtual(null)
        setFeedback({
          tipo: 'sucesso',
          texto: `Senha ${atualizada.numero} encerrada como ${LABEL_ESTADO[novoEstado]}.`,
        })
      } else {
        setSenhaAtual(atualizada)
        setFeedback({
          tipo: 'sucesso',
          texto: `Senha ${atualizada.numero} atualizada para ${LABEL_ESTADO[novoEstado]}.`,
        })
      }
      await carregarFila()
    } catch (err) {
      setFeedback({ tipo: 'erro', texto: extrairErro(err, 'Não foi possível alterar o estado.') })
      await carregarFila()
    } finally {
      setOcupado(false)
    }
  }

  function handleSair() {
    logout()
    navigate('/login', { replace: true })
  }

  const contagem = {
    SP: fila.aguardando.filter((s) => s.tipo === 'SP').length,
    SE: fila.aguardando.filter((s) => s.tipo === 'SE').length,
    SG: fila.aguardando.filter((s) => s.tipo === 'SG').length,
  }

  return (
    <div className="min-h-screen bg-canvas flex flex-col">
      <header className="border-b border-line bg-white">
        <div className="max-w-6xl mx-auto px-6 h-18 flex items-center justify-between gap-4">
          <Link to="/" className="hover:opacity-90 transition">
            <BrandLogo subtitulo={`${usuario?.nome} · ${usuario?.perfil}`} />
          </Link>

          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Guichê
              <select
                value={guiche}
                onChange={(e) => handleTrocarGuiche(e.target.value)}
                className="rounded-lg border border-line bg-brand-50 px-3 py-1.5 text-sm font-mono font-bold text-brand-800 outline-none focus:border-brand-800"
              >
                {GUICHES.map((g) => (
                  <option key={g} value={g}>
                    {g}
                  </option>
                ))}
              </select>
            </label>

            <button
              type="button"
              onClick={handleSair}
              className="inline-flex items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-canvas hover:text-ink transition cursor-pointer"
            >
              <LogOut className="h-4 w-4" />
              Sair
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-12 gap-6">
        <section className="lg:col-span-8 space-y-5">
          {feedback && (
            <div
              className={`rounded-lg border px-4 py-3 text-sm font-medium ${
                feedback.tipo === 'erro'
                  ? 'border-red-200 bg-red-50 text-red-700'
                  : 'border-brand-500/30 bg-brand-50 text-brand-800'
              }`}
            >
              {feedback.texto}
            </div>
          )}

          <div className="rounded-xl border border-line bg-white overflow-hidden">
            {senhaAtual ? (
              <div>
                <div className="bg-brand-950 text-white px-6 py-4 flex flex-wrap items-center justify-between gap-3">
                  <span className="font-mono text-xs uppercase tracking-widest text-brand-400 font-semibold">
                    Guichê {senhaAtual.guiche || guiche} · Atendimento Ativo
                  </span>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-brand-800 text-brand-100 border border-brand-500/30">
                    {LABEL_ESTADO[senhaAtual.estado_atual]}
                  </span>
                </div>

                <div className="p-6 sm:p-8 space-y-7">
                  <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line pb-6">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                        Senha em operação
                      </p>
                      <p className="text-4xl sm:text-5xl font-bold font-mono text-ink mt-1">
                        {senhaAtual.numero}
                      </p>
                    </div>

                    <span
                      className={`text-xs font-semibold px-3 py-1.5 rounded-md border ${
                        INFO_TIPO[senhaAtual.tipo].badge
                      }`}
                    >
                      {senhaAtual.tipo} · {INFO_TIPO[senhaAtual.tipo].nome}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {senhaAtual.estado_atual === 'CHAMADA' && (
                      <button
                        type="button"
                        disabled={ocupado}
                        onClick={() => handleTransicao('CHAMADA_NOVAMENTE')}
                        className="inline-flex items-center justify-center gap-2 rounded-lg border border-line bg-white px-4 py-3 text-sm font-semibold text-ink hover:border-brand-800 hover:text-brand-800 disabled:opacity-60 transition cursor-pointer"
                      >
                        <Repeat className="h-4 w-4" />
                        Chamar novamente
                      </button>
                    )}

                    {(senhaAtual.estado_atual === 'CHAMADA' ||
                      senhaAtual.estado_atual === 'CHAMADA_NOVAMENTE') && (
                      <>
                        <button
                          type="button"
                          disabled={ocupado}
                          onClick={() => handleTransicao('EM_ATENDIMENTO')}
                          className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-800 px-4 py-3 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60 transition cursor-pointer"
                        >
                          <Play className="h-4 w-4" />
                          Iniciar atendimento
                        </button>

                        <button
                          type="button"
                          disabled={ocupado}
                          onClick={() => handleTransicao('NAO_COMPARECEU')}
                          className="inline-flex items-center justify-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700 hover:bg-red-100 disabled:opacity-60 transition cursor-pointer"
                        >
                          <UserX className="h-4 w-4" />
                          Não compareceu
                        </button>
                      </>
                    )}

                    {senhaAtual.estado_atual === 'EM_ATENDIMENTO' && (
                      <button
                        type="button"
                        disabled={ocupado}
                        onClick={() => handleTransicao('ATENDIDA')}
                        className="sm:col-span-3 inline-flex items-center justify-center gap-2 rounded-lg bg-brand-800 px-4 py-3.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60 transition cursor-pointer"
                      >
                        <CheckCircle2 className="h-5 w-5 text-brand-400" />
                        Finalizar atendimento
                      </button>
                    )}
                  </div>

                  {senhaAtual.historico && senhaAtual.historico.length > 0 && (
                    <div className="pt-5 border-t border-line">
                      <p className="text-[11px] font-mono font-semibold uppercase tracking-widest text-slate-400 mb-3">
                        Linha do tempo
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {senhaAtual.historico.map((h) => (
                          <span
                            key={h.id}
                            className="font-mono text-xs px-2.5 py-1 rounded-md bg-canvas border border-line text-slate-700"
                          >
                            {LABEL_ESTADO[h.estado]} · {formatarHora(h.data_hora)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-10 sm:p-12 text-center space-y-6">
                <div className="mx-auto h-14 w-14 rounded-xl bg-brand-50 border border-brand-500/20 text-brand-800 flex items-center justify-center">
                  <Megaphone className="h-7 w-7" />
                </div>

                <div className="space-y-1.5">
                  <p className="font-mono text-xs font-semibold uppercase tracking-widest text-brand-800">
                    Pronto para atendimento
                  </p>
                  <h2 className="text-2xl font-bold text-ink">Guichê {guiche} livre</h2>
                  <p className="text-sm text-slate-600">
                    {fila.aguardando.length > 0
                      ? `${fila.aguardando.length} senha(s) aguardando na fila.`
                      : 'Nenhuma senha aguardando atendimento no momento.'}
                  </p>
                </div>

                <button
                  type="button"
                  disabled={ocupado || fila.aguardando.length === 0}
                  onClick={handleChamarProxima}
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-800 px-7 py-3.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-45 transition cursor-pointer"
                >
                  <Megaphone className="h-4 w-4" />
                  {ocupado ? 'Chamando...' : 'Chamar próxima senha'}
                </button>
              </div>
            )}
          </div>
        </section>

        <aside className="lg:col-span-4 rounded-xl border border-line bg-white p-6 flex flex-col">
          <div className="flex items-center justify-between pb-4 border-b border-line">
            <div>
              <h2 className="text-sm font-bold text-ink">Fila Aguardando</h2>
              <p className="text-xs text-slate-500">Priorização automática SP / SE / SG</p>
            </div>
            <button
              type="button"
              onClick={carregarFila}
              className="p-2 rounded-lg text-slate-500 hover:bg-brand-50 hover:text-brand-800 transition cursor-pointer"
              title="Atualizar fila"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2 py-4 border-b border-line">
            {(['SP', 'SE', 'SG'] as const).map((tipo) => (
              <div
                key={tipo}
                className="rounded-lg bg-canvas border border-line/80 p-2.5 text-center"
              >
                <span className="font-mono text-[11px] font-bold text-brand-800 block">{tipo}</span>
                <span className="text-lg font-bold font-mono text-ink">{contagem[tipo]}</span>
              </div>
            ))}
          </div>

          <div className="flex-1 divide-y divide-line/70 mt-2 max-h-[420px] overflow-y-auto">
            {fila.aguardando.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-10">Fila vazia.</p>
            ) : (
              fila.aguardando.map((s) => (
                <div key={s.id} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-bold font-mono text-ink">{s.numero}</p>
                    <p className="text-xs text-slate-500">Emitida às {formatarHora(s.data_emissao)}</p>
                  </div>
                  <span
                    className={`font-mono text-[11px] font-bold px-2 py-0.5 rounded-md border ${
                      INFO_TIPO[s.tipo].badge
                    }`}
                  >
                    {s.tipo}
                  </span>
                </div>
              ))
            )}
          </div>
        </aside>
      </main>
    </div>
  )
}