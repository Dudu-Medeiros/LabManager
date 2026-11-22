import type { EstadoSenha, TipoSenha } from '../types'

export const INFO_TIPO: Record<
  TipoSenha,
  { nome: string; descricao: string; badge: string; accent: string }
> = {
  SP: {
    nome: 'Prioritária',
    descricao: 'Idosos, gestantes, lactantes e pessoas com deficiência',
    badge: 'bg-amber-50 text-amber-800 border-amber-300/80',
    accent: 'border-t-amber-500',
  },
  SE: {
    nome: 'Retirada de Exames',
    descricao: 'Entrega rápida de resultados e laudos laboratoriais',
    badge: 'bg-brand-100 text-brand-800 border-brand-500/30',
    accent: 'border-t-brand-800',
  },
  SG: {
    nome: 'Atendimento Geral',
    descricao: 'Coletas, cadastros e agendamentos em geral',
    badge: 'bg-slate-100 text-slate-700 border-slate-300/80',
    accent: 'border-t-slate-600',
  },
}

export const LABEL_ESTADO: Record<EstadoSenha, string> = {
  EMITIDA: 'Emitida',
  AGUARDANDO: 'Aguardando',
  CHAMADA: 'Chamada',
  CHAMADA_NOVAMENTE: 'Rechamada',
  EM_ATENDIMENTO: 'Em atendimento',
  ATENDIDA: 'Atendida',
  NAO_COMPARECEU: 'Não compareceu',
}

export function formatarHora(iso: string): string {
  const temFuso = /[zZ]$|[+-]\d{2}:\d{2}$/.test(iso)
  const data = new Date(temFuso ? iso : `${iso}Z`)
  if (Number.isNaN(data.getTime())) return '--:--'
  return data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}