import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "labmanager.db"
BACKUP_DIR = BASE_DIR / "backups"


def realizar_backup():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Banco de dados não encontrado em {DB_PATH}")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = BACKUP_DIR / f"labmanager_backup_{carimbo}.db"

    with sqlite3.connect(DB_PATH) as origem, sqlite3.connect(destino) as copia:
        origem.backup(copia)

    print(f"Backup gerado com sucesso: {destino}")
    return destino


if __name__ == "__main__":
    realizar_backup()