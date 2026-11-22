export type TipoSenha = 'SP' | 'SE' | 'SG'

export type EstadoSenha =
  | 'EMITIDA'
  | 'AGUARDANDO'
  | 'CHAMADA'
  | 'CHAMADA_NOVAMENTE'
  | 'EM_ATENDIMENTO'
  | 'ATENDIDA'
  | 'NAO_COMPARECEU'

export type PerfilUsuario = 'ATENDENTE' | 'GESTOR'

export interface Usuario {
  id: number
  nome: string
  email: string
  perfil: PerfilUsuario
}

export interface HistoricoItem {
  id: number
  estado: EstadoSenha
  data_hora: string
  usuario_id: number | null
}

export interface Senha {
  id: number
  numero: string
  tipo: TipoSenha
  estado_atual: EstadoSenha
  data_emissao: string
  guiche: string | null
  versao: number
  usuario_id: number | null
  fila_id: number | null
  paciente_id: number | null
  historico?: HistoricoItem[]
}

export interface ChamadaPainel {
  evento_id: number
  senha_id: number
  numero: string
  tipo: TipoSenha
  prioridade: TipoSenha
  sequencial: string
  guiche: string
  estado_evento: 'CHAMADA' | 'CHAMADA_NOVAMENTE'
  estado_atual: EstadoSenha
  ultima_chamada: boolean
  data_hora: string
}

export interface PainelResponse {
  chamada_atual: ChamadaPainel | null
  ultimas_chamadas: ChamadaPainel[]
  aguardando: {
    SP: number
    SE: number
    SG: number
    total: number
  }
}

export interface FilaAtendimentoResponse {
  aguardando: Senha[]
  em_andamento: Senha[]
}

export interface RelatorioTotais {
  emitidas: number
  atendidas: number
  nao_compareceu: number
  nao_finalizadas: number
}

export interface MediaTempo {
  amostras: number
  segundos: number | null
  minutos: number | null
}

export interface TempoMedioBloco {
  atendimento: MediaTempo
  espera: MediaTempo
}

export interface IndicadorGuiche {
  guiche: string
  atendidas: number
  nao_compareceu: number
  total: number
}

export interface IndicadorAtendente {
  usuario_id: number
  atendente: string
  atendidas: number
  nao_compareceu: number
  total: number
}

export interface SenhaDetalhadaItem {
  senha_id: number
  numero: string
  tipo: TipoSenha
  estado_atual: EstadoSenha
  data_emissao: string | null
  data_atendimento: string | null
  guiche: string | null
}

export interface RelatorioPorDiaItem extends RelatorioTotais {
  data: string
}

export interface RelatorioResponse {
  periodo: {
    tipo: 'diario' | 'mensal'
    data?: string
    mes?: string
  }
  totais: RelatorioTotais
  por_tipo: Record<TipoSenha, RelatorioTotais>
  tempo_medio: Record<TipoSenha | 'geral', TempoMedioBloco>
  indicadores: {
    taxa_atendimento_percentual: number
    taxa_nao_comparecimento_percentual: number
    por_guiche: IndicadorGuiche[]
    por_atendente: IndicadorAtendente[]
  }
  detalhado: SenhaDetalhadaItem[]
  por_dia?: RelatorioPorDiaItem[]
}

export interface AuditoriaSenhaItem {
  senha_id: number
  senha: string
  tipo: TipoSenha
  estado_atual: EstadoSenha
  atendente: string | null
  guiche: string | null
  primeira_chamada: string | null
  segunda_chamada: string | null
  inicio_atendimento: string | null
  fim_atendimento: string | null
}

export interface AuditoriaSenhasResponse {
  periodo: {
    tipo: 'diario' | 'mensal'
    data?: string
    mes?: string
  }
  total: number
  registros: AuditoriaSenhaItem[]
}

export interface EncerrarExpedienteResponse {
  descartadas: number
  senhas_descartadas: string[]
  mensagem: string
}