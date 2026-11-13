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




class EditarDemandaForm(forms.ModelForm):
    observacao_alteracao = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descreva o motivo da alteração ou observação sobre o andamento...'
        }),
        required=False,
        label='Observação sobre a Alteração'
    )

    class Meta:
        model = Demanda
        fields = [
            'solicitante',
            'contato',
            'categoria',
            'descricao',
            'prioridade',
            'status',
            'prazo',
            'responsavel',
            'resultado',
        ]
        widgets = {
            'solicitante': forms.TextInput(attrs={'class': 'form-control'}),
            'contato': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'prazo': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'responsavel': forms.Select(attrs={'class': 'form-select'}),
            'resultado': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observação de encerramento ou justificativa em caso de cancelamento...'
            }),
        }
        labels = {
            'solicitante': 'Solicitante',
            'contato': 'Contato',
            'categoria': 'Tipo de Solicitação (Categoria)',
            'descricao': 'Descrição da Demanda',
            'prioridade': 'Prioridade',
            'status': 'Status da Demanda',
            'prazo': 'Prazo Previsto',
            'responsavel': 'Responsável',
            'resultado': 'Resultado / Justificativa Final',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = Categoria.objects.filter(ativa=True).order_by('nome')
        self.fields['responsavel'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'username')
        self.fields['responsavel'].empty_label = 'Não atribuído'
        self.fields['responsavel'].required = False
        self.fields['prazo'].required = False
