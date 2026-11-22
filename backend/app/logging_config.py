import logging
import os
from logging.handlers import RotatingFileHandler

NOME_DO_ARQUIVO = "labmanager.log"
TAMANHO_MAXIMO_BYTES = 5 * 1024 * 1024  # 5 MB por arquivo
QUANTIDADE_DE_ARQUIVOS_ANTIGOS = 5
FORMATO = "%(asctime)s %(levelname)s [%(name)s] %(message)s"

_MARCA = "_labmanager_handler"


def _marcar(handler):
    setattr(handler, _MARCA, True)
    return handler


def configurar_logging(app):
    """Configura o log da aplicação: console sempre e, se habilitado, arquivo com rotação.

    Pode ser chamada várias vezes (por exemplo, uma vez por teste) sem duplicar mensagens:
    os handlers criados aqui são removidos antes de serem recriados.
    """
    logger = logging.getLogger(app.name)

    nivel = getattr(logging, str(app.config.get("LOG_LEVEL", "INFO")).upper(), logging.INFO)
    logger.setLevel(nivel)

    for handler in list(logger.handlers):
        if getattr(handler, _MARCA, False):
            logger.removeHandler(handler)
            handler.close()

    formatador = logging.Formatter(FORMATO)

    console = _marcar(logging.StreamHandler())
    console.setFormatter(formatador)
    logger.addHandler(console)

    if app.config.get("LOG_TO_FILE"):
        pasta = app.config["LOG_DIR"]
        try:
            os.makedirs(pasta, exist_ok=True)
            arquivo = _marcar(RotatingFileHandler(
                os.path.join(pasta, NOME_DO_ARQUIVO),
                maxBytes=TAMANHO_MAXIMO_BYTES,
                backupCount=QUANTIDADE_DE_ARQUIVOS_ANTIGOS,
                encoding="utf-8",
            ))
            arquivo.setFormatter(formatador)
            logger.addHandler(arquivo)
        except OSError:
            # Sem permissão ou disco cheio: a API continua de pé, só com log no console.
            logger.warning("Não foi possível gravar o log em arquivo (%s).", pasta, exc_info=True)

    return logger
