# Tratamento de Falhas e Contingência - LabManager

Este documento explica como a API responde quando algo dá errado, onde olhar para descobrir a causa e o que a equipe deve fazer quando o sistema fica indisponível.

> As seções 1, 2 e 3 descrevem o que o sistema **já faz**. As seções 4, 5 e 6 são **orientações sugeridas** e devem ser validadas pelo gestor e pela equipe antes de virarem procedimento oficial.

## 1. Como a API responde a erros

Toda resposta de erro é JSON e segue o mesmo formato:

```json
{
  "erro": "Mensagem amigável para exibir ao usuário.",
  "codigo": "CODIGO_ESTAVEL",
  "id_erro": "a1b2c3d4"
}
```

* `erro`: texto em português, pronto para mostrar na tela.
* `codigo`: identificador fixo, para o front-end decidir o que fazer (ex.: `TOKEN_EXPIRADO` leva à tela de login).
* `id_erro`: só aparece nas **falhas do servidor** (500 e 503). É o código que liga a resposta ao detalhe técnico guardado no log. O atendente deve anotá-lo e informar ao suporte.

Os detalhes técnicos (stack trace, comandos SQL, caminhos de arquivos) **nunca** são enviados na resposta. Eles ficam só no log.

| Situação | Status | `codigo` |
|---|---|---|
| Rota inexistente | 404 | `NAO_ENCONTRADO` |
| Método HTTP não aceito pela rota | 405 | `METODO_NAO_PERMITIDO` |
| JSON malformado ou corpo inválido | 400 | `REQUISICAO_INVALIDA` |
| Corpo enviado em formato que não é JSON | 415 | `FORMATO_NAO_SUPORTADO` |
| Sem login (token ausente) | 401 | `NAO_AUTENTICADO` |
| Token inválido | 401 | `TOKEN_INVALIDO` |
| Sessão expirada | 401 | `TOKEN_EXPIRADO` |
| Perfil sem permissão para a rota | 403 | `ACESSO_NEGADO` |
| Banco de dados indisponível | 503 | `BANCO_INDISPONIVEL` (com `id_erro`) |
| Falha inesperada no servidor | 500 | `ERRO_INTERNO` (com `id_erro`) |

Os erros de **regra de negócio** tratados dentro das rotas (por exemplo, transição de estado proibida, senha não encontrada ou conflito entre atendentes) continuam trazendo o campo `erro` com a explicação e o status correspondente (400, 404, 409, 422). O front-end deve sempre usar o campo `erro` para mostrar a mensagem.

## 2. Logs

* **Onde:** `backend/logs/labmanager.log` (a pasta é criada automaticamente e não vai para o Git).
* **Rotação:** quando o arquivo chega a 5 MB, ele é arquivado como `labmanager.log.1`, `.2`, etc. São mantidos 5 arquivos antigos, então o log não cresce sem limite.
* **O que é registrado:** toda falha 500/503, com data e hora, método, rota, o `id_erro` e o **stack trace completo**.
* **Configuração** (no arquivo `.env` do backend, todas opcionais):

| Variável | Padrão | Para que serve |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Nível mínimo registrado (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `LOG_DIR` | `backend/logs` | Pasta onde o arquivo é gravado |
| `LOG_TO_FILE` | `1` | Use `0` para registrar só no console |

### Como investigar um erro a partir do `id_erro`

1. Peça ao atendente o código que apareceu na tela (por exemplo, `a1b2c3d4`).
2. Procure o código no log. No PowerShell (Windows), a pasta `backend`:

```powershell
Select-String -Path logs\labmanager.log -Pattern "a1b2c3d4" -Context 0,30
```

No Linux ou macOS:

```bash
grep -A 30 "a1b2c3d4" logs/labmanager.log
```

3. A linha encontrada mostra quando aconteceu e qual rota falhou. As linhas seguintes trazem o stack trace, e a última indica a causa.

## 3. Como saber se o sistema está de pé

Acesse `GET /health` (por exemplo, `http://localhost:5000/health`):

| Resposta | Significado |
|---|---|
| 200 com `"status": "ok"` | API e banco de dados funcionando |
| 503 com `"status": "indisponivel"` | A API está no ar, mas o banco não respondeu |
| Sem resposta ou erro de conexão | A API está fora do ar |

## 4. Contingência por cenário (sugestão)

| Cenário | Como aparece | O que fazer |
|---|---|---|
| **API fora do ar** | `/health` não responde; as telas mostram erro de conexão | Reiniciar o servidor (`flask run`, dentro de `backend`) e consultar o fim do log. Se não voltar em poucos minutos, passar para o atendimento manual (abaixo). |
| **Banco indisponível** | Erro 503 `BANCO_INDISPONIVEL`; `/health` devolve 503 | No SQLite, um bloqueio costuma ser passageiro: tentar de novo após alguns segundos. Se persistir, parar o servidor, conferir se outro programa está usando o arquivo do banco e iniciar de novo. Se o arquivo estiver corrompido, restaurar o backup (seção 5). |
| **Falha pontual** | Erro 500 `ERRO_INTERNO` com `id_erro` | Repetir a operação uma vez. Se o erro continuar, anotar o `id_erro` e acionar a equipe de desenvolvimento. |
| **Conflito entre atendentes** | Erro 409 informando que a senha foi alterada por outro atendente | Não é uma falha: dois atendentes agiram na mesma senha ao mesmo tempo e só o primeiro valeu. Atualizar a tela e continuar com a próxima senha. |
| **Totem, painel ou guichê sem acesso** (rede ou energia) | Telas sem conexão | Passar para o atendimento manual. |

### Atendimento manual (sugestão)

Enquanto o sistema não volta, manter o atendimento com senhas em papel:

1. Separar blocos numerados por tipo (SP, SE e SG) e entregar na ordem de chegada.
2. Chamar seguindo a mesma regra do sistema: SP primeiro e depois SE ou SG, alternando (`[SP] -> [SE ou SG] -> [SP] -> ...`).
3. Anotar em uma ficha o número, o tipo, o horário da chamada e o resultado (atendida ou não compareceu).
4. Quando o sistema voltar, o gestor decide se as fichas serão lançadas no sistema ou arquivadas.

## 5. Backup e recuperação do banco (sugestão)

O banco é um arquivo SQLite. Com a configuração padrão, fica em `backend/instance/labmanager.db` (ou no caminho definido em `DATABASE_URL`).

**Backup**

* Com o servidor parado, copiar o arquivo do banco para outro local (de preferência outro computador ou um disco externo).
* Sugestão de rotina: uma cópia por dia, ao fim do expediente (17h), guardando as últimas 7.

**Restauração**

1. Parar o servidor.
2. Renomear o arquivo com defeito (por exemplo, `labmanager.db.defeito`) para guardá-lo para análise.
3. Copiar o backup mais recente para o lugar do arquivo original.
4. Iniciar o servidor e conferir `GET /health`.
5. Lembrar que tudo o que foi feito **depois do backup** foi perdido. O relatório de auditoria (`GET /api/relatorios/auditoria`, perfil gestor) mostra até onde o sistema registrou ações, o que ajuda a descobrir o que precisa ser refeito.

**Se não houver backup**: criar um banco novo com `flask db upgrade` e `flask seed run` (dentro de `backend`). Isso recria as tabelas e os usuários de teste, mas as senhas e o histórico anteriores não voltam.

## 6. Depois do incidente (sugestão)

1. Confirmar que `GET /health` responde 200.
2. Fazer login e uma chamada de teste para ver que o fluxo básico funciona.
3. Revisar o log do período e procurar os `id_erro` informados pelos atendentes.
4. Consultar o relatório de auditoria do dia para conferir o que foi registrado durante o problema.
5. Registrar o incidente: o que aconteceu, horário de início e fim, impacto no atendimento e o que foi feito.

## 7. Recomendações para produção

* O arquivo `run.py` inicia o servidor com `debug=True`, o que é próprio de **desenvolvimento**: o modo debug do Flask mostra páginas de depuração com detalhes internos. Em produção, usar um servidor próprio (por exemplo, `waitress` ou `gunicorn`) com o modo debug desligado.
* Trocar `SECRET_KEY` e `JWT_SECRET_KEY` no `.env`. Os valores padrão do código servem apenas para desenvolvimento.
