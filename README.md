# LabFlow - Sistema de Controle de Atendimento

Sistema web para gerenciamento de filas e controle de atendimentos em laboratórios clínicos. 
Projeto Final da disciplina de Back End Frameworks - UNINASSAU (Semestre 2026.2).

## Equipe
* Eduardo Guilherme - Matrícula: 01802828
* Bruno André - Matrícula: 01554553
* [Nome do Integrante 3] - Matrícula: [Matrícula 3]

## Tecnologias e Versões
* Backend: Python 3.14+, Flask
* Banco de Dados: SQLite (com Flask-SQLAlchemy e Flask-Migrate)
* Frontend: React 19, TypeScript, Vite
* Autenticação: JWT (Flask-JWT-Extended)

## Dependências e Pré-requisitos
* Python 3.14 ou superior
* Node.js LTS 22 ou superior
* Git

As dependências específicas do backend estão listadas no arquivo `backend/requirements.txt` e as do frontend em `frontend/package.json`.

## Instalação e Execução

### 1. Configuração do Backend
Navegue até a pasta do backend:
`cd backend`

Crie e ative o ambiente virtual:
`python -m venv venv`
`venv\Scripts\activate` (Windows)

Instale as dependências:
`pip install -r requirements.txt`

Configure as variáveis de ambiente:
Copie o arquivo `.env.example` para `.env` e preencha as variáveis secretas.

Inicialize o banco de dados e aplique as migrations:
`flask db upgrade`

Popule o banco de dados com os dados iniciais (seed):
`flask seed run`

Inicie o servidor Flask:
`flask run`

### 2. Configuração do Frontend
Em um novo terminal, navegue até a pasta do frontend:
`cd frontend`

Instale as dependências:
`npm install`

Inicie o servidor de desenvolvimento:
`npm run dev`

## Integração com o Frontend
O frontend está configurado para se comunicar com a API do backend rodando localmente na porta padrão do Flask (http://localhost:5000). Certifique-se de iniciar o backend antes de interagir com as telas do React.

## Usuários de Teste e Seed
O script de seed (`flask seed run`) cria os seguintes usuários para testes:

* Perfil Atendente:
  * Email: atendente@labflow.com
  * Senha: password123
* Perfil Gestor:
  * Email: gestor@labflow.com
  * Senha: password123

## Testes Automatizados
Para executar a suíte de testes do backend utilizando Pytest, navegue até a pasta `backend` e execute:
`pytest`

## Documentação da API
A documentação interativa da API (Swagger/OpenAPI) pode ser acessada em:
`http://localhost:5000/api/docs`
*Uma coleção Postman também está disponível na pasta `docs/postman_collection.json`.*

## Arquitetura e Estratégia de Concorrência
O backend adota uma Arquitetura em Camadas (Routes, Services, Repositories, Models, Schemas) para separar responsabilidades. Para tratar a concorrência exigida no edital (evitar chamadas duplicadas da mesma senha por guichês diferentes), adotamos a estratégia de Lock Otimista no SQLite, utilizando uma coluna de versão nas tabelas críticas.

## Diagramas
Os diagramas de Casos de Uso, Classes, Máquina de Estados e Sequência estão disponíveis na pasta `/docs/diagramas`.

## Funcionalidades

Implementadas:
* [x] Emissão de senhas (SP, SG, SE) no formato YYMMDD-PPSQ.
* [x] Regra de alternância de filas (SP -> SE/SG -> SP -> SE/SG).
* [x] Autenticação e controle de perfis (Atendente e Gestor).
* [x] Máquina de estados completa (7 estados com validação).
* [x] Controle de chamadas concorrentes (Lock Otimista).
* [x] Relatórios diários e mensais.
* [x] Auditoria de atendimentos.

## Declaração de Uso de Inteligência Artificial
Declaramos que ferramentas de IA generativa foram utilizadas como apoio ao desenvolvimento deste projeto (ex: estruturação inicial de arquivos e revisão de conceitos), estando a equipe plenamente ciente e capaz de explicar todo o código fonte produzido, conforme as regras do edital.