# Diagrama de Sequência — Fluxo Completo e Concorrência

Representa a emissão anônima no totem, a disputa simultânea entre dois atendentes protegida por lock otimista (`versao`), a atualização do painel e o encerramento do atendimento.

```mermaid
sequenceDiagram
    actor AC as Cliente (Totem)
    participant API as LabManager API
    participant DB as Banco de Dados
    actor AA1 as Atendente 1 (G01)
    actor AA2 as Atendente 2 (G02)
    participant TV as Painel (TV)

    AC->>API: POST /api/senhas/emitir (SP, entrar_fila=true)
    API->>DB: INSERT senhas (versao=1) + historico (EMITIDA, AGUARDANDO)
    API-->>AC: 201 Created (261122-SP001)

    par Chamada simultanea em dois guiches
        AA1->>API: POST /api/senhas/chamar-proximo (G01)
        AA2->>API: POST /api/senhas/chamar-proximo (G02)
    end

    API->>DB: UPDATE senhas SET estado=CHAMADA, versao=versao+1 WHERE id=1 AND versao=2 (AA1)
    DB-->>API: rowcount = 1 (sucesso AA1)
    API->>DB: UPDATE senhas SET estado=CHAMADA, versao=versao+1 WHERE id=1 AND versao=2 (AA2)
    DB-->>API: rowcount = 0 (conflito detectado)
    API->>DB: Retry AA2 -> seleciona proxima senha disponivel (SE/SG)

    API-->>AA1: 200 OK (261122-SP001 no G01)
    API-->>AA2: 200 OK (proxima senha distinta no G02)

    TV->>API: GET /api/senhas/painel (polling 3s)
    API-->>TV: chamada_atual + 5 ultimas distintas
    TV->>TV: Destaque visual + audio PT-BR

    AA1->>API: PATCH /api/senhas/1/estado (EM_ATENDIMENTO)
    AA1->>API: PATCH /api/senhas/1/estado (ATENDIDA)
    API->>DB: Registra historico completo para auditoria e TM
    API-->>AA1: 200 OK (Atendimento finalizado)
```