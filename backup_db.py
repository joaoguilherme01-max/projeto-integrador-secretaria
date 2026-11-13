import os
import sys
import shutil
import sqlite3
from datetime import datetime

# Configurações
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'db.sqlite3')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')


def fazer_backup():
    """Gera cópia consistente do banco SQLite usando a API de backup nativa."""
    if not os.path.exists(DB_FILE):
        print(f"[ERRO] Banco de dados {DB_FILE} não encontrado.")
        return None

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f"backup_db_{timestamp}.sqlite3")

    print(f"Iniciando backup de {DB_FILE}...")
    try:
        # Usar backup API do sqlite3 garante consistência mesmo com conexões abertas
        source_conn = sqlite3.connect(DB_FILE)
        backup_conn = sqlite3.connect(backup_file)
        with backup_conn:
            source_conn.backup(backup_conn)
        backup_conn.close()
        source_conn.close()

        tamanho_kb = os.path.getsize(backup_file) / 1024
        print(f"[SUCESSO] Backup gerado com sucesso: {backup_file} ({tamanho_kb:.2f} KB)")
        return backup_file
    except Exception as e:
        print(f"[ERRO] Falha ao criar backup: {e}")
        return None


def restaurar_backup(arquivo_backup, destino_teste=None):
    """Restaura um arquivo de backup em um arquivo de destino."""
    if not os.path.exists(arquivo_backup):
        print(f"[ERRO] Arquivo de backup não encontrado: {arquivo_backup}")
        return False

    alvo = destino_teste if destino_teste else DB_FILE
    print(f"Restaurando backup de {arquivo_backup} para {alvo}...")
    try:
        shutil.copy2(arquivo_backup, alvo)
        # Valida integridade do banco restaurado
        conn = sqlite3.connect(alvo)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        res = cursor.fetchone()
        conn.close()

        if res and res[0] == 'ok':
            print(f"[SUCESSO] Restauração concluída e validada (PRAGMA integrity_check: {res[0]})!")
            return True
        else:
            print(f"[ALERTA] Integridade do banco restaurado falhou: {res}")
            return False
    except Exception as e:
        print(f"[ERRO] Falha na restauração: {e}")
        return False


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        if len(sys.argv) > 2:
            restaurar_backup(sys.argv[2])
        else:
            print("Uso para restaurar: python backup_db.py restore <caminho_do_arquivo_de_backup>")
    else:
        fazer_backup()

