from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
import pandas as pd
import numpy as np
import streamlit as st
from fpdf import FPDF # Importa a biblioteca para gerar PDF

# --- Função para criar o PDF a partir de um DataFrame ---
def dataframe_to_pdf(df: pd.DataFrame) -> bytes:
    """
    Converte um DataFrame do Pandas em um arquivo PDF e retorna em bytes.
    O PDF será em modo paisagem para melhor visualização de tabelas largas.
    """
    pdf = FPDF(orientation='L', unit='mm', format='A4') # 'L' para paisagem (Landscape)
    pdf.add_page()
    
    # Adiciona uma fonte que suporte caracteres latinos (opcional, mas recomendado)
    # Para suporte completo a UTF-8, seria necessário adicionar uma fonte .ttf
    pdf.set_font('Arial', '', 8)
    
    col_width = pdf.w / (len(df.columns) + 1) # Calcula a largura das colunas
    row_height = 8 # Altura da linha
    
    # Adiciona o cabeçalho da tabela
    pdf.set_fill_color(200, 220, 255) # Cor de fundo para o cabeçalho
    for col_name in df.columns:
        pdf.cell(col_width, row_height, str(col_name), border=1, ln=0, align='C', fill=True)
    pdf.ln(row_height)
    
    # Adiciona as linhas de dados
    pdf.set_fill_color(255, 255, 255)
    for index, row in df.iterrows():
        # Limita o número de caracteres por célula para evitar quebra de layout
        for item in row:
            text = str(item)[:35] # Pega os primeiros 35 caracteres para não estourar a célula
            pdf.cell(col_width, row_height, text, border=1, ln=0, align='L', fill=True)
        pdf.ln(row_height)
        
    # Retorna o PDF como bytes
    return pdf.output(dest='S').encode('latin-1')


# --- Configuração da Página do Streamlit ---
st.set_page_config(
    page_title="Análise do Banco de dados E-MEC - Terapia Ocupacional",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title('Análise do Banco de dados E-MEC - Terapia Ocupacional')

# --- Função de Filtro (seu código original, sem alterações) ---
def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Adicionar os Filtros")

    if not modify:
        return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
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
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
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

# --- Lógica Principal do App ---
# Carrega os dados (certifique-se que o arquivo CSV está na mesma pasta)
try:
    df_original = pd.read_csv('RelatorioMecTerapiaOcupacional.csv', sep=';')

    # Aplica os filtros e guarda o resultado em uma nova variável
    df_filtrado = filter_dataframe(df_original)

    # Exibe o DataFrame filtrado na tela
    st.dataframe(df_filtrado)

    # Gera o PDF a partir do DataFrame *filtrado*
    pdf_bytes = dataframe_to_pdf(df_filtrado)

    # Cria o botão de download
    st.download_button(
        label="Baixar Relatório em PDF",
        data=pdf_bytes,
        file_name="relatorio_filtrado_to.pdf",
        mime='application/pdf' # O mime type correto para PDF
    )

except FileNotFoundError:
    st.error("Erro: Arquivo 'RelatorioMecTerapiaOcupacional.csv' não encontrado. Por favor, verifique se o arquivo está na pasta correta.")