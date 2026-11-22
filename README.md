# LabManager — Sistema de Controle de Atendimento

Sistema web full-stack para gerenciamento de filas, chamadas com priorização automatizada, máquina de estados, relatórios gerenciais e auditoria para laboratórios de análises clínicas.

Projeto Final integrado das disciplinas de **Back End Frameworks** (Prof. Eduardo Hernandes) e **Front End** (Prof. João Ferreira) — **UNINASSAU (Semestre 2026.2)**.

## Equipe

| Integrante | Matrícula |
| :--- | :--- |
| Eduardo Guilherme | 01802828 |
| Bruno André | 01554553 |

## Tecnologias e Versões

- **Back-end:** Python 3.13+ (compatível com Python 3.14), Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Flask-CORS, Pytest
- **Banco de Dados:** SQLite (padrão local, compatível com MySQL 8.0 via `DATABASE_URL` no SQLAlchemy)
- **Front-end:** React 19, TypeScript, Vite, Tailwind CSS, React Router, Axios, Lucide React
- **Documentação da API:** OpenAPI 3.0 / Swagger UI (`/apidocs`)

## Pré-requisitos e Dependências

- **Python** 3.13 ou superior
- **Node.js** LTS 22 ou superior (com `npm`)
- **Git**

Todas as dependências estão declaradas em:
- Back-end: `backend/requirements.txt`
- Front-end: `frontend/package.json`

## Estrutura do Repositório

```text
LabManager/
├── backend/
│   ├── app/
│   │   ├── models/          # Entidades ORM (Usuario, Senha, HistoricoEstado, Fila, Paciente)
│   │   ├── repositories/    # Acesso a dados e operações atômicas (lock otimista)
│   │   ├── routes/          # Blueprints REST (auth, senhas, relatórios, docs)
│   │   ├── services/        # Regras de negócio, alternância, máquina de estados, expediente e KPIs
│   │   ├── decorators.py    # Controle de acesso por perfil (RBAC)
│   │   ├── errors.py        # Tratamento global de erros JSON padronizados
│   │   └── logging_config.py# Logs estruturados com rotação
│   ├── migrations/          # Histórico de migrations (Flask-Migrate / Alembic)
│   ├── tests/               # Suíte automatizada (69 testes com Pytest)
│   ├── backup_db.py         # Script de backup consistente do banco SQLite
│   ├── seed_simulacao.py    # Seed de simulação (TM por tipo + 5% de descarte)
│   ├── .env.example
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── public/              # Logo e favicon (logo.png)
│   ├── src/
│   │   ├── components/      # BrandLogo e ProtectedRoute
│   │   ├── contexts/        # AuthContext (sessão JWT)
│   │   ├── pages/           # Home, Totem, Painel, Login, Atendimento e Relatorios
│   │   ├── routes/          # AppRoutes
│   │   ├── services/        # Cliente Axios e chamadas à API
│   │   ├── types/           # Tipagens TypeScript
│   │   └── utils/           # Formatação de senhas, estados e fuso horário
│   ├── .env.example
│   └── package.json
├── docs/
│   ├── diagramas/
│   │   ├── casos-de-uso.md
│   │   ├── entidade-relacionamento.md
│   │   ├── maquina-estados.md
│   │   └── sequencia.md
│   ├── arquitetura-e-concorrencia.md
│   ├── contingencia.md
│   └── regras-de-negocio.md
└── README.md
```

## Instalação e Execução (do Zero)

### 1. Clonar o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd LabManager
```

### 2. Configurar e iniciar o Back-end

```bash
cd backend
python -m venv venv
```

Ative o ambiente virtual:
- **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
- **Windows (CMD):** `venv\Scripts\activate`
- **Linux / macOS:** `source venv/bin/activate`

Instale as dependências:

```bash
pip install -r requirements.txt
```

Crie o arquivo de variáveis de ambiente a partir do exemplo:
- **Windows (PowerShell):** `Copy-Item .env.example .env`
- **Linux / macOS:** `cp .env.example .env`

> **Atenção ao horário de expediente (`07h` às `17h`):** por padrão, `VALIDAR_EXPEDIENTE=true` bloqueia emissões e novas chamadas fora do horário comercial (conforme regra do edital). Caso esteja avaliando o sistema fora desse intervalo, altere `VALIDAR_EXPEDIENTE=false` no arquivo `backend/.env` antes de iniciar o servidor.

Aplique as migrations para criar o banco de dados:

```bash
flask db upgrade
```

Popule os usuários iniciais de teste:

```bash
flask seed
```

*(Opcional — recomendado para visualizar os relatórios e KPIs preenchidos)* Execute a simulação de atendimentos realistas (gera 20 senhas para ontem e 20 para hoje respeitando as faixas de TM e 5% de abandono):

```bash
python seed_simulacao.py
```

Suba a API Flask:

```bash
python run.py
```

A API ficará disponível em `http://127.0.0.1:5000`.

### 3. Configurar e iniciar o Front-end

Em um novo terminal, a partir da raiz do projeto:

```bash
cd frontend
npm install
```

Crie o `.env` local (opcional — o valor padrão já aponta para `http://127.0.0.1:5000`):
- **Windows (PowerShell):** `Copy-Item .env.example .env`
- **Linux / macOS:** `cp .env.example .env`

Inicie a aplicação web:

```bash
npm run dev
```

A interface ficará disponível em `http://localhost:5173`.

## Usuários de Teste e Seed

Criados automaticamente pelo comando `flask seed`:

| Perfil | Email | Senha | Permissões |
| :--- | :--- | :--- | :--- |
| **Atendente (`ATENDENTE`)** | `atendente@labflow.com` | `password123` | Operação de guichê (chamar, rechamar, iniciar, finalizar, marcar ausência) |
| **Gestor (`GESTOR`)** | `gestor@labflow.com` | `password123` | Operação de guichê, gestão de usuários, relatórios diários/mensais, auditoria e encerramento de expediente |

Ao executar `python seed_simulacao.py`, também é criado um segundo atendente (`atendente2@labflow.com` / `password123`) para compor os indicadores comparativos por atendente e por guichê.

## Integração com o Front-end

O front-end React consome diretamente a API REST do back-end (configurada via `VITE_API_URL` em `frontend/.env`, padrão `http://127.0.0.1:5000`) com envio automático do token JWT via interceptor do Axios.

Rotas disponíveis na interface:
- `/` — Central de operações com indicador de saúde da API (`/health`) em tempo real
- `/totem` — Totem de autoatendimento público e anônimo para emissão de senhas (`SP`, `SE`, `SG`)
- `/painel` — Painel de TV em tela cheia com chamada atual, até 5 últimas chamadas distintas, alerta sonoro e síntese de voz (`pt-BR`, anunciando *"Última chamada"* em rechamadas)
- `/login` — Autenticação para equipe interna (`ATENDENTE` e `GESTOR`)
- `/atendimento` — Operação de guichê (`G01` a `G04`), controle da fila e linha do tempo da senha
- `/relatorios` — Painel gerencial exclusivo para `GESTOR` (relatório diário/mensal, TM, KPIs por guichê/atendente, detalhamento por senha, auditoria consolidada e encerramento de expediente)

## Documentação da API (Swagger / OpenAPI)

Com o back-end em execução:
- **Swagger UI interativo:** `http://127.0.0.1:5000/apidocs`
- **Especificação OpenAPI 3.0 (JSON):** `http://127.0.0.1:5000/api/openapi.json`
- **Health Check:** `http://127.0.0.1:5000/health`

## Testes Automatizados

A suíte conta com **69 testes automatizados** em `backend/tests/`, cobrindo emissão, alternância de prioridades, filas vazias, máquina de estados, concorrência simultânea, expediente (`07h–17h`), relatórios/auditoria e tratamento global de erros.

Para executar (dentro da pasta `backend/` com o ambiente virtual ativo):

```bash
pytest
```

## Arquitetura, Concorrência, Segurança e Recuperação de Desastres

- **Arquitetura em Camadas:** separação entre `routes` (HTTP e validação), `services` (regras de negócio, alternância `SP -> SE/SG`, máquina de estados e métricas), `repositories` (queries e updates atômicos) e `models` (ORM SQLAlchemy).
- **Estratégia de Concorrência (Lock Otimista):** a tabela `senhas` possui uma coluna inteira `versao`. Na chamada da próxima senha e nas transições de estado, o `UPDATE` filtra simultaneamente por `id`, `versao` lida e `estado_atual`, incrementando `versao` na mesma instrução SQL. Caso dois guichês disputem a mesma senha simultaneamente, apenas um `UPDATE` obtém `rowcount == 1`; o outro recebe `0`, executa `rollback` e tenta automaticamente a próxima senha disponível (até 5 tentativas), garantindo ausência de duplicidade. Detalhes em [`docs/arquitetura-e-concorrencia.md`](docs/arquitetura-e-concorrencia.md).
- **Segurança, LGPD e Acessibilidade:** senhas armazenadas com hash seguro (`werkzeug.security`), autenticação JWT, RBAC por perfil (`@perfil_requerido`), segredos isolados via `.env`, interação anônima do paciente no totem (minimização de dados pela LGPD), trilha de auditoria restrita a ações operacionais e painel acessível com alto contraste e narração por voz em português.
- **Disponibilidade e Backup:** rota `/health` testando conexão real ao banco (`SELECT 1`, retornando `503` em indisponibilidade), handlers globais de erro sem exposição de stack traces, logs com rotação em `backend/logs/` e backup consistente sob demanda via `python backup_db.py` (salvo em `backend/backups/`). Detalhes em [`docs/contingencia.md`](docs/contingencia.md).

## Documentação Complementar e Diagramas

Toda a documentação técnica e os diagramas em Mermaid estão organizados em `/docs`:

- [Regras de Negócio](docs/regras-de-negocio.md)
- [Arquitetura e Estratégia de Concorrência](docs/arquitetura-e-concorrencia.md)
- [Plano de Contingência e Recuperação de Desastres](docs/contingencia.md)
- [Diagrama de Casos de Uso](docs/diagramas/casos-de-uso.md)
- [Diagrama Entidade-Relacionamento (ER)](docs/diagramas/entidade-relacionamento.md)
- [Diagrama da Máquina de Estados](docs/diagramas/maquina-estados.md)
- [Diagrama de Sequência (Fluxo Completo e Concorrência)](docs/diagramas/sequencia.md)

## Funcionalidades

### Implementadas
- [x] Emissão anônima de senhas (`SP`, `SE`, `SG`) no formato `YYMMDD-PPSQ` com sequencial de 3 dígitos e reinício diário.
- [x] Chamada com alternância `[SP] -> [SE|SG] -> [SP] -> [SE|SG]`, prioridade `SP > SE > SG`, tratamento de filas vazias e atendimento em qualquer guichê.
- [x] Máquina de estados completa (7 estados) com validação estrita de transições e histórico persistido.
- [x] Controle de expediente (`07h` às `17h`), conclusão de atendimentos em curso e descarte de senhas pendentes (automático após 17h ou manual pelo gestor).
- [x] Controle de concorrência com Lock Otimista e testes automatizados de chamadas simultâneas.
- [x] Autenticação JWT com hash seguro e controle de acesso por perfil (`ATENDENTE` e `GESTOR`).
- [x] Painel público com chamada atual, até 5 últimas chamadas distintas, destaque visual e áudio falado em `pt-BR` com aviso de *"Última chamada"*.
- [x] Relatórios diários e mensais (totais, por tipo, detalhado por senha, tempo médio de atendimento e espera).
- [x] Indicadores de desempenho (taxa de atendimento, taxa de não comparecimento, atendimentos por guichê e por atendente).
- [x] Auditoria de eventos paginada e auditoria consolidada por senha (atendente, guichê, 1ª chamada, 2ª chamada, início e fim).
- [x] Script de simulação realista de TM por categoria e 5% de descarte (`seed_simulacao.py`).
- [x] Documentação interativa Swagger/OpenAPI (`/apidocs`), health check (`/health`), logs com rotação e script de backup (`backup_db.py`).
- [x] Integração completa com front-end React/TypeScript (Totem, Painel, Guichê e Relatórios).

## Declaração de Uso de Inteligência Artificial

Conforme a Seção 9.5 do edital, declaramos que ferramentas de inteligência artificial generativa foram utilizadas como apoio durante o desenvolvimento deste projeto (auxílio na estruturação de componentes, revisão de conformidade com requisitos, elaboração de testes e documentação). Todos os integrantes acompanharam o desenvolvimento, compreendem a arquitetura adotada e estão aptos a explicar integralmente o código-fonte entregue.
