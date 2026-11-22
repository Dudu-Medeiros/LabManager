from flask import Blueprint, jsonify, Response

docs_bp = Blueprint("docs", __name__)

OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "LabManager API",
        "version": "1.0.0",
        "description": "API REST para controle de atendimento, filas prioritárias (SP/SE/SG), máquina de estados, relatórios e auditoria de laboratório de análises clínicas."
    },
    "servers": [{"url": "http://127.0.0.1:5000", "description": "Servidor local"}],
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    },
    "paths": {
        "/health": {
            "get": {
                "tags": ["Sistema"],
                "summary": "Health check da aplicação",
                "responses": {"200": {"description": "API operacional"}}
            }
        },
        "/api/auth/login": {
            "post": {
                "tags": ["Autenticação"],
                "summary": "Login de atendente ou gestor",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["email", "senha"],
                                "properties": {
                                    "email": {"type": "string", "example": "gestor@labflow.com"},
                                    "senha": {"type": "string", "example": "password123"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Token JWT e dados do usuário"},
                    "401": {"description": "Credenciais inválidas"}
                }
            }
        },
        "/api/auth/usuarios": {
            "get": {
                "tags": ["Autenticação"],
                "summary": "Listar usuários (GESTOR)",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "Lista de usuários"}}
            },
            "post": {
                "tags": ["Autenticação"],
                "summary": "Cadastrar atendente ou gestor (GESTOR)",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["nome", "email", "senha", "perfil"],
                                "properties": {
                                    "nome": {"type": "string"},
                                    "email": {"type": "string"},
                                    "senha": {"type": "string"},
                                    "perfil": {"type": "string", "enum": ["ATENDENTE", "GESTOR"]}
                                }
                            }
                        }
                    }
                },
                "responses": {"201": {"description": "Usuário criado"}}
            }
        },
        "/api/senhas/emitir": {
            "post": {
                "tags": ["Senhas"],
                "summary": "Emitir senha no totem (público)",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["tipo"],
                                "properties": {
                                    "tipo": {"type": "string", "enum": ["SP", "SE", "SG"]},
                                    "entrar_fila": {"type": "boolean", "default": True}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Senha emitida no formato YYMMDD-PPSQ"},
                    "403": {"description": "Fora do horário de expediente (07h–17h)"}
                }
            }
        },
        "/api/senhas/painel": {
            "get": {
                "tags": ["Senhas"],
                "summary": "Dados do painel público (chamada atual e 5 últimas distintas)",
                "responses": {"200": {"description": "Estado atual do painel"}}
            }
        },
        "/api/senhas/expediente": {
            "get": {
                "tags": ["Senhas"],
                "summary": "Status do expediente (07h às 17h)",
                "responses": {"200": {"description": "Informações de expediente"}}
            }
        },
        "/api/senhas/encerrar-expediente": {
            "post": {
                "tags": ["Senhas"],
                "summary": "Descartar senhas pendentes do dia (GESTOR)",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "Resumo de senhas descartadas"}}
            }
        },
        "/api/senhas/fila": {
            "get": {
                "tags": ["Senhas"],
                "summary": "Listar fila aguardando e atendimentos em andamento",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "Fila atual"}}
            }
        },
        "/api/senhas/chamar-proximo": {
            "post": {
                "tags": ["Senhas"],
                "summary": "Chamar próxima senha seguindo SP -> SE/SG com lock otimista",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {"guiche": {"type": "string", "example": "G01"}}
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Senha chamada"},
                    "403": {"description": "Fora do expediente"},
                    "404": {"description": "Fila vazia"},
                    "409": {"description": "Conflito de concorrência"}
                }
            }
        },
        "/api/senhas/{senha_id}/estado": {
            "patch": {
                "tags": ["Senhas"],
                "summary": "Transicionar estado da senha na máquina de estados",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {"name": "senha_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["estado"],
                                "properties": {
                                    "estado": {
                                        "type": "string",
                                        "enum": [
                                            "AGUARDANDO",
                                            "CHAMADA",
                                            "CHAMADA_NOVAMENTE",
                                            "EM_ATENDIMENTO",
                                            "ATENDIDA",
                                            "NAO_COMPARECEU"
                                        ]
                                    },
                                    "guiche": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Estado atualizado"},
                    "409": {"description": "Conflito de versão"},
                    "422": {"description": "Transição inválida"}
                }
            }
        },
        "/api/relatorios/diario": {
            "get": {
                "tags": ["Relatórios"],
                "summary": "Relatório diário, TM, KPIs e detalhamento por senha (GESTOR)",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {"name": "data", "in": "query", "schema": {"type": "string", "example": "2026-11-22"}}
                ],
                "responses": {"200": {"description": "Relatório diário"}}
            }
        },
        "/api/relatorios/mensal": {
            "get": {
                "tags": ["Relatórios"],
                "summary": "Relatório mensal consolidado por dia, TM e KPIs (GESTOR)",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {"name": "mes", "in": "query", "schema": {"type": "string", "example": "2026-11"}}
                ],
                "responses": {"200": {"description": "Relatório mensal"}}
            }
        },
        "/api/relatorios/auditoria": {
            "get": {
                "tags": ["Relatórios"],
                "summary": "Auditoria paginada de eventos (GESTOR)",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "Eventos de auditoria"}}
            }
        },
        "/api/relatorios/auditoria/senhas": {
            "get": {
                "tags": ["Relatórios"],
                "summary": "Auditoria consolidada por senha (1ª/2ª chamada, início e fim) (GESTOR)",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {"name": "data", "in": "query", "schema": {"type": "string"}},
                    {"name": "mes", "in": "query", "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "Auditoria por senha"}}
            }
        }
    }
}

SWAGGER_HTML = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>LabManager · Documentação da API</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    SwaggerUIBundle({
      url: '/api/openapi.json',
      dom_id: '#swagger-ui'
    });
  </script>
</body>
</html>"""


@docs_bp.route("/api/openapi.json", methods=["GET"])
def openapi_json():
    return jsonify(OPENAPI_SPEC), 200


@docs_bp.route("/apidocs", methods=["GET"])
def swagger_ui():
    return Response(SWAGGER_HTML, mimetype="text/html")