# -------------------
# 1. IMPORTAÇÕES
# -------------------
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
import pandas as pd
import numpy as np
import streamlit as st

# Importações para a geração de PDF
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# ----------------------------------------------------
# 2. FUNÇÃO PARA GERAR O PDF (VERSÃO ATUALIZADA)
# ----------------------------------------------------
def dataframe_to_pdf(df: pd.DataFrame) -> bytes:
    """
    Converte um DataFrame do Pandas em um arquivo PDF e retorna em bytes.
    O PDF será em modo paisagem para melhor visualização de tabelas largas.
    """
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    # Adiciona uma fonte que suporte caracteres latinos
    # Para suporte completo a UTF-8, seria necessário adicionar uma fonte .ttf específica
    pdf.set_font('Arial', '', 8)
    
    # Calcula a largura das colunas de forma dinâmica
    col_width = pdf.w / (len(df.columns) + 1)
    row_height = 8
    
    # Adiciona o cabeçalho da tabela
    pdf.set_fill_color(200, 220, 255) # Cor de fundo azul claro para o cabeçalho
    for col_name in df.columns:
        # Usa a sintaxe moderna para posicionamento (corrige o DeprecationWarning)
        pdf.cell(
            col_width, 
            row_height, 
            str(col_name), 
            border=1, 
            align='C', 
            fill=True, 
            new_x=XPos.RIGHT, 
            new_y=YPos.TOP
        )
    pdf.ln(row_height)
    
    # Adiciona as linhas de dados da tabela
    pdf.set_fill_color(255, 255, 255) # Fundo branco para as células de dados
    for index, row in df.iterrows():
        # Limita o número de caracteres por célula para evitar quebra de layout
        for item in row:
            text = str(item)[:35] # Pega os primeiros 35 caracteres do texto
            # Usa a sintaxe moderna para posicionamento
            pdf.cell(
                col_width, 
                row_height, 
                text, 
                border=1, 
                align='L', 
                fill=True, 
                new_x=XPos.RIGHT, 
                new_y=YPos.TOP
            )
        pdf.ln(row_height)
        
    # Retorna o PDF como bytes (corrige o AttributeError)
    # A função .output() sem argumentos já retorna os bytes necessários.
    return pdf.output()

# ----------------------------------
# 3. CONFIGURAÇÃO DA PÁGINA
# ----------------------------------
st.set_page_config(
    page_title="Análise do Banco de dados E-MEC - Terapia Ocupacional",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title('Análise do Banco de dados E-MEC - Terapia Ocupacional')

# -------------------------------------------------
# 4. FUNÇÃO DE FILTRO DO DATAFRAME (ORIGINAL)
# -------------------------------------------------
def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona uma UI na parte superior de um dataframe para permitir que os usuários filtrem colunas.
    """
    modify = st.checkbox("Adicionar os Filtros")

    if not modify:
        return df

    df = df.copy()

    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filtros aplicados", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Valores para {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Valores para {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Valores para {column}",
                    value=(df[column].min(), df[column].max()),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring ou Regex em {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]
    return df

# ----------------------------------
# 5. LÓGICA PRINCIPAL DO APP
# ----------------------------------
try:
    # Carrega o DataFrame a partir do arquivo CSV
    df_original = pd.read_csv('RelatorioMecTerapiaOcupacional.csv', sep=';')

    # Aplica os filtros e guarda o resultado em uma nova variável
    df_filtrado = filter_dataframe(df_original)

    # Exibe o DataFrame filtrado na tela
    st.dataframe(df_filtrado)

    # Gera o PDF a partir do DataFrame *filtrado*
    pdf_bytes = dataframe_to_pdf(df_filtrado)

    # Cria o botão de download com os dados do PDF gerado
    st.download_button(
        label="Baixar Relatório em PDF",
        data=pdf_bytes,
        file_name="relatorio_filtrado_to.pdf",
        mime='application/pdf' # O mime type correto para PDF
    )

except FileNotFoundError:
    st.error("Erro: Arquivo 'RelatorioMecTerapiaOcupacional.csv' não encontrado. Por favor, verifique se o arquivo está na mesma pasta do seu script.")
except Exception as e:
    st.error(f"Ocorreu um erro inesperado: {e}")