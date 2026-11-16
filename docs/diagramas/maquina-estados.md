# Máquina de Estados do Atendimento

Abaixo está o diagrama de transição de estados das senhas no sistema LabManager.

stateDiagram-v2
    [*] --> EMITIDA : Totem
    EMITIDA --> AGUARDANDO : Entra na fila
    AGUARDANDO --> CHAMADA : Atendente chama
    CHAMADA --> EM_ATENDIMENTO : Paciente comparece
    CHAMADA --> CHAMADA_NOVAMENTE : Paciente não comparece
    CHAMADA_NOVAMENTE --> EM_ATENDIMENTO : Paciente comparece (2ª vez)
    CHAMADA_NOVAMENTE --> NÃO_COMPARECEU : Abandono
    EM_ATENDIMENTO --> ATENDIDA : Atendimento finalizado
    ATENDIDA --> [*]
    NÃO_COMPARECEU --> [*]