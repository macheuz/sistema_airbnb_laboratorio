import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
import time
import sys
import os
import re


def extrair_detalhes_anuncio(driver, url):
    """
    Navega para a URL de um anúncio e extrai detalhes como número de quartos,
    camas, banheiros e horários de check-in/check-out.
    (Esta função permanece inalterada, pois sua lógica interna de extração está correta)
    """
    # Define a URL base para garantir que estamos na página principal do anúncio
    base_url = url.split('?')[0].split('/house-rules')[0]

    quartos = None
    camas = None
    banheiros = None
    horario_checkin = None
    horario_checkout = None

    # --------------------------------------------------------------------
    # Extrair Quartos, Camas e Banheiros da Página Principal
    # --------------------------------------------------------------------

    print("  - Extraindo Quartos, Camas e Banheiros...")
    try:
        driver.set_page_load_timeout(20)
        driver.get(base_url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        overview_section = soup.find('div', {'data-plugin-in-point-id': 'OVERVIEW_DEFAULT_V2'})
        if overview_section:
            lista_itens = overview_section.find_all('li', class_='l7n4lsf')
            for item in lista_itens:
                texto_item = item.get_text(strip=True).replace('·', '').strip()
                if 'quarto' in texto_item:
                    quartos = texto_item
                elif 'cama' in texto_item:
                    camas = texto_item
                elif 'banheiro' in texto_item:
                    banheiros = texto_item
        else:
            print("    Seção de visão geral não encontrada. Tentando método alternativo.")
            try:
                overview_element = driver.find_element(By.XPATH, "//*[contains(text(), 'hóspedes')]")
                parent_div = overview_element.find_element(By.XPATH, "./..")
                items = parent_div.find_elements(By.TAG_NAME, 'span')
                full_text = ' '.join([item.text for item in items if item.text.strip()])

                q = re.search(r'(\d+\s*quarto|Estúdio)', full_text)
                c = re.search(r'(\d+\s*cama)', full_text)
                b = re.search(r'(\d+\s*banheiro)', full_text)
                if q: quartos = q.group(1)
                if c: camas = c.group(1)
                if b: banheiros = b.group(1)
            except Exception:
                pass

    except TimeoutException:
        print("  - A página principal demorou muito para carregar. Pulando extração de quartos/camas/banheiros.")
    except Exception as e:
        print(f"  ERRO ao extrair quartos/camas/banheiros: {e}")
        quartos, camas, banheiros = 'Erro', 'Erro', 'Erro'

    print(f"    Quartos: {quartos}, Camas: {camas}, Banheiros: {banheiros}")

    # --------------------------------------------------------------------
    # Extrair Check-in/Check-out
    # --------------------------------------------------------------------
    print("  - Extraindo Check-in/Check-out...")
    try:
        soup_regras = BeautifulSoup(driver.page_source, 'html.parser')
        policies_section = soup_regras.find('div', {'data-section-id': 'POLICIES_DEFAULT'})
        if policies_section:
            rule_items = policies_section.find_all('div', class_='i1303y2k')
            for item in rule_items:
                texto_item = item.get_text(strip=True)
                if 'Check-in' in texto_item:
                    horario_checkin = texto_item
                elif 'Checkout' in texto_item:
                    horario_checkout = texto_item

        if not horario_checkin or not horario_checkout:
            print("    Check-in/Check-out não encontradas na seção principal, tentando clicar em 'Mostrar mais'...")
            try:
                show_more_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH,
                                                "//a[contains(., 'Mostrar regras da casa')] | //button[contains(., 'Mostrar mais')]"))
                )
                driver.execute_script("arguments[0].click();", show_more_button)
                time.sleep(2)

                soup_modal = BeautifulSoup(driver.page_source, 'html.parser')
                modal_rule_items = soup_modal.find_all('div', class_='f15dgkuj')
                for item in modal_rule_items:
                    texto_item = item.get_text(strip=True)
                    if 'Check-in:' in texto_item:
                        horario_checkin = texto_item
                    elif 'Checkout:' in texto_item:
                        horario_checkout = texto_item
            except (TimeoutException, NoSuchElementException):
                print("    Botão 'Mostrar mais' para Check-in/Check-out não encontrado.")
            except Exception as e:
                print(f"    Erro ao tentar abrir o modal de Check-in/Check-out: {e}")

    except Exception as e:
        print(f"  ERRO FATAL ao extrair os horários de check-in/out: {e}")
        horario_checkin, horario_checkout = 'Erro na extração', 'Erro na extração'
    finally:
        driver.set_page_load_timeout(60)

    print(f"    Check-in: {horario_checkin}")
    print(f"    Check-out: {horario_checkout}")

    return {
        "Quartos": quartos,
        "Camas": camas,
        "Banheiros": banheiros,
        "Horário de Check-in": horario_checkin,
        "Horário de Check-out": horario_checkout,
    }


# --------------------------------------------------------------------
# Bloco MAIN
# --------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python script.py <nome_do_arquivo.csv>")
        sys.exit(1)

    input_filename = sys.argv[1]
    base_name, extension = os.path.splitext(input_filename)
    # --- NOVO: Definindo nomes para arquivos de saída ---
    partial_results_filename = f"{base_name}_resultados_parciais.csv"
    final_output_filename = f"{base_name}_completo.csv"

    try:
        df_airbnb = pd.read_csv(input_filename)
        print(f"Arquivo '{input_filename}' carregado com sucesso.")
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{input_filename}' não encontrado.")
        sys.exit(1)

    if 'ID Imóvel' not in df_airbnb.columns or 'Link' not in df_airbnb.columns:
        print("ERRO: O arquivo CSV deve conter as colunas 'ID Imóvel' e 'Link'.")
        sys.exit(1)

    df_para_scrape = df_airbnb[['ID Imóvel', 'Link']].drop_duplicates(subset=['ID Imóvel']).dropna(subset=['Link'])
    total_links_unicos = len(df_para_scrape)
    print(f"\nEncontrados {total_links_unicos} imóveis únicos para processar.")

    # --- NOVO: Lógica para resumir o trabalho ---
    processed_ids = set()
    if os.path.exists(partial_results_filename):
        print(f"Encontrado arquivo de resultados parciais: '{partial_results_filename}'.")
        df_parcial = pd.read_csv(partial_results_filename)
        processed_ids = set(df_parcial['ID Imóvel'])
        print(f"Resumindo trabalho. {len(processed_ids)} imóveis já foram processados e serão pulados.")

    options = Options()
    options.add_argument('--headless')
    options.set_preference("permissions.default.image", 2)
    options.set_preference("permissions.default.stylesheet", 2)
    options.set_preference("gfx.downloadable_fonts.enabled", False)

    print("\nIniciando o navegador Firefox...")
    driver = webdriver.Firefox(options=options)

    # --- NOVO: Contador para reinício do navegador ---
    processed_in_this_session = 0
    total_a_processar = total_links_unicos - len(processed_ids)
    print(f"\nIniciando a extração para {total_a_processar} novos anúncios únicos...")

    for index, row in df_para_scrape.iterrows():
        id_imovel = row['ID Imóvel']
        url = row['Link']

        # --- ALTERADO: Pula se o ID já foi processado ---
        if id_imovel in processed_ids:
            continue

        # --- ALTERADO: Lógica de reinício do navegador ---
        if processed_in_this_session > 0 and processed_in_this_session % 50 == 0:
            print(f"\n--- Processados {processed_in_this_session} links nesta sessão. Reiniciando o navegador... ---")
            driver.quit()
            time.sleep(5)
            driver = webdriver.Firefox(options=options)
            print("--- Navegador reiniciado. Continuando a extração... ---\n")

        print(f"Processando anúncio {processed_in_this_session + 1}/{total_a_processar} (ID: {id_imovel}): {url}")

        if pd.notna(url) and isinstance(url, str) and url.startswith("http"):
            detalhes = extrair_detalhes_anuncio(driver, url)
        else:
            print(f"Link inválido ou ausente para o ID Imóvel {id_imovel}. Pulando.")
            detalhes = {
                "Quartos": 'Link Inválido', "Camas": 'Link Inválido',
                "Banheiros": 'Link Inválido', "Horário de Check-in": 'Link Inválido',
                "Horário de Check-out": 'Link Inválido'
            }

        # --- NOVO: Anexa o resultado ao arquivo CSV parcial ---
        detalhes['ID Imóvel'] = id_imovel
        df_resultado_atual = pd.DataFrame([detalhes])

        # Escreve o cabeçalho apenas se o arquivo não existir
        escrever_header = not os.path.exists(partial_results_filename)

        df_resultado_atual.to_csv(
            partial_results_filename,
            mode='a',  # 'a' para anexar (append)
            header=escrever_header,
            index=False
        )
        print(f"  > Resultado para ID {id_imovel} salvo em '{partial_results_filename}'")

        processed_in_this_session += 1

    print("\nExtração de todos os novos links concluída.")
    driver.quit()

    # --- NOVO: Lógica final para mesclar e salvar ---
    print("\nMapeando dados extraídos de volta para o DataFrame completo...")

    if os.path.exists(partial_results_filename):
        df_detalhes = pd.read_csv(partial_results_filename)

        colunas_novas = ['Quartos', 'Camas', 'Banheiros', 'Horário de Check-in', 'Horário de Check-out']
        # Remove colunas antigas para evitar duplicatas ao reexecutar
        df_airbnb_sem_detalhes = df_airbnb.drop(columns=colunas_novas, errors='ignore')

        # Mescla o dataframe original com os dados coletados (sejam eles desta ou de execuções anteriores)
        df_final = pd.merge(df_airbnb_sem_detalhes, df_detalhes, on='ID Imóvel', how='left')

        try:
            df_final.to_csv(final_output_filename, index=False)
            print(f"\nDataFrame final salvo com sucesso em '{final_output_filename}'")
        except Exception as e:
            print(f"\nOcorreu um erro ao salvar o arquivo CSV final: {e}")
    else:
        print("\nNenhum dado foi extraído. O arquivo final não foi gerado.")