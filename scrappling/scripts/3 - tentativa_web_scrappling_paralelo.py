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
import multiprocessing
import numpy as np
import glob


def extrair_detalhes_anuncio(driver, url):
    """
    Navega para a URL de um anúncio e extrai detalhes como número de quartos,
    camas e banheiros.
    """
    base_url = url.split('?')[0].split('/house-rules')[0]

    quartos = None
    camas = None
    banheiros = None

    # --------------------------------------------------------------------
    # Extrair Quartos, Camas e Banheiros da Página Principal
    # --------------------------------------------------------------------
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
        print("  - A página principal demorou muito para carregar. Pulando extração.")
    except Exception as e:
        print(f"  ERRO ao extrair quartos/camas/banheiros: {e}")
        quartos, camas, banheiros = 'Erro', 'Erro', 'Erro'
    finally:
        driver.set_page_load_timeout(60)

    return {
        "Quartos": quartos,
        "Camas": camas,
        "Banheiros": banheiros,
    }


def worker_process(worker_id, df_chunk, base_name):
    """
    Função executada por cada processo paralelo.
    """
    worker_log_prefix = f"[Worker {worker_id}]"
    print(f"{worker_log_prefix} Iniciando. Tarefas a executar: {len(df_chunk)}")

    worker_results_filename = f"{base_name}_worker_{worker_id}_temp_results.csv"

    options = Options()
    options.add_argument('--headless')
    options.set_preference("permissions.default.image", 2)
    options.set_preference("permissions.default.stylesheet", 2)
    options.set_preference("gfx.downloadable_fonts.enabled", False)

    driver = webdriver.Firefox(options=options)

    try:
        processed_in_this_session = 0
        for index, row in df_chunk.iterrows():
            # --- REMOVIDO: Bloco de reinicialização do navegador ---

            id_imovel = row['ID Imóvel']
            url = row['Link']

            print(f"{worker_log_prefix} Processando ID {id_imovel}: {url}")

            if pd.notna(url) and isinstance(url, str) and url.startswith("http"):
                detalhes = extrair_detalhes_anuncio(driver, url)
            else:
                print(f"{worker_log_prefix} Link inválido para ID {id_imovel}.")
                detalhes = {
                    "Quartos": 'Link Inválido', "Camas": 'Link Inválido',
                    "Banheiros": 'Link Inválido'
                }

            detalhes['ID Imóvel'] = id_imovel
            df_resultado_atual = pd.DataFrame([detalhes])

            escrever_header = not os.path.exists(worker_results_filename)
            df_resultado_atual.to_csv(worker_results_filename, mode='a', header=escrever_header, index=False)
            processed_in_this_session += 1

    except Exception as e:
        print(f"{worker_log_prefix} OCORREU UM ERRO INESPERADO: {e}")
    finally:
        print(f"{worker_log_prefix} Finalizado. Total processado: {processed_in_this_session}.")
        driver.quit()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python script.py <nome_do_arquivo.csv> <numero_de_threads>")
        sys.exit(1)

    input_filename = sys.argv[1]
    try:
        num_workers = int(sys.argv[2])
        if num_workers <= 0: raise ValueError()
    except ValueError:
        print("ERRO: O <numero_de_threads> deve ser um número inteiro positivo.")
        sys.exit(1)

    base_name, extension = os.path.splitext(input_filename)
    partial_results_filename = f"{base_name}_resultados_parciais.csv"
    final_output_filename = f"{base_name}_completo.csv"

    try:
        df_airbnb = pd.read_csv(input_filename)
        print(f"Arquivo '{input_filename}' carregado com {len(df_airbnb)} linhas.")
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{input_filename}' não encontrado.")
        sys.exit(1)

    if 'ID Imóvel' not in df_airbnb.columns or 'Link' not in df_airbnb.columns:
        print("ERRO: O arquivo CSV deve conter as colunas 'ID Imóvel' e 'Link'.")
        sys.exit(1)

    processed_ids = set()
    if os.path.exists(partial_results_filename):
        print(f"Encontrado arquivo de resultados parciais: '{partial_results_filename}'.")
        df_parcial = pd.read_csv(partial_results_filename)
        processed_ids = set(df_parcial['ID Imóvel'])
        print(f"Resumindo trabalho. {len(processed_ids)} imóveis já processados serão pulados.")

    df_para_scrape = df_airbnb[['ID Imóvel', 'Link']].drop_duplicates(subset=['ID Imóvel']).dropna(subset=['Link'])
    df_a_processar = df_para_scrape[~df_para_scrape['ID Imóvel'].isin(processed_ids)]

    total_a_processar = len(df_a_processar)
    if total_a_processar == 0:
        print("\nNenhum imóvel novo para processar. Saindo.")
        sys.exit(0)

    print(f"\nEncontrados {total_a_processar} imóveis únicos para processar com {num_workers} workers.")

    df_chunks = np.array_split(df_a_processar, num_workers)
    df_chunks = [chunk for chunk in df_chunks if not chunk.empty]

    processes = []
    for i, chunk in enumerate(df_chunks):
        p = multiprocessing.Process(target=worker_process, args=(i, chunk, base_name))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    print("\n--- Todos os workers terminaram. Consolidando resultados. ---")

    temp_files = glob.glob(f"{base_name}_worker_*_temp_results.csv")
    if temp_files:
        df_all_results = pd.concat([pd.read_csv(f) for f in temp_files], ignore_index=True)
        escrever_header = not os.path.exists(partial_results_filename)
        df_all_results.to_csv(partial_results_filename, mode='a', header=escrever_header, index=False)
        print(f"Resultados consolidados e anexados a '{partial_results_filename}'.")

        for f in temp_files:
            os.remove(f)
        print("Arquivos temporários foram removidos.")

    print("\nMapeando dados extraídos de volta para o DataFrame completo...")
    if os.path.exists(partial_results_filename):
        df_detalhes = pd.read_csv(partial_results_filename)

        colunas_novas = ['Quartos', 'Camas', 'Banheiros']

        df_airbnb_sem_detalhes = df_airbnb.drop(columns=colunas_novas, errors='ignore')
        df_final = pd.merge(df_airbnb_sem_detalhes, df_detalhes, on='ID Imóvel', how='left')

        try:
            df_final.to_csv(final_output_filename, index=False)
            print(f"\nDataFrame final salvo com sucesso em '{final_output_filename}'")
        except Exception as e:
            print(f"\nOcorreu um erro ao salvar o arquivo CSV final: {e}")
    else:
        print("\nNenhum dado foi extraído. O arquivo final não foi gerado.")