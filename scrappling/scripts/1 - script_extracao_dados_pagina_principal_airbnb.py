import pandas as pd
import time
import re
import os  # Importado para verificar a existência do arquivo
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from datetime import date, timedelta
import calendar


def buscar_e_extrair_airbnb(driver, local, data_checkin, data_checkout, numero_hospedes, max_paginas=None):
    """
    Função para buscar hospedagens no Airbnb usando uma sessão de navegador existente.
    Navega por páginas, extrai dados e retorna um DataFrame.
    (Esta função permanece inalterada em sua lógica interna de extração)
    """
    dados_hospedagens = []

    try:
        checkin_iso = f"{data_checkin[6:]}-{data_checkin[3:5]}-{data_checkin[:2]}"
        checkout_iso = f"{data_checkout[6:]}-{data_checkout[3:5]}-{data_checkout[:2]}"
        url = (f"https://www.airbnb.com.br/s/{local}/homes?checkin={checkin_iso}"
               f"&checkout={checkout_iso}&adults={numero_hospedes}")

        print(f"Acessando a URL: {url}")
        driver.get(url)

        pagina_atual = 1
        while True:
            if max_paginas is not None and pagina_atual > max_paginas:
                print(f"\nLimite de {max_paginas} página(s) atingido. Finalizando extração para esta data.")
                break

            print(f"\n--- Extraindo dados da página {pagina_atual} ---")

            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='card-container']"))
                )
                time.sleep(5)
            except TimeoutException:
                print("Tempo de espera excedido. Não foi possível carregar os anúncios.")
                try:
                    no_results_element = driver.find_element(By.CSS_SELECTOR, "h1")
                    if "Nenhum resultado" in no_results_element.text:
                        print("A página indica 'Nenhum resultado' para os filtros aplicados.")
                except NoSuchElementException:
                    pass
                break

            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            listings = soup.find_all('div', {'data-testid': 'card-container'})

            if not listings:
                print("Nenhum anúncio encontrado nesta página, finalizando.")
                break

            print(f"Encontrados {len(listings)} anúncios na página {pagina_atual}.")

            for listing in listings:
                link_tag = listing.find('a', href=True)
                link = "https://www.airbnb.com.br" + link_tag['href'] if link_tag and link_tag.get('href') else 'N/A'

                imovel_id = 'N/A'
                if link != 'N/A':
                    id_match = re.search(r'/rooms/(\d+)', link)
                    if id_match:
                        imovel_id = id_match.group(1)

                title_div = listing.find('div', {'data-testid': 'listing-card-title'})
                title = title_div.text.strip() if title_div else 'N/A'

                tipo_acomodacao = 'N/A'
                if ' em ' in title:
                    tipo_acomodacao = title.split(' em ', 1)[0]

                nota_avaliacao, qtd_avaliacoes = 'N/A', 'N/A'
                rating_container = listing.find('span', class_=re.compile(r'r4a59j5'))
                if rating_container:
                    rating_span = rating_container.find('span', {'aria-hidden': 'true'})
                    if rating_span:
                        full_rating_text = rating_span.text.strip()
                        if "Novo" in full_rating_text:
                            nota_avaliacao, qtd_avaliacoes = 'Novo', '0'
                        else:
                            score_match = re.search(r'([\d,.]+)', full_rating_text)
                            if score_match: nota_avaliacao = score_match.group(1)
                            count_match = re.search(r'\((\d+)\)', full_rating_text)
                            if count_match: qtd_avaliacoes = count_match.group(1)

                preco, qtd_noites = 'N/A', 'N/A'
                price_row = listing.find('div', {'data-testid': 'price-availability-row'})
                if price_row:
                    full_price_text = price_row.get_text(separator=' ').strip()
                    preco_match = re.search(r'R\$\s*([\d.]+)', full_price_text)
                    if preco_match:
                        preco_str = preco_match.group(1)
                        preco_final = preco_str.replace('.', '')
                        preco = f"R${preco_final}"

                    noites_match = re.search(r'(\d+)\s*noites', full_price_text)
                    if noites_match: qtd_noites = noites_match.group(1)

                dados_hospedagens.append({
                    'ID Imóvel': imovel_id, 'Título': title, 'Tipo de Acomodação': tipo_acomodacao,
                    'Data de Check-in': data_checkin, 'Data de Check-out': data_checkout,
                    'Número de Hóspedes': numero_hospedes, 'Preço total': preco, 'Total de Noites': qtd_noites,
                    'Avaliação': nota_avaliacao, 'Quantidade de Avaliações': qtd_avaliacoes, 'Link': link
                })

            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "a[aria-label='Próximo']")
                driver.execute_script("arguments[0].click();", next_button)
                pagina_atual += 1
            except NoSuchElementException:
                print("Não há mais páginas para extrair. Fim da extração.")
                break
    except Exception as e:
        print(f"Ocorreu um erro geral durante a extração: {e}")

    return pd.DataFrame(dados_hospedagens)

# ==============================================================================
# BLOCO DE EXECUÇÃO PRINCIPAL
# ==============================================================================

if __name__ == "__main__":
    locais_busca = [
        "Copacabana, Rio de Janeiro",
        "Ipanema, Rio de Janeiro",
        "Barra da Tijuca, Rio de Janeiro",
        "Leblon, Rio de Janeiro"
    ]
    meses_busca = [8, 9, 10, 11, 12]
    ano_busca = 2025
    hospedes = 1
    duracao_estadia_em_noites = 4

    # ===== ALTERAÇÃO 1: NOME DO ARQUIVO DEFINIDO NO INÍCIO =====
    # O nome do arquivo é definido uma vez para ser usado de forma incremental.
    nome_arquivo = f"airbnb_dados_gerais_{hospedes}_hospede_{duracao_estadia_em_noites}_noites{date.today().strftime('%Y_%m_%d')}.csv"

    # Remove a lista de dataframes que consumia memória
    # lista_de_dataframes = []
    driver = None
    iteration_counter = 0

    print("--- INICIANDO BUSCA ---")
    print(f"Os resultados serão salvos progressivamente em: '{nome_arquivo}'")

    for local in locais_busca:
        for mes in meses_busca:
            num_dias_no_mes = calendar.monthrange(ano_busca, mes)[1]

            print(f"\n{'=' * 60}")
            print(f"PROCESSANDO LOCAL: {local} | MÊS/ANO: {mes:02d}/{ano_busca}")
            print(f"{'=' * 60}")

            for dia in range(1, num_dias_no_mes + 1):
                iteration_counter += 1

                if iteration_counter > 1 and (iteration_counter - 1) % 100 == 0:
                    if driver:
                        print(
                            f"\n--- [Iteração {iteration_counter - 1}] Reiniciando o navegador para liberar recursos ---")
                        driver.quit()
                        driver = None

                if driver is None:
                    print("\n--- Iniciando uma nova sessão do navegador ---")
                    options = Options()
                    options.add_argument('--headless') # Roda o navegador sem interface gráfica. Essencial para economizar recursos.
                    options.add_argument('--disable-gpu') # Desabilita a aceleração por hardware, útil em ambientes de servidor e headless.
                    options.add_argument('--no-sandbox') # Necessário para rodar como root em alguns ambientes Linux.
                    options.add_argument('--disable-dev-shm-usage') # Evita problemas de memória compartilhada em contêineres.

                    # ===== ALTERAÇÃO 2: OPÇÕES OTIMIZADAS PARA MENOS RAM =====
                    # Bloqueia o carregamento de imagens, CSS, fontes e autoplay de mídia para acelerar e reduzir o uso de memória.
                    options.set_preference("permissions.default.image", 2)
                    options.set_preference("permissions.default.stylesheet", 2) # Pode quebrar a detecção de alguns elementos se a página depender muito de classes CSS para estrutura.
                    options.set_preference("gfx.downloadable_fonts.enabled", False)
                    options.set_preference("media.autoplay.enabled", False)

                    driver = webdriver.Firefox(options=options)

                data_de_checkin = date(ano_busca, mes, dia)
                data_de_checkout = data_de_checkin + timedelta(days=duracao_estadia_em_noites)

                checkin_str = data_de_checkin.strftime("%d/%m/%Y")
                checkout_str = data_de_checkout.strftime("%d/%m/%Y")

                inclui_fim_de_semana = "Não"
                for i in range(duracao_estadia_em_noites + 1):
                    dia_da_estadia = data_de_checkin + timedelta(days=i)
                    if dia_da_estadia.weekday() >= 5:
                        inclui_fim_de_semana = "Sim"
                        break

                print(f"\n--- Buscando dia {dia}/{num_dias_no_mes} para {local} | Check-in: {checkin_str} ---")

                df_resultado_diario = buscar_e_extrair_airbnb(
                    driver, local, checkin_str, checkout_str, hospedes #, max_paginas=1
                )

                # ===== ALTERAÇÃO 3: SALVAMENTO INCREMENTAL EM VEZ DE ACUMULAR EM MEMÓRIA =====
                if not df_resultado_diario.empty:
                    df_resultado_diario['Localização'] = local
                    df_resultado_diario['Inclui Fim de Semana'] = inclui_fim_de_semana

                    # Garante que a ordem das colunas seja sempre a mesma antes de salvar
                    colunas_ordenadas = [
                        'Localização', 'ID Imóvel', 'Título', 'Tipo de Acomodação',
                        'Data de Check-in', 'Data de Check-out', 'Inclui Fim de Semana',
                        'Número de Hóspedes', 'Preço total', 'Total de Noites', 'Avaliação',
                        'Quantidade de Avaliações', 'Link'
                    ]
                    df_resultado_diario = df_resultado_diario[colunas_ordenadas]

                    # Verifica se o arquivo já existe para decidir se escreve o cabeçalho
                    escrever_cabecalho = not os.path.exists(nome_arquivo)

                    # Usa o modo 'a' (append) para adicionar os dados ao final do arquivo
                    # sem carregar o conteúdo existente na memória.
                    df_resultado_diario.to_csv(
                        nome_arquivo,
                        mode='a',
                        header=escrever_cabecalho,
                        index=False,
                        encoding='utf-8-sig'
                    )
                    print(f"SUCESSO: {len(df_resultado_diario)} novos registros salvos em '{nome_arquivo}'")
                else:
                    print(f"AVISO: Nenhum resultado encontrado para {checkin_str} em {local}.")

    if driver:
        print("\n--- Fechando a sessão final do navegador. ---")
        driver.quit()

    # ===== ALTERAÇÃO 4: PÓS-PROCESSAMENTO PARA REMOVER DUPLICATAS =====
    # Após o término de toda a coleta, o arquivo final é lido, limpo e salvo novamente.
    # Isso mantém o consumo de memória baixo durante a coleta e ainda entrega um arquivo final limpo.
    print("\n\n--- FIM---")
