import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
import re
import pdfplumber
from DEFs import *
from DEFs_SAEP import *

# -------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -------------------------------
st.set_page_config(
    page_title="Sistema de Laudos Periciais",
    layout="wide"
)

# -------------------------------
# ESTADO INICIAL
# -------------------------------
st.session_state.setdefault("filtrou", False)
st.session_state.setdefault("bo_escolhido", None)

# ---------------------------
# INTERFACE
# ---------------------------
st.title("📄 Importação SAEP – Complementar dados do BO")

st.markdown(
    """
Nesta página você pode **complementar automaticamente** os dados de um BO
utilizando o **PDF da requisição SAEP**.

- Primeiro, utilize os **filtros na barra lateral** para localizar o BO desejado.  
- Em seguida, selecione o **BO** na área principal da página.  
- Por fim, faça o **upload do PDF** e confirme a gravação dos campos extraídos na planilha.

"""
)

df, sheet = carregar_dados_geral()
if df.empty:
    st.error("Erro ao carregar dados do Google Sheets.")
    st.stop()

bo_col = df.columns[1]
colunas_exibir = [
    "BO",
    "Data da Requisição",
    "Data do Exame",
    "Natureza",
    "Endereço",
    "Protocolo SAEP"
]

# ---------------------------
# MOSTRA TABELA AO ABRIR A TELA
# ---------------------------
st.subheader("📋 Dados atuais do Google Sheets")
if not st.session_state["filtrou"]:
    st.dataframe(df[colunas_exibir], use_container_width=True)
    st.success(f"Total de registros: {len(df)}")
st.caption(
    "Visualização geral dos registros atualmente presentes na planilha. "
    "Use os filtros ao lado para focar apenas no período e BO de interesse."
)

# ---------------------------
# SIDEBAR — FILTROS
# ---------------------------
st.sidebar.header("📅 Filtros para seleção do BO")

# Datas
data_min = df["Data da Requisição"].min().date()
data_max = df["Data da Requisição"].max().date()

data_inicial = st.sidebar.date_input(
    "Data inicial", value=data_min, min_value=data_min, max_value=data_max
)
data_final = st.sidebar.date_input(
    "Data final", value=data_max, min_value=data_min, max_value=data_max
)

# 🔧 ALTERADO — BO agora vem ANTES do botão Filtrar
lista_bos = df[bo_col].astype(str).unique().tolist()
lista_bos.insert(0, "Todos")  # permite não escolher BO

bo_filtro = st.sidebar.selectbox(
    "Número do BO (opcional)",
    options=lista_bos
)

aplicar_filtro = st.sidebar.button("🔎 Filtrar")

# ---------------------------
# FILTRO
# ---------------------------
df_filtrado = df.copy()

if aplicar_filtro:
    st.session_state["filtrou"] = True  # marca que houve filtro

    df_filtrado = df[
        (df["Data da Requisição"] >= pd.to_datetime(data_inicial)) &
        (df["Data da Requisição"] <= pd.to_datetime(data_final))
    ]

    if bo_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado[bo_col].astype(str) == bo_filtro]

    st.subheader("Dados filtrados")
    st.dataframe(df_filtrado, use_container_width=True)


# ---------------------------
# SELECIONAR BO APÓS FILTRAR
# ---------------------------
st.markdown("---")
st.header("📁 Selecionar BO para importar PDF SAEP")

st.markdown(
    """
Escolha abaixo o **BO** que será complementado com as informações extraídas do PDF.
Após a seleção, a opção de **upload do PDF** será exibida.
"""
)


if df_filtrado.empty:
    st.warning("Nenhum registro disponível.")
    st.stop()

lista_bos_filtrados = df_filtrado[bo_col].astype(str).unique().tolist()

bo_escolhido = st.selectbox(
    "Selecione o BO",
    options=lista_bos_filtrados,
    key="bo_escolhido"
)

# ---------------------------
# UPLOAD DO PDF — SOMENTE APÓS SELECIONAR BO
# ---------------------------
if st.session_state["bo_escolhido"]:
    st.success(f"BO selecionado: {bo_escolhido}")

    uploaded_pdf = st.file_uploader(
        "Envie o PDF do BO (arquivo gerado pelo SAEP)", type=["pdf"]
    )

    if uploaded_pdf:
        st.success("PDF enviado com sucesso!")

        # Extrai campos específicos
        dados_extraidos = extrair_campos(uploaded_pdf)

        st.subheader("📌 Campos extraídos automaticamente do PDF")
        st.write(dados_extraidos)

        st.caption(
            "Revise os campos acima. Eles serão gravados nas colunas correspondentes "
            "da planilha (Órgão Circunscrição, Delegado, Endereço do Fato, Quesitos e Histórico)."
        )

        # Localiza a linha do BO
        bo_escolhido = st.session_state["bo_escolhido"]
        linha_df = df.index[df[bo_col].astype(str) == bo_escolhido].tolist()
        linha_sheet = linha_df[0] + 2  # linha real na planilha

        # Copia todos os valores da linha atual
        valores = df.iloc[linha_df[0]].tolist()

        # Exemplo: supondo que sua planilha tenha colunas específicas para estes campos
        valores.append(dados_extraidos["orgao_circunscricao"])
        valores.append(dados_extraidos["delegado"])
        valores.append(dados_extraidos["endereco_fato"])
        valores.append(dados_extraidos["quesitos"])
        valores.append(dados_extraidos["historico"])

        if st.button("💾 Salvar dados do PDF no Google Sheets"):

            dict_update = {
                "Órgão Circunscrição": dados_extraidos["orgao_circunscricao"],
                "Delegado": dados_extraidos["delegado"],
                "Endereço do Fato": dados_extraidos["endereco_fato"],
                "Quesitos": dados_extraidos["quesitos"],
                "Historico": dados_extraidos["historico"]
            }
            atualizar_celulas_especificas(sheet, linha_sheet, dict_update)
            st.success(
                "Dados gravados com sucesso na planilha! "
                "Essas informações já podem ser utilizadas na etapa de geração do laudo."
            )
