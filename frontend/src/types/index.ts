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
  guiche: string
  estado_evento: 'CHAMADA' | 'CHAMADA_NOVAMENTE'
  estado_atual: EstadoSenha
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