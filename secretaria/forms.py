from django import forms
from django.contrib.auth.models import User
from .models import Demanda, Categoria


class DemandaForm(forms.ModelForm):
    class Meta:
        model = Demanda
        fields = [
            'solicitante',
            'contato',
            'categoria',
            'descricao',
            'prioridade',
            'prazo',
            'responsavel',
        ]
        widgets = {
            'solicitante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo do aluno ou responsável',
                'required': True,
            }),
            'contato': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Telefone, WhatsApp ou e-mail',
                'required': True,
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descreva detalhadamente o que foi solicitado...',
                'required': True,
            }),
            'prioridade': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'prazo': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'responsavel': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'solicitante': 'Solicitante',
            'contato': 'Contato',
            'categoria': 'Tipo de Solicitação (Categoria)',
            'descricao': 'Descrição da Demanda',
            'prioridade': 'Prioridade',
            'prazo': 'Prazo Previsto de Conclusão',
            'responsavel': 'Responsável pelo Atendimento',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra apenas categorias ativas
        self.fields['categoria'].queryset = Categoria.objects.filter(ativa=True).order_by('nome')
        self.fields['categoria'].empty_label = 'Selecione uma categoria...'
        
        # Filtra usuários ativos para atribuição
        self.fields['responsavel'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'username')
        self.fields['responsavel'].empty_label = 'Não atribuído (definir na triagem)'
        self.fields['responsavel'].required = False
        self.fields['prazo'].required = False

