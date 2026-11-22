import { api } from './api'
import type {
  EstadoSenha,
  FilaAtendimentoResponse,
  PainelResponse,
  Senha,
  TipoSenha,
} from '../types'

export async function emitirSenhaRequest(tipo: TipoSenha): Promise<Senha> {
  const { data } = await api.post<Senha>('/api/senhas/emitir', {
    tipo,
    entrar_fila: true,
  })
  return data
}

export async function obterPainelRequest(): Promise<PainelResponse> {
  const { data } = await api.get<PainelResponse>('/api/senhas/painel')
  return data
}

export async function obterFilaRequest(): Promise<FilaAtendimentoResponse> {
  const { data } = await api.get<FilaAtendimentoResponse>('/api/senhas/fila')
  return data
}

export async function chamarProximaRequest(guiche: string): Promise<Senha> {
  const { data } = await api.post<Senha>('/api/senhas/chamar-proximo', { guiche })
  return data
}

export async function atualizarEstadoRequest(
  senhaId: number,
  estado: EstadoSenha,
  guiche?: string,
): Promise<Senha> {
  const payload: { estado: EstadoSenha; guiche?: string } = { estado }
  if (guiche) payload.guiche = guiche
  const { data } = await api.patch<Senha>(`/api/senhas/${senhaId}/estado`, payload)
  return data
}