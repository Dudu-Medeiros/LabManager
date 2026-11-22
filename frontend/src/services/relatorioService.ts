import { api } from './api'
import type {
  AuditoriaSenhasResponse,
  EncerrarExpedienteResponse,
  RelatorioResponse,
} from '../types'

export async function obterRelatorioDiarioRequest(data?: string): Promise<RelatorioResponse> {
  const params = data ? { data } : undefined
  const { data: resposta } = await api.get<RelatorioResponse>('/api/relatorios/diario', { params })
  return resposta
}

export async function obterRelatorioMensalRequest(mes?: string): Promise<RelatorioResponse> {
  const params = mes ? { mes } : undefined
  const { data: resposta } = await api.get<RelatorioResponse>('/api/relatorios/mensal', { params })
  return resposta
}

export async function obterAuditoriaSenhasRequest(
  filtros: { data?: string; mes?: string },
): Promise<AuditoriaSenhasResponse> {
  const { data } = await api.get<AuditoriaSenhasResponse>('/api/relatorios/auditoria/senhas', {
    params: filtros,
  })
  return data
}

export async function encerrarExpedienteRequest(): Promise<EncerrarExpedienteResponse> {
  const { data } = await api.post<EncerrarExpedienteResponse>('/api/senhas/encerrar-expediente')
  return data
}