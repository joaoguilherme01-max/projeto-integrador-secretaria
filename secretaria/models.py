from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class PerfilUsuario(models.Model):
    PERFIL_CHOICES = [
        ('ADMINISTRADOR', 'Administrador'),
        ('GESTOR', 'Gestor da Secretaria'),
        ('ATENDENTE', 'Atendente / Servidor'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    perfil = models.CharField(max_length=20, choices=PERFIL_CHOICES, default='ATENDENTE')
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_perfil_display()})"


class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, default='')
    ativa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Demanda(models.Model):
    PRIORIDADE_CHOICES = [
        ('BAIXA', 'Baixa'),
        ('MEDIA', 'Média'),
        ('ALTA', 'Alta'),
        ('URGENTE', 'Urgente'),
    ]

    STATUS_CHOICES = [
        ('RECEBIDA', 'Recebida'),
        ('TRIAGEM', 'Em Triagem'),
        ('AGUARDANDO_INFO', 'Aguardando Informações'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('EM_VALIDACAO', 'Em Validação'),
        ('CONCLUIDA', 'Concluída'),
        ('CANCELADA', 'Cancelada'),
    ]

    protocolo = models.CharField(max_length=20, unique=True, editable=False)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='demandas')
    responsavel = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='demandas_atribuidas'
    )
    solicitante = models.CharField(max_length=150)
    contato = models.CharField(max_length=100)
    descricao = models.TextField()
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='MEDIA')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RECEBIDA')
    data_entrada = models.DateTimeField(auto_now_add=True)
    prazo = models.DateField(null=True, blank=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    resultado = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Demanda'
        verbose_name_plural = 'Demandas'
        ordering = ['-data_entrada']

    def __str__(self):
        return f"{self.protocolo} - {self.solicitante} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.protocolo:
            ano_atual = timezone.now().year
            prefixo = f"SEC-{ano_atual}-"
            ultima_demanda = Demanda.objects.filter(protocolo__startswith=prefixo).order_by('-id').first()
            if ultima_demanda and ultima_demanda.protocolo:
                try:
                    ultimo_seq = int(ultima_demanda.protocolo.split('-')[-1])
                    proximo_seq = ultimo_seq + 1
                except (ValueError, IndexError):
                    proximo_seq = 1
            else:
                proximo_seq = 1
            self.protocolo = f"{prefixo}{proximo_seq:05d}"
        super().save(*args, **kwargs)


class Historico(models.Model):
    demanda = models.ForeignKey(Demanda, on_delete=models.CASCADE, related_name='historicos')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='historicos_registrados')
    etapa_anterior = models.CharField(max_length=50, blank=True, default='')
    nova_etapa = models.CharField(max_length=50)
    responsavel_anterior = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='historicos_responsavel_anterior'
    )
    novo_responsavel = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='historicos_novo_responsavel'
    )
    observacao = models.TextField(blank=True, default='')
    data_alteracao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico'
        verbose_name_plural = 'Históricos'
        ordering = ['-data_alteracao']

    def __str__(self):
        return f"Histórico {self.demanda.protocolo} - {self.nova_etapa} ({self.data_alteracao.strftime('%d/%m/%Y %H:%M')})"


class Anexo(models.Model):
    demanda = models.ForeignKey(Demanda, on_delete=models.CASCADE, related_name='anexos')
    nome_arquivo = models.CharField(max_length=255)
    arquivo = models.FileField(upload_to='anexos/%Y/%m/')
    data_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'
        ordering = ['-data_envio']

    def __str__(self):
        return f"{self.nome_arquivo} ({self.demanda.protocolo})"
