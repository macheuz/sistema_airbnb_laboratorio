import json
from django.core.cache import cache
from collections import defaultdict
from datetime import datetime, timedelta
from django.db.models import Avg, Count, F, Max, Min, Q, Case, When, IntegerField, Exists, OuterRef
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.functions import Extract
from django.http import JsonResponse
from django.views.generic import ListView, TemplateView, View
from datetime import datetime, timedelta, date
from apps.agendamento.models import Agendamento
from apps.imovel.models import Imovel
from apps.localizacoes.models import Bairro, Cidade
from .forms import AgendamentoForm, ComparacaoForm, PlanejadorFeriasForm


class ComparacaoView(TemplateView):
    """
    View para a página de comparação entre cidades/bairros.
    """
    template_name = "core/comparacao.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Buscar apenas cidades que têm agendamentos com dados
        cidades_com_dados = Cidade.objects.filter(
            imoveis_cidade__agendamentos__isnull=False,
            imoveis_cidade__agendamentos__data_checkin__gte=datetime.today()
        ).distinct().order_by('nome')

        context['cidades'] = cidades_com_dados
        return context


class BairrosPorCidadeComparacaoView(View):
    """
    API View para comparação que retorna apenas bairros que têm dados.
    """

    def get(self, request, *args, **kwargs):
        cidade_id = request.GET.get('cidade_id')
        if not cidade_id:
            return JsonResponse({'error': 'Cidade não especificada'}, status=400)

        try:
            # Buscar apenas bairros que têm agendamentos futuros
            bairros_com_dados = Bairro.objects.filter(
                cidade_id=cidade_id,
                imoveis_bairro__agendamentos__data_checkin__gte=datetime.today()
            ).distinct().order_by('nome').values('id', 'nome')

            return JsonResponse(list(bairros_com_dados), safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class DatasDisponiveisComparacaoView(View):
    """
    API View para retornar datas disponíveis para comparação.
    """

    def get(self, request, *args, **kwargs):
        cidade_1 = request.GET.get('cidade_1')
        bairro_1 = request.GET.get('bairro_1')
        cidade_2 = request.GET.get('cidade_2')
        bairro_2 = request.GET.get('bairro_2')

        if not all([cidade_1, cidade_2]):
            return JsonResponse({'error': 'Cidades não especificadas'}, status=400)

        try:
            # Construir filtros para ambas as localizações
            filtro_1 = Q(imovel__cidade_id=cidade_1, data_checkin__gte=datetime.today())
            if bairro_1:
                filtro_1 &= Q(imovel__bairro_id=bairro_1)

            filtro_2 = Q(imovel__cidade_id=cidade_2, data_checkin__gte=datetime.today())
            if bairro_2:
                filtro_2 &= Q(imovel__bairro_id=bairro_2)

            # Buscar datas que existem em AMBAS as localizações
            datas_local_1 = set(
                Agendamento.objects.filter(filtro_1)
                .values_list('data_checkin', flat=True)
                .distinct()
            )

            datas_local_2 = set(
                Agendamento.objects.filter(filtro_2)
                .values_list('data_checkin', flat=True)
                .distinct()
            )

            # Interseção - datas disponíveis em ambos os locais
            datas_comuns = datas_local_1.intersection(datas_local_2)

            # Formatar para o frontend
            datas_formatadas = sorted([
                d.strftime('%Y-%m-%d') for d in datas_comuns
            ])

            return JsonResponse(datas_formatadas, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class HospedesDisponiveisComparacaoView(View):
    """
    API View para retornar quantidade de hóspedes disponível para comparação.
    """

    def get(self, request, *args, **kwargs):
        cidade_1 = request.GET.get('cidade_1')
        bairro_1 = request.GET.get('bairro_1')
        cidade_2 = request.GET.get('cidade_2')
        bairro_2 = request.GET.get('bairro_2')
        data_checkin_str = request.GET.get('data_checkin')

        if not all([cidade_1, cidade_2, data_checkin_str]):
            return JsonResponse({'error': 'Parâmetros insuficientes'}, status=400)

        try:
            data_checkin = datetime.strptime(data_checkin_str, '%Y-%m-%d').date()

            # Construir filtros para ambas as localizações
            filtro_1 = Q(imovel__cidade_id=cidade_1, data_checkin=data_checkin)
            if bairro_1:
                filtro_1 &= Q(imovel__bairro_id=bairro_1)

            filtro_2 = Q(imovel__cidade_id=cidade_2, data_checkin=data_checkin)
            if bairro_2:
                filtro_2 &= Q(imovel__bairro_id=bairro_2)

            # Buscar hospedes que existem em AMBAS as localizações
            hospedes_local_1 = set(
                Agendamento.objects.filter(filtro_1)
                .values_list('hospedes', flat=True)
                .distinct()
            )

            hospedes_local_2 = set(
                Agendamento.objects.filter(filtro_2)
                .values_list('hospedes', flat=True)
                .distinct()
            )

            # Interseção - hospedes disponíveis em ambos os locais
            hospedes_comuns = sorted(hospedes_local_1.intersection(hospedes_local_2))

            return JsonResponse(hospedes_comuns, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class NoitesDisponiveisComparacaoView(View):
    """
    API View para retornar quantidade de noites disponível para comparação.
    """

    def get(self, request, *args, **kwargs):
        cidade_1 = request.GET.get('cidade_1')
        bairro_1 = request.GET.get('bairro_1')
        cidade_2 = request.GET.get('cidade_2')
        bairro_2 = request.GET.get('bairro_2')
        data_checkin_str = request.GET.get('data_checkin')
        hospedes = request.GET.get('hospedes')

        if not all([cidade_1, cidade_2, data_checkin_str, hospedes]):
            return JsonResponse({'error': 'Parâmetros insuficientes'}, status=400)

        try:
            data_checkin = datetime.strptime(data_checkin_str, '%Y-%m-%d').date()
            hospedes = int(hospedes)

            # Construir filtros para ambas as localizações
            filtro_1 = Q(
                imovel__cidade_id=cidade_1,
                data_checkin=data_checkin,
                hospedes__gte=hospedes
            )
            if bairro_1:
                filtro_1 &= Q(imovel__bairro_id=bairro_1)

            filtro_2 = Q(
                imovel__cidade_id=cidade_2,
                data_checkin=data_checkin,
                hospedes__gte=hospedes
            )
            if bairro_2:
                filtro_2 &= Q(imovel__bairro_id=bairro_2)

            # Calcular durações disponíveis em ambas as localizações
            duracoes_1 = set(
                Agendamento.objects.filter(filtro_1)
                .annotate(duracao_em_dias=F('data_checkout') - F('data_checkin'))
                .values_list('duracao_em_dias', flat=True)
            )

            duracoes_2 = set(
                Agendamento.objects.filter(filtro_2)
                .annotate(duracao_em_dias=F('data_checkout') - F('data_checkin'))
                .values_list('duracao_em_dias', flat=True)
            )

            # Converter para dias e encontrar interseção
            noites_1 = set([d.days for d in duracoes_1 if d and d.days > 0])
            noites_2 = set([d.days for d in duracoes_2 if d and d.days > 0])

            noites_comuns = sorted(noites_1.intersection(noites_2))

            return JsonResponse(noites_comuns, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class HomePageView(TemplateView):
    """
    View para a página inicial.
    Prepara os dados para popular os filtros do formulário de busca,
    consultando os modelos apropriados de forma otimizada.
    """
    template_name = "core/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fornece a lista de cidades para o primeiro campo do filtro
        context['cidades'] = Cidade.objects.all().order_by('nome')
        # Instancia o formulário para ser usado no template
        context['form'] = AgendamentoForm()
        return context


class BairrosPorCidadeView(View):
    """
    API View para retornar uma lista de bairros em formato JSON
    para uma determinada cidade, usada para popular o dropdown de bairros
    dinamicamente via AJAX.
    """

    def get(self, request, *args, **kwargs):
        cidade_id = request.GET.get('cidade_id')
        if not cidade_id:
            return JsonResponse({'error': 'Cidade não especificada'}, status=400)

        bairros = Bairro.objects.filter(cidade_id=cidade_id).order_by('nome').values('id', 'nome')
        return JsonResponse(list(bairros), safe=False)


class DatasDisponiveisView(View):
    """
    API View que retorna as datas de check-in disponíveis para uma cidade
    e opcionalmente para um bairro específico.
    """

    def get(self, request, *args, **kwargs):
        cidade_id = request.GET.get('cidade_id')
        bairro_id = request.GET.get('bairro_id')

        if not cidade_id:
            return JsonResponse({'error': 'Cidade não especificada'}, status=400)

        # Constrói o filtro baseado nos parâmetros fornecidos
        filtro = Q(imovel__cidade_id=cidade_id, data_checkin__gte=datetime.today())

        if bairro_id:
            filtro &= Q(imovel__bairro_id=bairro_id)

        # Busca apenas as datas de check-in distintas e futuras
        datas = Agendamento.objects.filter(filtro).values('data_checkin').distinct().order_by('data_checkin')

        # Formata as datas para o frontend (YYYY-MM-DD)
        datas_formatadas = [d['data_checkin'].strftime('%Y-%m-%d') for d in datas]
        return JsonResponse(datas_formatadas, safe=False)


class HospedesDisponiveisView(View):
    """
    API View que retorna a quantidade de hóspedes disponíveis para uma cidade/bairro e data.
    """

    def get(self, request, *args, **kwargs):
        cidade_id = request.GET.get('cidade_id')
        bairro_id = request.GET.get('bairro_id')
        data_checkin_str = request.GET.get('data_checkin')

        if not all([cidade_id, data_checkin_str]):
            return JsonResponse({'error': 'Parâmetros insuficientes'}, status=400)

        try:
            data_checkin = datetime.strptime(data_checkin_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Formato de data inválido'}, status=400)

        # Constrói o filtro baseado nos parâmetros fornecidos
        filtro = Q(imovel__cidade_id=cidade_id, data_checkin=data_checkin)

        if bairro_id:
            filtro &= Q(imovel__bairro_id=bairro_id)

        # Busca as quantidades de hóspedes distintas para os filtros selecionados
        hospedes = Agendamento.objects.filter(filtro).values_list('hospedes', flat=True).distinct().order_by('hospedes')

        return JsonResponse(list(hospedes), safe=False)


class NoitesDisponiveisView(View):
    """
    API View que retorna as durações de estadia (em noites) disponíveis
    baseado nos filtros anteriores.
    """

    def get(self, request, *args, **kwargs):
        cidade_id = request.GET.get('cidade_id')
        bairro_id = request.GET.get('bairro_id')
        data_checkin_str = request.GET.get('data_checkin')
        hospedes = request.GET.get('hospedes')

        if not all([cidade_id, data_checkin_str, hospedes]):
            return JsonResponse({'error': 'Parâmetros insuficientes'}, status=400)

        try:
            data_checkin = datetime.strptime(data_checkin_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Formato de data inválido'}, status=400)

        # Constrói o filtro baseado nos parâmetros fornecidos
        filtro = Q(imovel__cidade_id=cidade_id, data_checkin=data_checkin, hospedes__gte=hospedes)

        if bairro_id:
            filtro &= Q(imovel__bairro_id=bairro_id)

        # Filtra agendamentos com base nos parâmetros e calcula a duração da estadia
        duracoes = Agendamento.objects.filter(filtro).annotate(
            duracao_em_dias=F('data_checkout') - F('data_checkin')
        ).values_list('duracao_em_dias', flat=True).distinct()

        # Converte os objetos timedelta para inteiros (dias)
        noites = sorted([d.days for d in duracoes if d and d.days > 0])
        return JsonResponse(noites, safe=False)


class ResultadosBuscaView(ListView):
    model = Agendamento
    template_name = 'core/resultados.html'
    context_object_name = 'resultados'
    paginate_by = 12

    def get_queryset(self):
        # Cache key baseado nos parâmetros GET
        cache_key = f"results_{hash(frozenset(self.request.GET.items()))}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Query base com select_related para evitar queries excessivas
        queryset = Agendamento.objects.select_related(
            'imovel',
            'imovel__bairro',
            'imovel__cidade'
        ).prefetch_related(
            'anuncios',
            'imovel__avaliacoes'
        )

        # Validar formulário
        self.form = AgendamentoForm(self.request.GET)
        if not self.form.is_valid():
            return Agendamento.objects.none()

        data = self.form.cleaned_data

        # 1. FILTROS BÁSICOS

        # Filtro de localização
        if data.get('bairro'):
            queryset = queryset.filter(imovel__bairro_id=data['bairro'])
        elif data.get('cidade'):
            queryset = queryset.filter(imovel__cidade_id=data['cidade'])

        # Filtro de data
        if data.get('data_checkin'):
            queryset = queryset.filter(data_checkin=data['data_checkin'])

        # 2. FILTROS DE CAPACIDADE E DURAÇÃO

        # Filtro de hóspedes (>=)
        if data.get('hospedes'):
            queryset = queryset.filter(hospedes__gte=data['hospedes'])

        # Filtro de duração (quantidade de noites)
        if data.get('quantidade_noites'):
            queryset = queryset.annotate(
                duracao=F('data_checkout') - F('data_checkin')
            ).filter(
                duracao=timedelta(days=data['quantidade_noites'])
            )

        # 3. FILTROS DE PROPRIEDADES

        # Quartos (>=)
        if data.get('quartos'):
            quartos_filter = int(data['quartos'])
            if quartos_filter == 5:  # 5+ quartos
                queryset = queryset.filter(imovel__quartos__gte=5)
            else:
                queryset = queryset.filter(imovel__quartos__gte=quartos_filter)

        # Camas (>=)
        if data.get('camas'):
            camas_filter = int(data['camas'])
            if camas_filter == 5:  # 5+ camas
                queryset = queryset.filter(imovel__camas__gte=5)
            else:
                queryset = queryset.filter(imovel__camas__gte=camas_filter)

        #  Banheiros (>=)
        if data.get('banheiros'):
            banheiros_filter = int(data['banheiros'])
            if banheiros_filter == 3:  # 3+ banheiros
                queryset = queryset.filter(imovel__banheiros__gte=3)
            else:
                queryset = queryset.filter(imovel__banheiros__gte=banheiros_filter)

        # 4. FILTRO DE PREÇO
        if data.get('preco_maximo'):
            queryset = queryset.filter(preco_por_dia__lte=data['preco_maximo'])

        # 5. ORDENAÇÃO OTIMIZADA
        # Primeiro por preço, depois por avaliação
        queryset = queryset.order_by('preco_por_dia', '-imovel__avaliacoes__nota')

        # 6. APLICAR DISTINCT para evitar possíveis duplicatas
        queryset = queryset.distinct()

        # Cache por 10 minutos se a query for complexa
        if len(self.request.GET) > 3:  # Múltiplos filtros
            cache.set(cache_key, queryset, 600)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Cache para dados dos gráficos
        chart_cache_key = f"charts_{hash(frozenset(self.request.GET.items()))}"
        chart_data = cache.get(chart_cache_key)

        if chart_data is None:
            # Obter o queryset filtrado para os gráficos
            filtered_queryset = self.get_queryset()

            # Passar formulário e estatísticas básicas
            context['form'] = self.form
            context['total_resultados'] = filtered_queryset.count()
            context['query_params'] = self.request.GET.urlencode()

            # Gerar dados dos gráficos apenas se houver resultados
            if filtered_queryset.exists() and self.form.is_valid():
                chart_data = self._generate_chart_data_optimized(filtered_queryset)
                cache.set(chart_cache_key, chart_data, 600)  # Cache por 10 minutos
            else:
                chart_data = {
                    'chart_data_quartos_json': json.dumps([]),
                    'chart_data_camas_json': json.dumps([]),
                    'chart_data_tendencia_quartos_json': json.dumps([]),
                    'chart_data_tendencia_camas_json': json.dumps([])
                }

        context.update(chart_data)
        return context

    def _generate_chart_data_optimized(self, queryset):
        """
        Geração de dados para gráficos com agregações.
        """
        from django.db.models import Case, When, IntegerField

        # 1. Dados para gráfico de preços por quartos
        chart_data_quartos = list(
            queryset.filter(imovel__quartos__isnull=False)
            .annotate(
                quartos_agrupados=Case(
                    When(imovel__quartos__gte=4, then=4),
                    default=F('imovel__quartos'),
                    output_field=IntegerField()
                )
            )
            .values('quartos_agrupados')
            .annotate(
                preco_medio=Avg('preco_por_dia'),
                total_propriedades=Count('imovel', distinct=True)
            )
            .order_by('quartos_agrupados')
        )

        # 2. Dados para gráfico de preços por camas
        chart_data_camas = list(
            queryset.filter(imovel__camas__isnull=False)
            .annotate(
                camas_agrupadas=Case(
                    When(imovel__camas__gte=4, then=4),
                    default=F('imovel__camas'),
                    output_field=IntegerField()
                )
            )
            .values('camas_agrupadas')
            .annotate(
                preco_medio=Avg('preco_por_dia'),
                total_propriedades=Count('imovel', distinct=True)
            )
            .order_by('camas_agrupadas')
        )

        # 3. Dados de tendência mensal
        form_data = self.form.cleaned_data
        chart_data_tendencia_quartos = self._obter_tendencia_mensal_otimizada(
            form_data, 'imovel__quartos'
        )
        chart_data_tendencia_camas = self._obter_tendencia_mensal_otimizada(
            form_data, 'imovel__camas'
        )

        return {
            'chart_data_quartos_json': json.dumps(chart_data_quartos, default=str),
            'chart_data_camas_json': json.dumps(chart_data_camas, default=str),
            'chart_data_tendencia_quartos_json': json.dumps(chart_data_tendencia_quartos, default=str),
            'chart_data_tendencia_camas_json': json.dumps(chart_data_tendencia_camas, default=str)
        }

    def _obter_tendencia_mensal_otimizada(self, form_data, categoria_field):
        """
         tendência mensal.
        """
        data_checkin_usuario = form_data.get('data_checkin')
        if not data_checkin_usuario:
            return []

        # Usar apenas os últimos 30 dias para otimizar
        mes_busca = data_checkin_usuario.month
        ano_busca = data_checkin_usuario.year

        # Cache para essa query específica
        cache_key_trend = f"trend_{ano_busca}_{mes_busca}_{hash(str(form_data))}"
        cached_trend = cache.get(cache_key_trend)
        if cached_trend is not None:
            return cached_trend

        # Filtro base otimizado
        filtro_base = Q()
        if form_data.get('bairro'):
            filtro_base &= Q(imovel__bairro_id=form_data['bairro'])
        elif form_data.get('cidade'):
            filtro_base &= Q(imovel__cidade_id=form_data['cidade'])

        # Adicionar outros filtros essenciais
        if form_data.get('hospedes'):
            filtro_base &= Q(hospedes__gte=form_data['hospedes'])

        # Filtro de data para o mês
        filtro_mensal = filtro_base & Q(
            data_checkin__year=ano_busca,
            data_checkin__month=mes_busca,
            **{f'{categoria_field}__isnull': False}
        )

        dados_raw = list(
            Agendamento.objects.filter(filtro_mensal)
            .annotate(
                dia_mes=Extract('data_checkin', 'day'),
                categoria_agrupada=Case(
                    When(**{f'{categoria_field}__gte': 4}, then=4),
                    default=F(categoria_field),
                    output_field=IntegerField()
                )
            )
            .values('dia_mes', 'categoria_agrupada')
            .annotate(
                preco_medio=Avg('preco_por_dia'),
                total_propriedades=Count('imovel', distinct=True)
            )
            .order_by('dia_mes', 'categoria_agrupada')
        )

        # Processar dados para incluir linha de média geral
        resultado = []
        media_geral_por_dia = {}

        # Calcular média geral por dia
        for item in dados_raw:
            dia = item['dia_mes']
            if dia not in media_geral_por_dia:
                media_geral_por_dia[dia] = []
            media_geral_por_dia[dia].append(float(item['preco_medio'] or 0))

        # Adicionar dados por categoria
        for item in dados_raw:
            resultado.append({
                'dia_mes': item['dia_mes'],
                categoria_field: item['categoria_agrupada'],
                'preco_medio': float(item['preco_medio'] or 0),
                'total_opcoes': item['total_propriedades'],
                'is_media_geral': False
            })

        # Adicionar linha de média geral
        for dia, precos in media_geral_por_dia.items():
            if precos:
                resultado.append({
                    'dia_mes': dia,
                    categoria_field: 'media_geral',
                    'preco_medio': sum(precos) / len(precos),
                    'total_opcoes': len(precos),
                    'is_media_geral': True
                })

        # Cache por 30 minutos
        cache.set(cache_key_trend, resultado, 1800)
        return resultado


class ComparacaoDataView(View):
    """
    API View que retorna dados comparativos entre duas localizações.
    Agora usa a mesma lógica de filtros da busca principal.
    """

    def get(self, request, *args, **kwargs):
        # Validar dados usando o formulário
        form = ComparacaoForm(request.GET)

        if not form.is_valid():
            return JsonResponse({'error': 'Parâmetros inválidos', 'errors': form.errors}, status=400)

        try:
            # Obter informações das localizações
            location_info = form.get_location_info()

            # Construir filtros para cada localização usando a lógica corrigida
            agendamentos_1 = self._obter_agendamentos_filtrados(
                location_info['local_1'],
                location_info['data_checkin'],
                location_info['hospedes'],
                location_info['quantidade_noites']
            )

            agendamentos_2 = self._obter_agendamentos_filtrados(
                location_info['local_2'],
                location_info['data_checkin'],
                location_info['hospedes'],
                location_info['quantidade_noites']
            )

            # Obter dados para cada localização
            dados_local_1 = self._obter_dados_localizacao_comparacao(
                agendamentos_1,
                location_info['local_1'],
                location_info['hospedes'],
                location_info['quantidade_noites']
            )
            dados_local_2 = self._obter_dados_localizacao_comparacao(
                agendamentos_2,
                location_info['local_2'],
                location_info['hospedes'],
                location_info['quantidade_noites']
            )

            # Gerar gráfico de comparação de preços na data específica
            grafico_comparacao_data = self._gerar_grafico_comparacao_data(
                dados_local_1, dados_local_2, location_info['data_checkin']
            )

            # Estruturar resposta
            resposta = {
                'local_1': dados_local_1,
                'local_2': dados_local_2,
                'comparacao_geral': self._gerar_comparacao_geral(dados_local_1, dados_local_2),
                'grafico_comparacao_data': grafico_comparacao_data,
                'parametros_busca': {
                    'data_checkin': location_info['data_checkin'].isoformat(),
                    'hospedes': location_info['hospedes'],
                    'quantidade_noites': location_info['quantidade_noites']
                }
            }

            return JsonResponse(resposta, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def _obter_agendamentos_filtrados(self, location_info, data_checkin, hospedes, quantidade_noites):
        """
        Obtém agendamentos usando a mesma lógica da busca principal.
        """
        # Query base
        queryset = Agendamento.objects.select_related(
            'imovel', 'imovel__bairro', 'imovel__cidade'
        ).prefetch_related(
            'anuncios', 'imovel__avaliacoes'
        )

        # Filtro por localização
        if location_info['tipo'] == 'bairro':
            queryset = queryset.filter(imovel__bairro_id=location_info['id'])
        elif location_info['tipo'] == 'cidade':
            queryset = queryset.filter(imovel__cidade_id=location_info['cidade_id'])

        # Filtro por data de check-in
        queryset = queryset.filter(data_checkin=data_checkin)

        # Filtro por hóspedes (>=)
        queryset = queryset.filter(hospedes__gte=hospedes)

        # Filtro por duração da estadia (quantidade de noites)
        queryset = queryset.annotate(
            duracao=F('data_checkout') - F('data_checkin')
        ).filter(
            duracao=timedelta(days=quantidade_noites)
        )

        return queryset

    def _obter_dados_localizacao_comparacao(self, queryset, location_info, hospedes, quantidade_noites):
        """
        Obtém todos os dados necessários para uma localização na comparação.
        """
        # Informações básicas da localização
        if location_info['tipo'] == 'cidade':
            local_obj = Cidade.objects.get(id=location_info['cidade_id'])
            nome_local = f"{local_obj.nome}, {local_obj.estado}"
        else:
            local_obj = Bairro.objects.get(id=location_info['id'])
            nome_local = f"{local_obj.nome}, {local_obj.cidade.nome}"

        # 1. Preços por quartos ao longo do ano
        precos_quartos_ano = self._obter_precos_ano_por_categoria(
            location_info, 'imovel__quartos', hospedes, quantidade_noites
        )

        # 2. Preços por camas ao longo do ano
        precos_camas_ano = self._obter_precos_ano_por_categoria(
            location_info, 'imovel__camas', hospedes, quantidade_noites
        )

        # 3. Preços para a data específica por quartos e camas
        precos_data_quartos_raw = list(
            queryset.filter(imovel__quartos__isnull=False)
            .annotate(
                quartos_agrupados=Case(
                    When(imovel__quartos__gte=4, then=4),
                    default=F('imovel__quartos'),
                    output_field=IntegerField()
                )
            )
            .values('quartos_agrupados')
            .annotate(preco_medio=Avg('preco_por_dia'))
            .order_by('quartos_agrupados')
        )

        precos_data_camas_raw = list(
            queryset.filter(imovel__camas__isnull=False)
            .annotate(
                camas_agrupadas=Case(
                    When(imovel__camas__gte=4, then=4),
                    default=F('imovel__camas'),
                    output_field=IntegerField()
                )
            )
            .values('camas_agrupadas')
            .annotate(preco_medio=Avg('preco_por_dia'))
            .order_by('camas_agrupadas')
        )

        # Converter para formato JSON-safe
        precos_data_quartos = []
        for item in precos_data_quartos_raw:
            precos_data_quartos.append({
                'quartos_agrupados': item['quartos_agrupados'],
                'preco_medio': float(item['preco_medio'] or 0)
            })

        precos_data_camas = []
        for item in precos_data_camas_raw:
            precos_data_camas.append({
                'camas_agrupadas': item['camas_agrupadas'],
                'preco_medio': float(item['preco_medio'] or 0)
            })

        # 4. Top 10 acomodações mais baratas
        acomodacoes_raw = list(
            queryset.values(
                'imovel__id',
                'imovel__tipo_acomodacao',
                'imovel__quartos',
                'imovel__camas',
                'imovel__banheiros',
                'anuncios__titulo',
                'anuncios__link'
            )
            .annotate(
                preco_medio=Avg('preco_por_dia'),
                avaliacao_media=Avg('imovel__avaliacoes__nota'),
                total_avaliacoes=Avg('imovel__avaliacoes__qtd_avaliacoes')
            )
            .order_by('preco_medio')[:10]
        )

        # Converter valores para tipos seguros para JSON
        acomodacoes_baratas = []
        for item in acomodacoes_raw:
            acomodacao = {
                'imovel__id': item['imovel__id'],
                'imovel__tipo_acomodacao': item['imovel__tipo_acomodacao'],
                'imovel__quartos': item['imovel__quartos'] or 0,
                'imovel__camas': item['imovel__camas'] or 0,
                'imovel__banheiros': item['imovel__banheiros'] or 0,
                'anuncios__titulo': item['anuncios__titulo'],
                'anuncios__link': item['anuncios__link'],
                'preco_medio': float(item['preco_medio'] or 0),
                'avaliacao_media': float(item['avaliacao_media']) if item['avaliacao_media'] else None,
                'total_avaliacoes': float(item['total_avaliacoes']) if item['total_avaliacoes'] else None
            }
            acomodacoes_baratas.append(acomodacao)

        # 5. Estatísticas gerais
        if queryset.exists():
            estatisticas_raw = queryset.aggregate(
                preco_medio_geral=Avg('preco_por_dia'),
                preco_minimo=Min('preco_por_dia'),
                preco_maximo=Max('preco_por_dia'),
                total_propriedades=Count('imovel', distinct=True),
                total_agendamentos=Count('id')
            )

            # Garantir que todos os valores sejam convertidos para float ou int
            estatisticas = {
                'preco_medio_geral': float(estatisticas_raw['preco_medio_geral'] or 0),
                'preco_minimo': float(estatisticas_raw['preco_minimo'] or 0),
                'preco_maximo': float(estatisticas_raw['preco_maximo'] or 0),
                'total_propriedades': int(estatisticas_raw['total_propriedades'] or 0),
                'total_agendamentos': int(estatisticas_raw['total_agendamentos'] or 0)
            }
        else:
            estatisticas = {
                'preco_medio_geral': 0.0,
                'preco_minimo': 0.0,
                'preco_maximo': 0.0,
                'total_propriedades': 0,
                'total_agendamentos': 0
            }

        return {
            'nome': nome_local,
            'tipo': location_info['tipo'],
            'id': location_info['id'],
            'precos_quartos_ano': precos_quartos_ano,
            'precos_camas_ano': precos_camas_ano,
            'precos_data_quartos': precos_data_quartos,
            'precos_data_camas': precos_data_camas,
            'acomodacoes_baratas': acomodacoes_baratas,
            'estatisticas': estatisticas
        }

    def _obter_precos_ano_por_categoria(self, location_info, categoria_field, hospedes, quantidade_noites):
        """
        Obtém preços ao longo do ano para uma categoria (quartos ou camas).
        """
        # Construir filtro base para o ano
        filtro_ano = Q(
            data_checkin__year=datetime.now().year,
            hospedes__gte=hospedes
        )

        # Adicionar filtro de localização
        if location_info['tipo'] == 'cidade':
            filtro_ano &= Q(imovel__cidade_id=location_info['cidade_id'])
        else:
            filtro_ano &= Q(imovel__bairro_id=location_info['id'])

        # Filtrar valores nulos da categoria
        filtro_ano &= Q(**{f'{categoria_field}__isnull': False})

        # Buscar dados agrupados por mês e categoria
        dados_raw = Agendamento.objects.filter(filtro_ano).annotate(
            mes=Extract('data_checkin', 'month'),
            duracao_dias=F('data_checkout') - F('data_checkin')
        ).filter(
            duracao_dias=timedelta(days=quantidade_noites)
        ).annotate(
            categoria_agrupada=Case(
                When(**{f'{categoria_field}__gte': 4}, then=4),
                default=F(categoria_field),
                output_field=IntegerField()
            )
        ).values('mes', 'categoria_agrupada').annotate(
            preco_medio=Avg('preco_por_dia'),
            total_propriedades=Count('imovel', distinct=True)
        ).order_by('mes', 'categoria_agrupada')

        # Converter para formato JSON-safe
        dados = []
        for item in dados_raw:
            dados.append({
                'mes': item['mes'],
                'categoria_agrupada': item['categoria_agrupada'],
                'preco_medio': float(item['preco_medio'] or 0),
                'total_propriedades': int(item['total_propriedades'] or 0)
            })

        return dados

    def _gerar_grafico_comparacao_data(self, dados_1, dados_2, data_checkin):
        """Gera dados para o gráfico de comparação de preços na data específica."""
        return {
            'data_checkin': data_checkin.isoformat(),
            'local_1_quartos': dados_1['precos_data_quartos'],
            'local_1_camas': dados_1['precos_data_camas'],
            'local_2_quartos': dados_2['precos_data_quartos'],
            'local_2_camas': dados_2['precos_data_camas']
        }

    def _gerar_comparacao_geral(self, dados_1, dados_2):
        """
        Gera insights comparativos entre as duas localizações.
        """
        est_1 = dados_1['estatisticas']
        est_2 = dados_2['estatisticas']

        # Verificar se há dados suficientes
        if not est_1['preco_medio_geral'] or not est_2['preco_medio_geral']:
            return {
                'erro': True,
                'economia_potencial': 0,
                'diferenca_preco_percentual': 0,
                'local_mais_barato': 'N/A',
                'recomendacao': 'Não há dados suficientes para as condições especificadas. Tente ajustar os filtros de data, hóspedes ou duração.'
            }

        # Calcular diferenças percentuais
        preco_1 = float(est_1['preco_medio_geral'])
        preco_2 = float(est_2['preco_medio_geral'])

        diff_preco_medio = ((preco_2 - preco_1) / preco_1 * 100) if preco_1 else 0
        diff_propriedades = est_2['total_propriedades'] - est_1['total_propriedades']

        # Determinar qual é mais barato
        local_mais_barato = dados_1['nome'] if preco_1 < preco_2 else dados_2['nome']

        # Economia potencial
        economia_potencial = abs(preco_1 - preco_2)

        return {
            'erro': False,
            'diferenca_preco_percentual': round(abs(diff_preco_medio), 2),
            'diferenca_propriedades': diff_propriedades,
            'local_mais_barato': local_mais_barato,
            'economia_potencial': float(economia_potencial),
            'recomendacao': self._gerar_recomendacao_corrigida(dados_1, dados_2, preco_1, preco_2)
        }

    def _gerar_recomendacao_corrigida(self, dados_1, dados_2, preco_1, preco_2):
        """
        Gera uma recomendação baseada nos dados comparativos.
        """
        diferenca_percentual = abs(preco_1 - preco_2) / min(preco_1, preco_2) * 100

        if diferenca_percentual < 5:
            return f"Os preços são muito similares entre {dados_1['nome']} e {dados_2['nome']} (diferença de {diferenca_percentual:.1f}%). Considere outros fatores como localização e comodidades."
        elif preco_1 < preco_2:
            economia = preco_2 - preco_1
            return f"✅ {dados_1['nome']} é {diferenca_percentual:.1f}% mais barato que {dados_2['nome']}, com economia média de R$ {economia:.2f} por dia."
        else:
            economia = preco_1 - preco_2
            return f"✅ {dados_2['nome']} é {diferenca_percentual:.1f}% mais barato que {dados_1['nome']}, com economia média de R$ {economia:.2f} por dia."


class PlanejadorFeriasView(TemplateView):
    """View principal para o planejador de férias."""
    template_name = "core/planejador_ferias.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PlanejadorFeriasForm()
        context['estatisticas_rapidas'] = self._obter_estatisticas_rapidas_cache()
        return context

    def _obter_estatisticas_rapidas_cache(self):
        """Obtém estatísticas com cache de 1 hora."""
        cache_key = 'vacation_quick_stats'
        stats = cache.get(cache_key)

        if stats is None:
            hoje = date.today()
            proximos_30_dias = hoje + timedelta(days=30)

            # Query com agregação direta
            stats_raw = Agendamento.objects.filter(
                data_checkin__gte=hoje,
                data_checkin__lte=proximos_30_dias
            ).aggregate(
                preco_medio_dia=Avg('preco_por_dia'),
                preco_minimo_dia=Min('preco_por_dia'),
                preco_maximo_dia=Max('preco_por_dia'),
                total_opcoes=Count('id'),
                total_cidades=Count('imovel__cidade', distinct=True)
            )

            if stats_raw['preco_medio_dia']:
                stats = {
                    'preco_medio_dia': round(float(stats_raw['preco_medio_dia']), 2),
                    'preco_minimo_dia': round(float(stats_raw['preco_minimo_dia']), 2),
                    'preco_maximo_dia': round(float(stats_raw['preco_maximo_dia']), 2),
                    'total_opcoes': stats_raw['total_opcoes'],
                    'total_cidades': stats_raw['total_cidades'],
                    'orcamento_sugerido_3_noites': round(float(stats_raw['preco_medio_dia']) * 3, 2),
                    'orcamento_sugerido_7_noites': round(float(stats_raw['preco_medio_dia']) * 7, 2),
                }
            else:
                stats = {
                    'preco_medio_dia': 0, 'preco_minimo_dia': 0, 'preco_maximo_dia': 0,
                    'total_opcoes': 0, 'total_cidades': 0,
                    'orcamento_sugerido_3_noites': 0, 'orcamento_sugerido_7_noites': 0,
                }

            # Cache por 1 hora
            cache.set(cache_key, stats, 3600)

        return stats


class PlanejadorFeriasResultadosView(View):
    """API View para busca de férias."""

    def get(self, request, *args, **kwargs):
        form = PlanejadorFeriasForm(request.GET)

        if not form.is_valid():
            return JsonResponse({'error': 'Parâmetros inválidos', 'errors': form.errors}, status=400)

        try:
            criterios = form.get_search_criteria()

            # Busca em etapas para reduzir carga
            opcoes_viagem = self._buscar_opcoes_otimizado(criterios)

            if not opcoes_viagem:
                return JsonResponse({
                    'success': True,
                    'total_opcoes': 0,
                    'resultados_por_cidade': [],
                    'estatisticas': self._stats_vazias(),
                    'sugestoes': [{'tipo': 'sem_resultados', 'titulo': 'Nenhuma opção encontrada',
                                   'descricao': 'Tente aumentar seu orçamento ou período.', 'acao': 'Ajustar'}]
                })

            # Organizar e processar apenas o necessário
            resultados_organizados = self._organizar_resultados_otimizado(opcoes_viagem)
            estatisticas = self._gerar_estatisticas_rapidas(opcoes_viagem, criterios)
            sugestoes = self._gerar_sugestoes_rapidas(opcoes_viagem, criterios)

            return JsonResponse({
                'success': True,
                'criterios_busca': self._serializar_criterios(criterios),
                'total_opcoes': len(opcoes_viagem),
                'resultados_por_cidade': resultados_organizados,
                'estatisticas': estatisticas,
                'sugestoes': sugestoes,
            }, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def _buscar_opcoes_otimizado(self, criterios):
        """Busca com filtros em ordem de seletividade."""

        # ETAPA 1: Filtros mais seletivos primeiro
        preco_maximo_por_dia = float(criterios['orcamento_total']) / criterios['quantidade_noites']

        # Query base
        base_query = Agendamento.objects.select_related(
            'imovel__cidade', 'imovel__bairro'
        ).filter(
            # Filtros seletivos
            preco_por_dia__lte=preco_maximo_por_dia,
            data_checkin__gte=criterios['data_inicio_busca'],
            data_checkin__lte=criterios['data_fim_busca'],
            hospedes__gte=criterios['hospedes']
        ).annotate(
            duracao_noites=F('data_checkout') - F('data_checkin')
        ).filter(
            duracao_noites=timedelta(days=criterios['quantidade_noites'])
        )

        # ETAPA 2: Filtros opcionais
        if criterios.get('quartos_minimo'):
            base_query = base_query.filter(imovel__quartos__gte=criterios['quartos_minimo'])

        if criterios.get('camas_minimo'):
            base_query = base_query.filter(imovel__camas__gte=criterios['camas_minimo'])

        # ETAPA 3: Ordenar por economia e limitar resultados iniciais
        base_query = base_query.order_by('preco_por_dia')[:2000]  # Limitado para performance

        # ETAPA 4: Processar filtro de fim de semana apenas se necessário
        if criterios['inclui_fim_de_semana']:
            agendamentos_fds = []
            for agendamento in base_query:
                data_checkout = agendamento.data_checkin + timedelta(days=criterios['quantidade_noites'])
                if self._inclui_fim_de_semana_rapido(agendamento.data_checkin, data_checkout):
                    agendamentos_fds.append(agendamento)
            agendamentos_finais = agendamentos_fds
        else:
            agendamentos_finais = list(base_query)

        # ETAPA 5: Processar opções (limitado a 1000 para performance)
        opcoes = []

        # Coletar IDs dos agendamentos para busca em lote dos anúncios
        agendamento_ids = [ag.id for ag in agendamentos_finais[:1000]]

        # Buscar anúncios em uma única query usando prefetch em lote
        anuncios_dict = {}
        if agendamento_ids:
            from apps.anuncios.models import Anuncio
            anuncios_queryset = Anuncio.objects.filter(
                agendamento_id__in=agendamento_ids
            ).select_related('agendamento')

            for anuncio in anuncios_queryset:
                anuncios_dict[anuncio.agendamento_id] = anuncio

        for agendamento in agendamentos_finais[:1000]:
            preco_total = float(agendamento.preco_por_dia) * criterios['quantidade_noites']

            if preco_total <= float(criterios['orcamento_total']):
                data_checkout = agendamento.data_checkin + timedelta(days=criterios['quantidade_noites'])

                # Buscar anúncio do dicionário pré-carregado
                anuncio = anuncios_dict.get(agendamento.id)

                opcao = {
                    'cidade_nome': agendamento.imovel.cidade.nome,
                    'cidade_estado': agendamento.imovel.cidade.estado,
                    'cidade_id': agendamento.imovel.cidade.id,
                    'bairro_nome': agendamento.imovel.bairro.nome,
                    'bairro_id': agendamento.imovel.bairro.id,
                    'data_checkin': agendamento.data_checkin.isoformat(),
                    'data_checkout': data_checkout.isoformat(),
                    'preco_total': preco_total,
                    'economia': float(criterios['orcamento_total']) - preco_total,
                    'preco_por_dia': float(agendamento.preco_por_dia),
                    'hospedes': agendamento.hospedes,
                    'inclui_fim_de_semana': criterios['inclui_fim_de_semana'] if criterios[
                        'inclui_fim_de_semana'] else self._inclui_fim_de_semana_rapido(agendamento.data_checkin,
                                                                                       data_checkout),
                    'tipo_acomodacao': agendamento.imovel.tipo_acomodacao or 'Acomodação',
                    # Dados básicos do imóvel
                    'imovel': {
                        'quartos': agendamento.imovel.quartos or 0,
                        'camas': agendamento.imovel.camas or 0,
                        'banheiros': agendamento.imovel.banheiros or 0,
                        'tipo_acomodacao': agendamento.imovel.tipo_acomodacao or 'N/A',
                    },
                    # Dados do anúncio sem queries adicionais
                    'anuncio': {
                        'titulo': anuncio.titulo if anuncio else (agendamento.imovel.tipo_acomodacao or 'Acomodação'),
                        'link': anuncio.link if anuncio and anuncio.link else None
                    }
                }

                # LAZY LOADING: Carregar avaliação apenas quando necessário (comentado para performance)
                # Pode ser ativado se necessário, mas adiciona queries
                opcao['avaliacao'] = {'nota': None, 'quantidade': 0}

                opcoes.append(opcao)

        return opcoes

    def _inclui_fim_de_semana_rapido(self, data_inicio, data_fim):
        """Verificação rápida de fim de semana."""
        if (data_fim - data_inicio).days < 2:
            return False

        # Verificar apenas alguns dias para otimizar
        for i in range(min(7, (data_fim - data_inicio).days)):
            dia = data_inicio + timedelta(days=i)
            if dia.weekday() == 5:  # Sábado
                # Verificar se também tem domingo
                if (dia + timedelta(days=1)) < data_fim and (dia + timedelta(days=1)).weekday() == 6:
                    return True
        return False

    def _organizar_resultados_otimizado(self, opcoes):
        """Organização usando defaultdict e processamento em lote."""
        if not opcoes:
            return []

        # Agrupar por cidade/bairro usando defaultdict para performance
        cidades = defaultdict(lambda: {
            'cidade_nome': '',
            'estado': '',
            'cidade_id': 0,
            'total_opcoes': 0,
            'precos': [],
            'economias': [],
            'bairros': defaultdict(lambda: {
                'bairro_nome': '',
                'bairro_id': 0,
                'opcoes': [],
                'precos': [],
                'economias': []
            })
        })

        # Processar opcoes em um único loop
        for opcao in opcoes:
            cidade_key = opcao['cidade_nome']
            bairro_key = opcao['bairro_nome']

            cidade = cidades[cidade_key]
            if not cidade['cidade_nome']:  # Inicializar apenas uma vez
                cidade.update({
                    'cidade_nome': opcao['cidade_nome'],
                    'estado': opcao['cidade_estado'],
                    'cidade_id': opcao['cidade_id']
                })

            bairro = cidade['bairros'][bairro_key]
            if not bairro['bairro_nome']:  # Inicializar apenas uma vez
                bairro.update({
                    'bairro_nome': opcao['bairro_nome'],
                    'bairro_id': opcao['bairro_id']
                })

            # Adicionar aos dados de agregação
            preco = opcao['preco_total']
            economia = opcao['economia']

            cidade['precos'].append(preco)
            cidade['economias'].append(economia)
            bairro['precos'].append(preco)
            bairro['economias'].append(economia)
            bairro['opcoes'].append(opcao)

        # Calcular estatísticas e formatar resultado final
        resultado = []
        for cidade_data in cidades.values():
            # Stats da cidade
            precos_cidade = cidade_data['precos']
            economias_cidade = cidade_data['economias']

            cidade_final = {
                'cidade_nome': cidade_data['cidade_nome'],
                'estado': cidade_data['estado'],
                'cidade_id': cidade_data['cidade_id'],
                'total_opcoes': len(precos_cidade),
                'preco_medio': sum(precos_cidade) / len(precos_cidade) if precos_cidade else 0,
                'preco_minimo': min(precos_cidade) if precos_cidade else 0,
                'economia_media': sum(economias_cidade) / len(economias_cidade) if economias_cidade else 0,
                'bairros': {}
            }

            # Processar bairros
            for bairro_data in cidade_data['bairros'].values():
                precos_bairro = bairro_data['precos']
                economias_bairro = bairro_data['economias']
                opcoes_bairro = bairro_data['opcoes']

                # Ordenar por economia e manter top 3 para performance
                opcoes_bairro.sort(key=lambda x: x['economia'], reverse=True)

                cidade_final['bairros'][bairro_data['bairro_nome']] = {
                    'bairro_nome': bairro_data['bairro_nome'],
                    'bairro_id': bairro_data['bairro_id'],
                    'total_opcoes': len(opcoes_bairro),
                    'preco_medio': sum(precos_bairro) / len(precos_bairro) if precos_bairro else 0,
                    'preco_minimo': min(precos_bairro) if precos_bairro else 0,
                    'economia_media': sum(economias_bairro) / len(economias_bairro) if economias_bairro else 0,
                    'opcoes': opcoes_bairro[:3]  # Top 3 por bairro para performance
                }

            resultado.append(cidade_final)

        # Ordenar cidades por economia média
        resultado.sort(key=lambda x: x['economia_media'], reverse=True)
        return resultado[:10]  # Top 10 cidades para performance

    def _gerar_estatisticas_rapidas(self, opcoes, criterios):
        """Estatísticas otimizadas com cálculos em lote."""
        if not opcoes:
            return self._stats_vazias()

        # Cálculos em vetores para performance
        precos = [o['preco_total'] for o in opcoes]
        economias = [o['economia'] for o in opcoes]

        # Sets para contagem única
        cidades_unicas = {o['cidade_nome'] for o in opcoes}
        bairros_unicos = {(o['cidade_nome'], o['bairro_nome']) for o in opcoes}

        # Contagem condicional otimizada
        opcoes_fds = sum(1 for o in opcoes if o['inclui_fim_de_semana'])

        preco_medio = sum(precos) / len(precos)
        economia_media = sum(economias) / len(economias)
        percentual_usado = (preco_medio / float(criterios['orcamento_total'])) * 100

        return {
            'total_opcoes': len(opcoes),
            'total_cidades': len(cidades_unicas),
            'total_bairros': len(bairros_unicos),
            'economia_media': round(economia_media, 2),
            'economia_maxima': round(max(economias), 2),
            'preco_medio': round(preco_medio, 2),
            'opcoes_com_fim_de_semana': opcoes_fds,
            'percentual_orcamento_usado': round(percentual_usado, 1)
        }

    def _gerar_sugestoes_rapidas(self, opcoes, criterios):
        """Sugestões"""
        if not opcoes:
            return [{'tipo': 'sem_resultados', 'titulo': 'Nenhuma opção encontrada',
                     'descricao': 'Tente aumentar seu orçamento ou período.', 'acao': 'Ajustar'}]

        sugestoes = []
        economia_media = sum(o['economia'] for o in opcoes) / len(opcoes)

        if economia_media > 100:
            sugestoes.append({
                'tipo': 'economia',
                'titulo': f'Economia média de R$ {economia_media:.2f}',
                'descricao': 'Seu orçamento permite encontrar ótimas opções!',
                'acao': 'Ver opções'
            })

        opcoes_fds = sum(1 for o in opcoes if o['inclui_fim_de_semana'])
        if opcoes_fds > 0:
            sugestoes.append({
                'tipo': 'fim_de_semana',
                'titulo': f'{opcoes_fds} opções incluem fim de semana',
                'descricao': 'Perfeito para relaxar!',
                'acao': 'Ver opções'
            })

        # Cidade com melhor economia (sample de 50 para performance)
        sample_opcoes = opcoes[:50]
        cidades_economia = defaultdict(list)
        for opcao in sample_opcoes:
            cidades_economia[opcao['cidade_nome']].append(opcao['economia'])

        if cidades_economia:
            melhor_cidade = max(cidades_economia.items(),
                                key=lambda x: sum(x[1]) / len(x[1]))
            sugestoes.append({
                'tipo': 'destino_recomendado',
                'titulo': f'{melhor_cidade[0]} oferece boa economia',
                'descricao': f'Entre as opções analisadas',
                'acao': 'Ver opções'
            })

        return sugestoes

    def _stats_vazias(self):
        """Retorna estrutura de estatísticas vazia."""
        return {
            'total_opcoes': 0, 'total_cidades': 0, 'total_bairros': 0,
            'economia_media': 0, 'economia_maxima': 0, 'preco_medio': 0,
            'opcoes_com_fim_de_semana': 0, 'percentual_orcamento_usado': 0
        }

    def _serializar_criterios(self, criterios):
        """Serializa critérios para JSON."""
        return {
            'orcamento_total': float(criterios['orcamento_total']),
            'orcamento_por_noite': float(criterios['orcamento_por_noite']),
            'quantidade_noites': criterios['quantidade_noites'],
            'hospedes': criterios['hospedes'],
            'inclui_fim_de_semana': criterios['inclui_fim_de_semana'],
            'data_inicio_busca': criterios['data_inicio_busca'].isoformat(),
            'data_fim_busca': criterios['data_fim_busca'].isoformat(),
        }


class HomePageView(TemplateView):
    """View para a página inicial."""
    template_name = "core/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cidades'] = Cidade.objects.all().order_by('nome')
        context['form'] = AgendamentoForm()
        return context


class BairrosPorCidadeView(View):
    """API View para retornar uma lista de bairros por cidade."""

    def get(self, request, *args, **kwargs):
        cidade_id = request.GET.get('cidade_id')
        if not cidade_id:
            return JsonResponse({'error': 'Cidade não especificada'}, status=400)

        bairros = Bairro.objects.filter(cidade_id=cidade_id).order_by('nome').values('id', 'nome')
        return JsonResponse(list(bairros), safe=False)


class DatasDisponiveisView(View):
    """API View que retorna as datas de check-in disponíveis."""

    def get(self, request, *args, **kwargs):
        cidade_id = request.GET.get('cidade_id')
        bairro_id = request.GET.get('bairro_id')

        if not cidade_id:
            return JsonResponse({'error': 'Cidade não especificada'}, status=400)

        filtro = Q(imovel__cidade_id=cidade_id, data_checkin__gte=datetime.today())

        if bairro_id:
            filtro &= Q(imovel__bairro_id=bairro_id)

        datas = Agendamento.objects.filter(filtro).values('data_checkin').distinct().order_by('data_checkin')
        datas_formatadas = [d['data_checkin'].strftime('%Y-%m-%d') for d in datas]
        return JsonResponse(datas_formatadas, safe=False)


class HospedesDisponiveisView(View):
    """API View que retorna a quantidade de hóspedes disponíveis."""

    def get(self, request, *args, **kwargs):
        cidade_id = request.GET.get('cidade_id')
        bairro_id = request.GET.get('bairro_id')
        data_checkin_str = request.GET.get('data_checkin')

        if not all([cidade_id, data_checkin_str]):
            return JsonResponse({'error': 'Parâmetros insuficientes'}, status=400)

        try:
            data_checkin = datetime.strptime(data_checkin_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Formato de data inválido'}, status=400)

        filtro = Q(imovel__cidade_id=cidade_id, data_checkin=data_checkin)

        if bairro_id:
            filtro &= Q(imovel__bairro_id=bairro_id)

        hospedes = Agendamento.objects.filter(filtro).values_list('hospedes', flat=True).distinct().order_by('hospedes')
        return JsonResponse(list(hospedes), safe=False)


class NoitesDisponiveisView(View):
    """API View que retorna as durações de estadia disponíveis."""

    def get(self, request, *args, **kwargs):
        cidade_id = request.GET.get('cidade_id')
        bairro_id = request.GET.get('bairro_id')
        data_checkin_str = request.GET.get('data_checkin')
        hospedes = request.GET.get('hospedes')

        if not all([cidade_id, data_checkin_str, hospedes]):
            return JsonResponse({'error': 'Parâmetros insuficientes'}, status=400)

        try:
            data_checkin = datetime.strptime(data_checkin_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Formato de data inválido'}, status=400)

        filtro = Q(imovel__cidade_id=cidade_id, data_checkin=data_checkin, hospedes__gte=hospedes)

        if bairro_id:
            filtro &= Q(imovel__bairro_id=bairro_id)

        duracoes = Agendamento.objects.filter(filtro).annotate(
            duracao_em_dias=F('data_checkout') - F('data_checkin')
        ).values_list('duracao_em_dias', flat=True).distinct()

        noites = sorted([d.days for d in duracoes if d and d.days > 0])
        return JsonResponse(noites, safe=False)

