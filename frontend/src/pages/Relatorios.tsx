import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  BarChart3,
  Clock,
  Headphones,
  LogOut,
  PowerOff,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import {
  encerrarExpedienteRequest,
  obterAuditoriaSenhasRequest,
  obterRelatorioDiarioRequest,
  obterRelatorioMensalRequest,
} from '../services/relatorioService'
import { formatarHora, INFO_TIPO, LABEL_ESTADO } from '../utils/senhas'
import { BrandLogo } from '../components/BrandLogo'
import type { AuditoriaSenhasResponse, RelatorioResponse, TipoSenha } from '../types'

type ModoPeriodo = 'diario' | 'mensal'
type AbaTabela = 'detalhado' | 'auditoria' | 'por_dia'

function hojeLocal(): string {
  const agora = new Date()
  const ano = agora.getFullYear()
  const mes = String(agora.getMonth() + 1).padStart(2, '0')
  const dia = String(agora.getDate()).padStart(2, '0')
  return `${ano}-${mes}-${dia}`
}

function mesLocal(): string {
  const agora = new Date()
  const ano = agora.getFullYear()
  const mes = String(agora.getMonth() + 1).padStart(2, '0')
  return `${ano}-${mes}`
}

function formatarMinutos(minutos: number | null | undefined): string {
  if (minutos === null || minutos === undefined) return '—'
  return `${minutos.toFixed(1).replace('.', ',')} min`
}

function formatarDataHoraCurta(iso: string | null): string {
  if (!iso) return '—'
  const temFuso = /[zZ]$|[+-]\d{2}:\d{2}$/.test(iso)
  const data = new Date(temFuso ? iso : `${iso}Z`)
  if (Number.isNaN(data.getTime())) return '—'
  const dia = data.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
  return `${dia} ${formatarHora(iso)}`
}

export function Relatorios() {
  const { usuario, logout } = useAuth()
  const navigate = useNavigate()

  const [modo, setModo] = useState<ModoPeriodo>('diario')
  const [dataRef, setDataRef] = useState(hojeLocal)
  const [mesRef, setMesRef] = useState(mesLocal)
  const [aba, setAba] = useState<AbaTabela>('detalhado')

  const [relatorio, setRelatorio] = useState<RelatorioResponse | null>(null)
  const [auditoria, setAuditoria] = useState<AuditoriaSenhasResponse | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [encerrando, setEncerrando] = useState(false)
  const [feedback, setFeedback] = useState<{ tipo: 'erro' | 'sucesso'; texto: string } | null>(null)

  const carregarDados = useCallback(async () => {
    setCarregando(true)
    setFeedback(null)

    try {
      const [dadosRelatorio, dadosAuditoria] = await Promise.all([
        modo === 'diario'
          ? obterRelatorioDiarioRequest(dataRef)
          : obterRelatorioMensalRequest(mesRef),
        obterAuditoriaSenhasRequest(modo === 'diario' ? { data: dataRef } : { mes: mesRef }),
      ])

      setRelatorio(dadosRelatorio)
      setAuditoria(dadosAuditoria)
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        logout()
        navigate('/login', { replace: true })
        return
      }
      const msg =
        axios.isAxiosError(err) && err.response?.data?.erro
          ? err.response.data.erro
          : 'Não foi possível carregar os relatórios.'
      setFeedback({ tipo: 'erro', texto: msg })
    } finally {
      setCarregando(false)
    }
  }, [modo, dataRef, mesRef, logout, navigate])

  useEffect(() => {
    carregarDados()
  }, [carregarDados])

  useEffect(() => {
    if (modo === 'diario' && aba === 'por_dia') {
      setAba('detalhado')
    }
  }, [modo, aba])

  async function handleEncerrarExpediente() {
    setEncerrando(true)
    setFeedback(null)
    try {
      const res = await encerrarExpedienteRequest()
      setFeedback({ tipo: 'sucesso', texto: res.mensagem })
      await carregarDados()
    } catch (err) {
      const msg =
        axios.isAxiosError(err) && err.response?.data?.erro
          ? err.response.data.erro
          : 'Erro ao encerrar expediente.'
      setFeedback({ tipo: 'erro', texto: msg })
    } finally {
      setEncerrando(false)
    }
  }

  function handleSair() {
    logout()
    navigate('/login', { replace: true })
  }

  const tipos: TipoSenha[] = ['SP', 'SE', 'SG']

  return (
    <div className="min-h-screen bg-canvas flex flex-col">
      <header className="border-b border-line bg-white">
        <div className="max-w-7xl mx-auto px-6 h-18 flex items-center justify-between gap-4">
          <Link to="/" className="hover:opacity-90 transition">
            <BrandLogo subtitulo={`Gestão & Auditoria · ${usuario?.nome}`} />
          </Link>

          <div className="flex items-center gap-2.5">
            <Link
              to="/atendimento"
              className="inline-flex items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 text-sm font-medium text-ink hover:border-brand-800 hover:text-brand-800 transition"
            >
              <Headphones className="h-4 w-4" />
              Guichê
            </Link>

            <button
              type="button"
              disabled={encerrando}
              onClick={handleEncerrarExpediente}
              className="inline-flex items-center gap-1.5 rounded-lg border border-amber-300 bg-amber-50 px-3 py-1.5 text-sm font-semibold text-amber-900 hover:bg-amber-100 disabled:opacity-60 transition cursor-pointer"
            >
              <PowerOff className="h-4 w-4" />
              {encerrando ? 'Encerrando...' : 'Encerrar expediente'}
            </button>

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

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <p className="font-mono text-xs font-semibold uppercase tracking-widest text-brand-800">
              Painel Gerencial
            </p>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-ink">
              Relatórios, Indicadores e Auditoria
            </h1>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            <div className="inline-flex rounded-lg border border-line bg-white p-1">
              <button
                type="button"
                onClick={() => setModo('diario')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition cursor-pointer ${
                  modo === 'diario'
                    ? 'bg-brand-800 text-white'
                    : 'text-slate-600 hover:text-ink'
                }`}
              >
                Diário
              </button>
              <button
                type="button"
                onClick={() => setModo('mensal')}
                className={`px-3 py-1.5 text-xs font-semibold rounded-md transition cursor-pointer ${
                  modo === 'mensal'
                    ? 'bg-brand-800 text-white'
                    : 'text-slate-600 hover:text-ink'
                }`}
              >
                Mensal
              </button>
            </div>

            {modo === 'diario' ? (
              <input
                type="date"
                value={dataRef}
                onChange={(e) => setDataRef(e.target.value)}
                className="rounded-lg border border-line bg-white px-3 py-2 text-sm font-mono text-ink outline-none focus:border-brand-800"
              />
            ) : (
              <input
                type="month"
                value={mesRef}
                onChange={(e) => setMesRef(e.target.value)}
                className="rounded-lg border border-line bg-white px-3 py-2 text-sm font-mono text-ink outline-none focus:border-brand-800"
              />
            )}

            <button
              type="button"
              onClick={carregarDados}
              className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-white px-3 py-2 text-sm font-medium text-ink hover:border-brand-800 hover:text-brand-800 transition cursor-pointer"
            >
              <RefreshCw className={`h-4 w-4 ${carregando ? 'animate-spin' : ''}`} />
              Atualizar
            </button>
          </div>
        </div>

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

        {relatorio && (
          <>
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="rounded-xl border border-line bg-white p-5">
                <span className="font-mono text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Senhas emitidas
                </span>
                <p className="text-3xl font-bold font-mono text-ink mt-2">
                  {relatorio.totais.emitidas}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Em aberto: {relatorio.totais.nao_finalizadas}
                </p>
              </div>

              <div className="rounded-xl border border-line bg-white p-5">
                <span className="font-mono text-xs font-semibold uppercase tracking-wider text-brand-800">
                  Senhas atendidas
                </span>
                <p className="text-3xl font-bold font-mono text-brand-800 mt-2">
                  {relatorio.totais.atendidas}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Taxa de atendimento: {relatorio.indicadores.taxa_atendimento_percentual}%
                </p>
              </div>

              <div className="rounded-xl border border-line bg-white p-5">
                <span className="font-mono text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Não compareceu / descarte
                </span>
                <p className="text-3xl font-bold font-mono text-ink mt-2">
                  {relatorio.totais.nao_compareceu}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Taxa de abandono: {relatorio.indicadores.taxa_nao_comparecimento_percentual}%
                </p>
              </div>

              <div className="rounded-xl border border-line bg-brand-950 text-white p-5">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold uppercase tracking-wider text-brand-400">
                    TM Geral
                  </span>
                  <Clock className="h-4 w-4 text-brand-400" />
                </div>
                <p className="text-3xl font-bold font-mono mt-2">
                  {formatarMinutos(relatorio.tempo_medio.geral.atendimento.minutos)}
                </p>
                <p className="text-xs text-slate-300 mt-1">
                  Espera média: {formatarMinutos(relatorio.tempo_medio.geral.espera.minutos)}
                </p>
              </div>
            </section>

            <section className="grid grid-cols-1 lg:grid-cols-12 gap-5">
              <div className="lg:col-span-7 rounded-xl border border-line bg-white p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-line pb-3">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="h-4 w-4 text-brand-800" />
                    <h2 className="text-sm font-bold text-ink">
                      Quantitativo e Tempo Médio (TM) por Prioridade
                    </h2>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead>
                      <tr className="border-b border-line text-xs font-mono uppercase text-slate-500">
                        <th className="py-2.5 pr-3">Tipo</th>
                        <th className="py-2.5 px-3">Emitidas</th>
                        <th className="py-2.5 px-3">Atendidas</th>
                        <th className="py-2.5 px-3">Abandono</th>
                        <th className="py-2.5 px-3">TM Atend.</th>
                        <th className="py-2.5 pl-3">Espera</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line/70">
                      {tipos.map((tipo) => (
                        <tr key={tipo}>
                          <td className="py-3 pr-3">
                            <span
                              className={`font-mono text-xs font-bold px-2 py-0.5 rounded-md border ${INFO_TIPO[tipo].badge}`}
                            >
                              {tipo}
                            </span>
                            <span className="ml-2 text-xs text-slate-600">
                              {INFO_TIPO[tipo].nome}
                            </span>
                          </td>
                          <td className="py-3 px-3 font-mono font-semibold text-ink">
                            {relatorio.por_tipo[tipo].emitidas}
                          </td>
                          <td className="py-3 px-3 font-mono font-semibold text-brand-800">
                            {relatorio.por_tipo[tipo].atendidas}
                          </td>
                          <td className="py-3 px-3 font-mono text-slate-600">
                            {relatorio.por_tipo[tipo].nao_compareceu}
                          </td>
                          <td className="py-3 px-3 font-mono font-semibold text-ink">
                            {formatarMinutos(relatorio.tempo_medio[tipo].atendimento.minutos)}
                          </td>
                          <td className="py-3 pl-3 font-mono text-slate-600">
                            {formatarMinutos(relatorio.tempo_medio[tipo].espera.minutos)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="lg:col-span-5 rounded-xl border border-line bg-white p-6 space-y-5">
                <div className="flex items-center gap-2 border-b border-line pb-3">
                  <ShieldCheck className="h-4 w-4 text-brand-800" />
                  <h2 className="text-sm font-bold text-ink">Desempenho por Guichê e Atendente</h2>
                </div>

                <div className="space-y-4">
                  <div>
                    <p className="font-mono text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-2">
                      Por Guichê
                    </p>
                    {relatorio.indicadores.por_guiche.length === 0 ? (
                      <p className="text-xs text-slate-400">Sem movimentação no período.</p>
                    ) : (
                      <div className="grid grid-cols-2 gap-2">
                        {relatorio.indicadores.por_guiche.map((g) => (
                          <div
                            key={g.guiche}
                            className="rounded-lg border border-line bg-canvas/60 px-3 py-2 flex items-center justify-between"
                          >
                            <span className="font-mono text-xs font-bold text-brand-800">
                              {g.guiche}
                            </span>
                            <span className="font-mono text-xs text-ink">
                              <strong>{g.atendidas}</strong>/{g.total}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div>
                    <p className="font-mono text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-2">
                      Por Atendente
                    </p>
                    {relatorio.indicadores.por_atendente.length === 0 ? (
                      <p className="text-xs text-slate-400">Sem atendimentos registrados.</p>
                    ) : (
                      <div className="divide-y divide-line/70 border border-line rounded-lg">
                        {relatorio.indicadores.por_atendente.map((a) => (
                          <div
                            key={a.usuario_id}
                            className="px-3 py-2 flex items-center justify-between text-xs"
                          >
                            <span className="font-medium text-ink">{a.atendente}</span>
                            <span className="font-mono text-slate-600">
                              <strong className="text-brand-800">{a.atendidas}</strong> atendidas ·{' '}
                              {a.nao_compareceu} ausentes
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </section>

            <section className="rounded-xl border border-line bg-white overflow-hidden">
              <div className="px-6 pt-4 border-b border-line flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => setAba('detalhado')}
                  className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition cursor-pointer ${
                    aba === 'detalhado'
                      ? 'border-brand-800 text-brand-800'
                      : 'border-transparent text-slate-500 hover:text-ink'
                  }`}
                >
                  Detalhado por Senha ({relatorio.detalhado.length})
                </button>

                <button
                  type="button"
                  onClick={() => setAba('auditoria')}
                  className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition cursor-pointer ${
                    aba === 'auditoria'
                      ? 'border-brand-800 text-brand-800'
                      : 'border-transparent text-slate-500 hover:text-ink'
                  }`}
                >
                  Auditoria de Chamadas ({auditoria?.total ?? 0})
                </button>

                {modo === 'mensal' && (
                  <button
                    type="button"
                    onClick={() => setAba('por_dia')}
                    className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition cursor-pointer ${
                      aba === 'por_dia'
                        ? 'border-brand-800 text-brand-800'
                        : 'border-transparent text-slate-500 hover:text-ink'
                    }`}
                  >
                    Consolidado por Dia ({relatorio.por_dia?.length ?? 0})
                  </button>
                )}
              </div>

              <div className="overflow-x-auto">
                {aba === 'detalhado' && (
                  <table className="w-full text-sm text-left">
                    <thead>
                      <tr className="bg-canvas/70 border-b border-line text-xs font-mono uppercase text-slate-500">
                        <th className="py-3 px-6">Numeração</th>
                        <th className="py-3 px-4">Tipo</th>
                        <th className="py-3 px-4">Estado</th>
                        <th className="py-3 px-4">Emissão</th>
                        <th className="py-3 px-4">Atendimento</th>
                        <th className="py-3 px-6">Guichê</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line/70">
                      {relatorio.detalhado.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="py-10 text-center text-slate-400">
                            Nenhuma senha registrada neste período.
                          </td>
                        </tr>
                      ) : (
                        relatorio.detalhado.map((item) => (
                          <tr key={item.senha_id} className="hover:bg-canvas/40">
                            <td className="py-3 px-6 font-mono font-bold text-ink">
                              {item.numero}
                            </td>
                            <td className="py-3 px-4">
                              <span
                                className={`font-mono text-xs font-bold px-2 py-0.5 rounded-md border ${INFO_TIPO[item.tipo].badge}`}
                              >
                                {item.tipo}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-xs font-medium text-slate-700">
                              {LABEL_ESTADO[item.estado_atual]}
                            </td>
                            <td className="py-3 px-4 font-mono text-xs text-slate-600">
                              {formatarDataHoraCurta(item.data_emissao)}
                            </td>
                            <td className="py-3 px-4 font-mono text-xs text-slate-600">
                              {formatarDataHoraCurta(item.data_atendimento)}
                            </td>
                            <td className="py-3 px-6 font-mono text-xs font-bold text-brand-800">
                              {item.guiche ?? '—'}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                )}

                {aba === 'auditoria' && (
                  <table className="w-full text-sm text-left">
                    <thead>
                      <tr className="bg-canvas/70 border-b border-line text-xs font-mono uppercase text-slate-500">
                        <th className="py-3 px-6">Senha</th>
                        <th className="py-3 px-4">Atendente</th>
                        <th className="py-3 px-4">Guichê</th>
                        <th className="py-3 px-4">1ª Chamada</th>
                        <th className="py-3 px-4">2ª Chamada</th>
                        <th className="py-3 px-4">Início</th>
                        <th className="py-3 px-6">Fim</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line/70">
                      {!auditoria || auditoria.registros.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-10 text-center text-slate-400">
                            Nenhum registro de auditoria neste período.
                          </td>
                        </tr>
                      ) : (
                        auditoria.registros.map((reg) => (
                          <tr key={reg.senha_id} className="hover:bg-canvas/40">
                            <td className="py-3 px-6 font-mono font-bold text-ink">{reg.senha}</td>
                            <td className="py-3 px-4 text-xs text-slate-700">
                              {reg.atendente ?? '—'}
                            </td>
                            <td className="py-3 px-4 font-mono text-xs font-bold text-brand-800">
                              {reg.guiche ?? '—'}
                            </td>
                            <td className="py-3 px-4 font-mono text-xs text-slate-600">
                              {reg.primeira_chamada ? formatarHora(reg.primeira_chamada) : '—'}
                            </td>
                            <td className="py-3 px-4 font-mono text-xs text-slate-600">
                              {reg.segunda_chamada ? formatarHora(reg.segunda_chamada) : '—'}
                            </td>
                            <td className="py-3 px-4 font-mono text-xs text-slate-600">
                              {reg.inicio_atendimento ? formatarHora(reg.inicio_atendimento) : '—'}
                            </td>
                            <td className="py-3 px-6 font-mono text-xs text-slate-600">
                              {reg.fim_atendimento ? formatarHora(reg.fim_atendimento) : '—'}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                )}

                {aba === 'por_dia' && modo === 'mensal' && (
                  <table className="w-full text-sm text-left">
                    <thead>
                      <tr className="bg-canvas/70 border-b border-line text-xs font-mono uppercase text-slate-500">
                        <th className="py-3 px-6">Data</th>
                        <th className="py-3 px-4">Emitidas</th>
                        <th className="py-3 px-4">Atendidas</th>
                        <th className="py-3 px-4">Não compareceu</th>
                        <th className="py-3 px-6">Em aberto</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line/70">
                      {(relatorio.por_dia ?? []).length === 0 ? (
                        <tr>
                          <td colSpan={5} className="py-10 text-center text-slate-400">
                            Nenhum dia com registros neste mês.
                          </td>
                        </tr>
                      ) : (
                        (relatorio.por_dia ?? []).map((dia) => (
                          <tr key={dia.data} className="hover:bg-canvas/40">
                            <td className="py-3 px-6 font-mono font-bold text-ink">{dia.data}</td>
                            <td className="py-3 px-4 font-mono">{dia.emitidas}</td>
                            <td className="py-3 px-4 font-mono font-semibold text-brand-800">
                              {dia.atendidas}
                            </td>
                            <td className="py-3 px-4 font-mono text-slate-600">
                              {dia.nao_compareceu}
                            </td>
                            <td className="py-3 px-6 font-mono text-slate-600">
                              {dia.nao_finalizadas}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                )}
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  )
}