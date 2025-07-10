# apps/core/forms.py - Atualizações para funcionalidade de comparação

from django import forms
from datetime import date, timedelta


class AgendamentoForm(forms.Form):

    # Filtros principais (obrigatórios)
    cidade = forms.IntegerField(required=True)
    bairro = forms.IntegerField(required=False)
    data_checkin = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    hospedes = forms.IntegerField(required=True, min_value=1)
    quantidade_noites = forms.IntegerField(required=True, min_value=1)

    # Filtros de propriedades (>=)
    quartos = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Qualquer quantidade'),
            ('1', '1+ quarto'),
            ('2', '2+ quartos'),
            ('3', '3+ quartos'),
            ('4', '4+ quartos'),
            ('5', '5+ quartos'),
        ]
    )

    camas = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Qualquer quantidade'),
            ('1', '1+ cama'),
            ('2', '2+ camas'),
            ('3', '3+ camas'),
            ('4', '4+ camas'),
            ('5', '5+ camas'),
        ]
    )

    banheiros = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Qualquer quantidade'),
            ('1', '1+ banheiro'),
            ('2', '2+ banheiros'),
            ('3', '3+ banheiros'),
        ]
    )

    # Filtro de preço
    preco_maximo = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Ex: 300',
            'step': '0.01'
        })
    )

    def clean_bairro(self):
        """Validação customizada para o campo bairro."""
        bairro = self.cleaned_data.get('bairro')
        if bairro == '' or bairro is None:
            return None
        return bairro

    def clean_quartos(self):
        """Converte string vazia para None."""
        quartos = self.cleaned_data.get('quartos')
        if quartos == '' or quartos is None:
            return None
        return int(quartos)

    def clean_camas(self):
        """Converte string vazia para None."""
        camas = self.cleaned_data.get('camas')
        if camas == '' or camas is None:
            return None
        return int(camas)

    def clean_banheiros(self):
        """Converte string vazia para None."""
        banheiros = self.cleaned_data.get('banheiros')
        if banheiros == '' or banheiros is None:
            return None
        return int(banheiros)

    def clean_data_checkin(self):
        """Validação para garantir que a data seja futura."""
        data = self.cleaned_data.get('data_checkin')
        if data and data < date.today():
            raise forms.ValidationError("A data deve ser futura.")
        return data


class ComparacaoForm(forms.Form):
    """
    Formulário para validar os dados de comparação entre localidades.
    """
    # Localização 1
    cidade_1 = forms.IntegerField(required=True)
    bairro_1 = forms.IntegerField(required=False)

    # Localização 2
    cidade_2 = forms.IntegerField(required=True)
    bairro_2 = forms.IntegerField(required=False)

    # Parâmetros de busca
    data_checkin = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'min': date.today().isoformat()})
    )
    hospedes = forms.IntegerField(required=True, min_value=1, max_value=20)
    quantidade_noites = forms.IntegerField(required=True, min_value=1, max_value=30)

    def clean_data_checkin(self):
        """Validação para garantir que a data seja futura."""
        data = self.cleaned_data.get('data_checkin')
        if data and data < date.today():
            raise forms.ValidationError("A data deve ser futura.")
        return data

    def clean_bairro_1(self):
        """Conversão de string vazia para None."""
        bairro = self.cleaned_data.get('bairro_1')
        if bairro == '' or bairro is None:
            return None
        return bairro

    def clean_bairro_2(self):
        """Conversão de string vazia para None."""
        bairro = self.cleaned_data.get('bairro_2')
        if bairro == '' or bairro is None:
            return None
        return bairro

    def clean(self):
        """
        Validação customizada para garantir que as comparações sejam válidas.
        """
        cleaned_data = super().clean()
        cidade_1 = cleaned_data.get('cidade_1')
        bairro_1 = cleaned_data.get('bairro_1')
        cidade_2 = cleaned_data.get('cidade_2')
        bairro_2 = cleaned_data.get('bairro_2')

        # Se as cidades são iguais, pelo menos um deve ter bairro especificado
        if cidade_1 == cidade_2:
            if not bairro_1 and not bairro_2:
                raise forms.ValidationError(
                    "Para comparar a mesma cidade, você deve especificar pelo menos um bairro."
                )
            if bairro_1 and bairro_2 and bairro_1 == bairro_2:
                raise forms.ValidationError(
                    "Por favor, selecione bairros diferentes para comparar."
                )

        return cleaned_data

    def get_location_info(self):
        """
        Retorna informações estruturadas sobre as localizações para comparação.
        """
        if not self.is_valid():
            return None

        data = self.cleaned_data

        # Localização 1
        if data.get('bairro_1'):
            loc_1 = {
                'tipo': 'bairro',
                'id': data.get('bairro_1'),
                'cidade_id': data.get('cidade_1')
            }
        else:
            loc_1 = {
                'tipo': 'cidade',
                'id': data.get('cidade_1'),
                'cidade_id': data.get('cidade_1')
            }

        # Localização 2
        if data.get('bairro_2'):
            loc_2 = {
                'tipo': 'bairro',
                'id': data.get('bairro_2'),
                'cidade_id': data.get('cidade_2')
            }
        else:
            loc_2 = {
                'tipo': 'cidade',
                'id': data.get('cidade_2'),
                'cidade_id': data.get('cidade_2')
            }

        return {
            'local_1': loc_1,
            'local_2': loc_2,
            'data_checkin': data.get('data_checkin'),
            'hospedes': data.get('hospedes'),
            'quantidade_noites': data.get('quantidade_noites')
        }


class PlanejadorFeriasForm(forms.Form):
    """
    Formulário para o planejador de férias onde o usuário define
    orçamento e requisitos para encontrar opções de viagem.
    """
    # Orçamento total
    orcamento_total = forms.DecimalField(
        required=True,
        min_value=100,
        max_value=50000,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Ex: 1500.00',
            'step': '0.01',
            'class': 'form-control'
        }),
        label='Orçamento Total (R$)',
        help_text='Quanto você quer gastar no total com hospedagem?'
    )

    # Quantidade de noites
    quantidade_noites = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=30,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Ex: 7',
            'class': 'form-control'
        }),
        label='Quantidade de Noites',
        help_text='Quantas noites você quer ficar?'
    )

    # Número de hóspedes
    hospedes = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=20,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Ex: 2',
            'class': 'form-control'
        }),
        label='Número de Hóspedes',
        help_text='Quantas pessoas vão viajar?'
    )

    # Requisito de fim de semana
    inclui_fim_de_semana = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Deve incluir fim de semana',
        help_text='A viagem deve incluir sábado e domingo?'
    )

    # Período de busca (próximos meses)
    periodo_busca = forms.ChoiceField(
        required=True,
        choices=[
            (30, 'Próximos 30 dias'),
            (60, 'Próximos 2 meses'),
            (90, 'Próximos 3 meses'),
            (180, 'Próximos 6 meses'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Período de Busca',
        help_text='Em qual período você pode viajar?'
    )

    # Filtros opcionais
    quartos_minimo = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Qualquer',
            'class': 'form-control'
        }),
        label='Mínimo de Quartos (opcional)'
    )

    camas_minimo = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=20,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Qualquer',
            'class': 'form-control'
        }),
        label='Mínimo de Camas (opcional)'
    )

    def clean_orcamento_total(self):
        """Validação do orçamento total."""
        orcamento = self.cleaned_data.get('orcamento_total')
        if orcamento and orcamento < 100:
            raise forms.ValidationError("O orçamento mínimo é R$ 100,00")
        return orcamento

    def clean(self):
        """Validações customizadas do formulário."""
        cleaned_data = super().clean()
        orcamento = cleaned_data.get('orcamento_total')
        noites = cleaned_data.get('quantidade_noites')
        hospedes = cleaned_data.get('hospedes')

        # Calcular preço médio por dia para verificar viabilidade
        if orcamento and noites and hospedes:
            preco_medio_dia = orcamento / noites

            # Verificar se o orçamento é muito baixo
            if preco_medio_dia < 50:
                raise forms.ValidationError(
                    f"Seu orçamento resulta em R$ {preco_medio_dia:.2f} por dia. "
                    "Tente aumentar o orçamento ou diminuir a quantidade de noites."
                )

            # Verificar se o orçamento é muito alto
            if preco_medio_dia > 2000:
                self.add_error('orcamento_total',
                               "Orçamento muito alto. Você pode encontrar excelentes opções com valores menores.")

        return cleaned_data

    def get_budget_per_night(self):
        """Retorna o orçamento médio por noite."""
        if self.is_valid():
            data = self.cleaned_data
            return data['orcamento_total'] / data['quantidade_noites']
        return None

    def get_search_criteria(self):
        """Retorna critérios estruturados para a busca."""
        if not self.is_valid():
            return None

        data = self.cleaned_data

        # Calcular período de busca
        hoje = date.today()
        periodo_dias = int(data['periodo_busca'])
        data_limite = hoje + timedelta(days=periodo_dias)

        return {
            'orcamento_total': data['orcamento_total'],
            'orcamento_por_noite': self.get_budget_per_night(),
            'quantidade_noites': data['quantidade_noites'],
            'hospedes': data['hospedes'],
            'inclui_fim_de_semana': data['inclui_fim_de_semana'],
            'data_inicio_busca': hoje,
            'data_fim_busca': data_limite,
            'quartos_minimo': data.get('quartos_minimo'),
            'camas_minimo': data.get('camas_minimo'),
        }