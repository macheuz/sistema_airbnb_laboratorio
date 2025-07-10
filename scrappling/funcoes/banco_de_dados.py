import psycopg2
import psycopg2.extras  # Para usar execute_batch
import pandas as pd
from io import StringIO
import logging

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- Funções de Conexão com Banco de Dados ---

def abre_conexao_banco_de_dados():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="planb",
            user="usuario",
            password="senha",
            port=5436
        )
        cursor = conn.cursor()
        logging.info("Conexão com o banco de dados estabelecida com sucesso.")
        return conn, cursor
    except psycopg2.Error as e:
        logging.error(f"Erro ao conectar ao banco de dados: {e}")
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None, None


def fecha_conexao_banco_de_dados(conn, cursor):
    try:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logging.info("Conexão com o banco de dados fechada com sucesso.")
    except psycopg2.Error as e:
        logging.error(f"Erro ao fechar a conexão com o banco de dados: {e}")
        print(f"Erro ao fechar a conexão com o banco de dados: {e}")



def retorna_tabela(nome_tabela, nome_schema="public"):
    conn, cursor = abre_conexao_banco_de_dados()

    if conn and cursor:
        try:
            sql = f'SELECT * FROM "{nome_schema}"."{nome_tabela}"'
            print(f"Executando query: {sql}")
            logging.info(f"Executando query: {sql}")

            cursor.execute(sql)
            dados = cursor.fetchall()
            colunas = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(dados, columns=colunas)
            logging.info(f"Tabela '{nome_tabela}' lida com sucesso, {len(df)} linhas retornadas.")
            return df
        except Exception as e:
            logging.error(f"Erro ao ler a tabela '{nome_tabela}': {e}")
            print(f"Erro ao ler a tabela: {e}")
            return None
        finally:
            fecha_conexao_banco_de_dados(conn, cursor)
    else:
        print("Não foi possível conectar ao banco de dados.")
        logging.error("Falha na leitura da tabela pois não foi possível conectar ao banco de dados.")
        return None



def insere_dados_no_banco(dados, tabela_destino, nome_schema="public"):
    if dados.empty:
        print("DataFrame de entrada está vazio. Nenhuma inserção será realizada.")
        logging.warning(f"Tentativa de inserção na tabela '{tabela_destino}' com DataFrame vazio.")
        return

    conn = None
    cursor = None
    tabela_com_schema_log = f'"{nome_schema}"."{tabela_destino}"'

    try:
        conn, cursor = abre_conexao_banco_de_dados()
        if conn is None or cursor is None:
            raise ConnectionError("Falha ao abrir a conexão com o banco de dados.")

        buffer = StringIO()
        dados.to_csv(buffer, index=False, header=False, sep=';', quotechar='"')
        buffer.seek(0)

        colunas_str = ', '.join(f'"{col}"' for col in dados.columns)
        sql_copy_command = (
            f'COPY "{nome_schema}"."{tabela_destino}" ({colunas_str}) '
            f"FROM STDIN WITH (FORMAT CSV, HEADER FALSE, DELIMITER ';', QUOTE '\"')"
        )

        logging.info(f"Executando comando COPY para a tabela {tabela_com_schema_log}")
        print(f"Executando comando COPY para a tabela {tabela_com_schema_log}")

        cursor.copy_expert(sql=sql_copy_command, file=buffer)
        conn.commit()

        mensagem_sucesso = f"{cursor.rowcount} linhas inseridas com sucesso na tabela {tabela_com_schema_log}."
        logging.info(mensagem_sucesso)
        print(mensagem_sucesso)

    except Exception as e:
        if conn:
            conn.rollback()
        mensagem_erro = f"Ocorreu um erro ao inserir dados na tabela {tabela_com_schema_log}: {e}"
        print(mensagem_erro)
        logging.error(mensagem_erro)
        raise
    finally:
        if conn:
            fecha_conexao_banco_de_dados(conn, cursor)



def excluir_linhas_por_dataframe(df_referencia, coluna_df, tabela_alvo, coluna_tabela, nome_schema="public"):
    """
    Exclui linhas de uma tabela do banco de dados com base nos valores de uma coluna de um DataFrame.
    """
    print(f"--- Iniciando processo de EXCLUSÃO na tabela '{nome_schema}'.'{tabela_alvo}' ---")

    if df_referencia.empty:
        print("O DataFrame de referência está vazio. Nenhuma exclusão será realizada.")
        return
    if coluna_df not in df_referencia.columns:
        raise ValueError(f"A coluna '{coluna_df}' não foi encontrada no DataFrame de referência.")

    valores_para_excluir = df_referencia[coluna_df].dropna().unique().tolist()
    if not valores_para_excluir:
        print(f"Nenhum valor válido encontrado na coluna '{coluna_df}' para exclusão.")
        return

    conn, cursor = None, None
    try:
        conn, cursor = abre_conexao_banco_de_dados()
        if conn is None or cursor is None:
            raise ConnectionError("Não foi possível estabelecer conexão com o banco de dados.")

        query = f'DELETE FROM "{nome_schema}"."{tabela_alvo}" WHERE "{coluna_tabela}" IN %s'
        valores_tuple = tuple(valores_para_excluir)

        print(f"Preparando para excluir {len(valores_tuple)} registros únicos da tabela '{tabela_alvo}'.")
        cursor.execute(query, (valores_tuple,))
        linhas_excluidas = cursor.rowcount
        conn.commit()

        print(f"Operação concluída. {linhas_excluidas} linha(s) foram excluídas com sucesso.")
        logging.info(f"{linhas_excluidas} linha(s) excluídas da tabela '{nome_schema}'.'{tabela_alvo}'.")

    except Exception as e:
        print(f"Ocorreu um erro durante a exclusão. A transação será revertida (rollback). Erro: {e}")
        logging.error(f"Erro na exclusão da tabela '{tabela_alvo}': {e}. Transação revertida.")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            fecha_conexao_banco_de_dados(conn, cursor)


def atualizar_dados_no_banco(df_atualizacao, tabela_alvo, colunas_para_atualizar, coluna_chave, nome_schema="public"):

    print(f"--- Iniciando processo de ATUALIZAÇÃO na tabela '{nome_schema}'.'{tabela_alvo}' ---")

    if df_atualizacao.empty:
        print("O DataFrame de atualização está vazio. Nenhuma operação será realizada.")
        return

    colunas_necessarias = colunas_para_atualizar + [coluna_chave]
    for col in colunas_necessarias:
        if col not in df_atualizacao.columns:
            raise ValueError(f"A coluna '{col}' necessária para a atualização não foi encontrada no DataFrame.")

    conn, cursor = None, None
    try:
        conn, cursor = abre_conexao_banco_de_dados()
        if conn is None or cursor is None:
            raise ConnectionError("Não foi possível estabelecer conexão com o banco de dados.")

        set_clause = ", ".join([f'"{col}" = %s' for col in colunas_para_atualizar])
        query = f'UPDATE "{nome_schema}"."{tabela_alvo}" SET {set_clause} WHERE "{coluna_chave}" = %s'

        colunas_ordenadas = colunas_para_atualizar + [coluna_chave]
        dados_para_atualizar = [tuple(row) for row in df_atualizacao[colunas_ordenadas].itertuples(index=False)]

        print(f"Preparando para atualizar {len(dados_para_atualizar)} registros.")

        # Usa execute_batch, que é ideal para executar um comando (UPDATE) várias vezes.
        psycopg2.extras.execute_batch(cursor, query, dados_para_atualizar)

        linhas_atualizadas = cursor.rowcount
        conn.commit()

        print(f"Operação concluída. {linhas_atualizadas} linha(s) foram atualizadas na tabela '{tabela_alvo}'.")
        logging.info(f"{linhas_atualizadas} linha(s) atualizadas na tabela '{nome_schema}'.'{tabela_alvo}'.")

    except Exception as e:
        print(f"Ocorreu um erro durante a atualização. A transação será revertida (rollback). Erro: {e}")
        logging.error(f"Erro na atualização da tabela '{tabela_alvo}': {e}. Transação revertida.")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            fecha_conexao_banco_de_dados(conn, cursor)