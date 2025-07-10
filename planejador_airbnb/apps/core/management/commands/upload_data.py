import csv
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from apps.core.models import Imovel


# --- Funções Auxiliares de Limpeza (Helpers) ---
# Estas funções continuam as mesmas, pois são essenciais para o tratamento dos dados.

def _clean_decimal(value_str):
    """Tenta converter uma string de preço/avaliação para Decimal. Retorna None em caso de falha."""
    if not value_str:
        return None
    try:
        cleaned_str = str(value_str).replace('R$', '').replace('.', '').replace(',', '.').strip()
        return Decimal(cleaned_str) if cleaned_str else None
    except InvalidOperation:
        return None


def _clean_integer(value_str):
    """Extrai um número inteiro de uma string. Retorna None se não encontrar."""
    if value_str is None or value_str == '':
        return None
    try:
        # Tenta a conversão direta que é mais rápida.
        return int(float(str(value_str).strip()))
    except (ValueError, TypeError):
        # Usa regex como fallback para casos como '2 hóspedes'.
        numbers = re.findall(r'\d+', str(value_str))
        return int(numbers[0]) if numbers else None


def _clean_date(value_str, date_format='%d/%m/%Y'):
    """Converte string de data para objeto date. Retorna None em caso de falha."""
    if not value_str:
        return None
    try:
        return datetime.strptime(value_str, date_format).date()
    except (ValueError, TypeError):
        return None


class Command(BaseCommand):
    help = 'Adiciona todos os imóveis de um arquivo CSV ao banco de dados sem apagar dados existentes.'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='O caminho completo para o arquivo CSV.')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                imoveis_para_adicionar = []

                self.stdout.write(self.style.NOTICE(f'Lendo arquivo para adicionar novos registros: {file_path}...'))

                for i, row in enumerate(reader, 1):
                    # Validações críticas para garantir a integridade mínima do registro
                    id_imovel_str = row.get('ID Imóvel')
                    if not id_imovel_str or not id_imovel_str.isdigit():
                        self.stdout.write(
                            self.style.WARNING(f"Linha {i}: ID do Imóvel ausente ou inválido. LINHA IGNORADA."))
                        continue

                    data_checkin = _clean_date(row.get('Data de Check-in'))
                    data_checkout = _clean_date(row.get('Data de Check-out'))
                    if not data_checkin or not data_checkout:
                        self.stdout.write(self.style.WARNING(
                            f"Linha {i} (ID: {id_imovel_str}): Formato de data inválido. LINHA IGNORADA."))
                        continue

                    # Monta o objeto Imovel em memória com os dados da linha
                    imovel_obj = Imovel(
                        id_imovel=int(id_imovel_str),
                        titulo=row.get('Título', ''),
                        tipo_acomodacao=row.get('Tipo de Acomodação', ''),
                        data_checkin=data_checkin,
                        data_checkout=data_checkout,
                        inclui_fim_de_semana=row.get('Inclui Fim de Semana', '').lower() == 'sim',
                        hospedes=_clean_integer(row.get('Número de Hóspedes')),
                        preco_total=_clean_decimal(row.get('Preço total')),
                        total_noites=_clean_integer(row.get('Total de Noites')),
                        avaliacao=_clean_decimal(row.get('Avaliação')),
                        qtd_avaliacoes=_clean_integer(row.get('Quantidade de Avaliações')),
                        link=row.get('Link', ''),
                        localizacao=row.get('Localização', ''),
                        quartos=_clean_integer(row.get('Quartos')),
                        camas=_clean_integer(row.get('Camas')),
                        banheiros=_clean_integer(row.get('Banheiros')),
                        horario_checkin=row.get('Horário de Check-in', ''),
                        horario_checkout=row.get('Horário de Check-out', ''),
                    )
                    imoveis_para_adicionar.append(imovel_obj)

                self.stdout.write(self.style.SUCCESS(
                    f'Arquivo processado. {len(imoveis_para_adicionar)} novos registros serão adicionados.'))

                # --- Operação de Banco de Dados em Bloco ---
                if imoveis_para_adicionar:
                    self.stdout.write(self.style.NOTICE('Iniciando inserção em massa no banco de dados...'))
                    # Insere todos os objetos da lista de uma só vez. É rápido e eficiente.
                    Imovel.objects.bulk_create(imoveis_para_adicionar, batch_size=1000)
                    self.stdout.write(self.style.SUCCESS('Novos registros adicionados com sucesso!'))
                else:
                    self.stdout.write(
                        self.style.WARNING('Nenhum registro válido encontrado no arquivo para adicionar.'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Erro: Arquivo não encontrado em "{file_path}".'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ocorreu um erro inesperado durante a importação: {e}"))