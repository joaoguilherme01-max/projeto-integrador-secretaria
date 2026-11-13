from django.core.management.base import BaseCommand
from datetime import datetime
import os
import sqlite3
from django.conf import settings


class Command(BaseCommand):
    help = 'Gera backup seguro e consistente do banco SQLite'

    def handle(self, *args, **options):
        db_path = settings.DATABASES['default']['NAME']
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f"backup_db_{timestamp}.sqlite3")

        self.stdout.write(f"Iniciando backup de {db_path}...")
        try:
            source_conn = sqlite3.connect(db_path)
            backup_conn = sqlite3.connect(backup_path)
            with backup_conn:
                source_conn.backup(backup_conn)
            backup_conn.close()
            source_conn.close()

            tamanho_kb = os.path.getsize(backup_path) / 1024
            self.stdout.write(self.style.SUCCESS(
                f"Backup gerado com sucesso: {backup_path} ({tamanho_kb:.2f} KB)"
            ))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Erro ao gerar backup: {e}"))

