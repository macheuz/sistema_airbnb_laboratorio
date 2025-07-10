# apps/core/urls.py - Adição das URLs do planejador de férias

from django.urls import path
from .views import (
    HomePageView,
    BairrosPorCidadeView,
    ResultadosBuscaView,
    DatasDisponiveisView,
    HospedesDisponiveisView,
    NoitesDisponiveisView,
    # Views para comparação (otimizadas)
    ComparacaoView,
    ComparacaoDataView,
    BairrosPorCidadeComparacaoView,
    # APIs específicas para comparação otimizada
    DatasDisponiveisComparacaoView,
    HospedesDisponiveisComparacaoView,
    NoitesDisponiveisComparacaoView,
    # NOVAS: Views para planejador de férias
    PlanejadorFeriasView,
    PlanejadorFeriasResultadosView
)

app_name = 'core'

urlpatterns = [
    # URL da página inicial
    path('', HomePageView.as_view(), name='home'),

    # URL para página de resultados
    path('resultados/', ResultadosBuscaView.as_view(), name='resultados_busca'),

    # URL para página de comparação
    path('comparacao/', ComparacaoView.as_view(), name='comparacao'),

    # URL para o planejador de férias
    path('planejador-ferias/', PlanejadorFeriasView.as_view(), name='planejador_ferias'),

    # --- URLs da API para filtros dinâmicos (busca normal) ---
    path('api/bairros/', BairrosPorCidadeView.as_view(), name='api_bairros_por_cidade'),
    path('api/datas-disponiveis/', DatasDisponiveisView.as_view(), name='api_datas_disponiveis'),
    path('api/hospedes-disponiveis/', HospedesDisponiveisView.as_view(), name='api_hospedes_disponiveis'),
    path('api/noites-disponiveis/', NoitesDisponiveisView.as_view(), name='api_noites_disponiveis'),

    # --- APIs específicas para comparação ---
    path('api/comparacao-data/', ComparacaoDataView.as_view(), name='api_comparacao_data'),
    path('api/bairros-comparacao/', BairrosPorCidadeComparacaoView.as_view(), name='api_bairros_comparacao'),

    # APIs para filtros dinâmicos de comparação
    path('api/datas-disponiveis-comparacao/', DatasDisponiveisComparacaoView.as_view(),
         name='api_datas_disponiveis_comparacao'),
    path('api/hospedes-disponiveis-comparacao/', HospedesDisponiveisComparacaoView.as_view(),
         name='api_hospedes_disponiveis_comparacao'),
    path('api/noites-disponiveis-comparacao/', NoitesDisponiveisComparacaoView.as_view(),
         name='api_noites_disponiveis_comparacao'),

    # API para o planejador de férias
    path('api/planejador-ferias/', PlanejadorFeriasResultadosView.as_view(), name='api_planejador_ferias'),
]