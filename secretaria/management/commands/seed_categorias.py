from django.core.management.base import BaseCommand
from secretaria.models import Categoria


class Command(BaseCommand):
    help = 'Popula as categorias iniciais da secretaria escolar'

    def handle(self, *args, **options):
        categorias = [
            ('Declaração', 'Emissão de declarações diversas (matrícula, frequência, conclusão).'),
            ('Histórico escolar', 'Emissão de 1ª e 2ª via de histórico escolar.'),
            ('Matrícula', 'Processos de matrícula inicial e renovação de matrícula.'),
            ('Transferência', 'Solicitação e expedição de transferência escolar.'),
            ('Atendimento', 'Atendimento geral e esclarecimento de dúvidas da secretaria.')
        ]

        for nome, desc in categorias:
            obj, created = Categoria.objects.get_or_create(
                nome=nome,
                defaults={'descricao': desc, 'ativa': True}
            )
            status = 'Criada' if created else 'Já existente'
            self.stdout.write(self.style.SUCCESS(f"{obj.nome}: {status}"))

