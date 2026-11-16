# Decisões de Arquitetura e Concorrência

## Arquitetura do Backend
O backend foi estruturado utilizando **Arquitetura em Camadas (Layered Architecture)**, separando as responsabilidades para manter os *Controllers* (Rotas) limpos, conforme exigido na rubrica de avaliação.
* **Routes:** Recebem as requisições HTTP e devolvem as respostas JSON.
* **Services:** Contêm toda a lógica de negócio (máquina de estados, alternância de filas).
* **Repositories:** Única camada responsável pela comunicação e queries no banco de dados SQLite.

## Estratégia de Concorrência (Lock Otimista)
Como o banco de dados oficial do projeto é o **SQLite**, enfrentamos limitações nativas de escrita concorrente (o SQLite não suporta `SELECT FOR UPDATE SKIP LOCKED` como o PostgreSQL/MySQL).

Para evitar que dois ou mais atendentes (AA) chamem o mesmo paciente (AC) simultaneamente, adotamos a estratégia de **Lock Otimista (Optimistic Locking)**:
1. A tabela de `Atendimentos` possui uma coluna `versao` (inteiro).
2. Quando um atendente solicita o próximo da fila, o sistema lê o registro e sua `versao` atual (ex: versão 1).
3. Ao atualizar o estado para `CHAMADA`, o banco exige que a versão ainda seja 1 (`UPDATE ... WHERE id = X AND versao = 1`).
4. Se outro atendente tiver feito a chamada milissegundos antes, a versão já será 2. O banco rejeitará a segunda atualização, e o sistema buscará automaticamente o próximo da fila, impedindo a duplicidade sem travar o banco.