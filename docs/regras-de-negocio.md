# Regras de Negócio - LabManager

## 1. Tipos de Senhas e Prioridades
O sistema gerencia três tipos de senhas, em ordem de prioridade:
1. **SP (Senha Prioritária):** Maior prioridade. Tempo Médio (TM) de 15 min (±5 min).
2. **SE (Senha de Exames):** Atendimento rápido. TM de 1 min (95% dos casos) a 5 min (5%).
3. **SG (Senha Geral):** Menor prioridade. TM de 5 min (±3 min).

## 2. Formato da Senha
Toda senha emitida segue estritamente o formato `YYMMDD-PPSQ`:
* `YYMMDD`: Ano, mês e dia da emissão.
* `PP`: Tipo da senha (SP, SE ou SG).
* `SQ`: Sequencial de 3 dígitos, reiniciado diariamente.

## 3. Lógica de Alternância da Fila
A chamada obedece ao seguinte ciclo contínuo, tratando filas vazias quando necessário:
`[SP] -> [SE ou SG] -> [SP] -> [SE ou SG]`

## 4. Regras de Expediente e Abandono
* **Expediente:** O sistema opera exclusivamente das 07h às 17h. Fora desse horário, senhas não são emitidas nem chamadas (senhas restantes são descartadas).
* **Abandono (Não Comparecimento):** Se o paciente for chamado 2 vezes e não comparecer ao guichê, o atendimento é cancelado (estado `NÃO_COMPARECEU`) e o sistema avança para a próxima senha da fila.
* **Taxa de Descarte:** Historicamente, 5% das senhas emitidas são descartadas sem atendimento.