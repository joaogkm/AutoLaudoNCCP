import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from DEFs import *
import os


# -------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -------------------------------
st.set_page_config(
    page_title="Sistema de Laudos Periciais",
    layout="wide"
)

# -------------------------------
# TELA PRINCIPAL
# -------------------------------
st.title("📋 Resumo dos Atendimentos")

st.markdown(
    """
Esta página apresenta um **resumo dos registros**, permitindo que o perito visualize rapidamente os atendimentos.

- **Objetivo desta tela:**
  - Consultar os casos já cadastrados.  
  - Visualizar a lista completa de atendimentos ou filtrar por **período de requisição**;  
  - Opcionalmente filtrar por um **BO específico** na barra lateral.
"""
)

df = carregar_dados_resumo()

# nome das colunas conforme carregadas
bo_col = df.columns[5]
colunas_exibir = [
    "Perito",
    "R.D.O.",
    "Protocolo",
    "Data da requisição_fmt",
    "Data de chegada",
    "Natureza do fato",
    "Endereço do local",
    "D.P. do fato"
]

# só exibe df completo quando NENHUM filtro foi aplicado
st.session_state.setdefault("filtrou", False)
if not st.session_state["filtrou"]:
    st.dataframe(df[colunas_exibir], use_container_width=True)
    st.success(f"Total de registros: {len(df)}")

    st.caption(
        "Tabela resumida com os principais campos para facilitar a localização do caso. "
        "Use os filtros na barra lateral para refinar a busca."
    )


# ---------------------------
# SIDEBAR — FILTROS (datas + BO)
# ---------------------------

st.sidebar.header("📅 Filtros de consulta")

# ---------------------------
# FILTRO PERITO (PRIMEIRO)
# ---------------------------
lista_peritos = sorted(df["Perito"].dropna().unique().tolist())

peritos_escolhidos = st.sidebar.multiselect(
    "Perito responsável",
    options=lista_peritos,
    default=[]
)

# DataFrame base conforme Perito
df_base = df.copy()

# if perito_escolhido != "Todos":
#     df_base = df_base[df_base["Perito"] == perito_escolhido]

if peritos_escolhidos:
    df_base = df_base[df_base["Perito"].isin(peritos_escolhidos)]

# 🚨 Aviso se não houver registros
if df_base.empty:
    st.warning("⚠️ Não há registros para o(s) perito(s) selecionado(s).")
    st.stop()

# Datas
data_min = df_base["Data da requisição"].min().date()
data_max = df_base["Data da requisição"].max().date()

data_inicial = st.sidebar.date_input(
    "Data inicial", value=data_min, min_value=data_min, max_value=data_max
)
data_final = st.sidebar.date_input(
    "Data final", value=data_max, min_value=data_min, max_value=data_max
)

# BO (opcional)
lista_bos = sorted(df_base[bo_col].astype(str).unique().tolist())

bos_escolhidos = st.sidebar.multiselect(
    "Número do BO (opcional)",
    options=lista_bos,
    default=[]
)
# botão vem por último
aplicar_filtro = st.sidebar.button("🔎 Filtrar")

# --------------------------------
# INICIALIZA CONTROLE (IMPORTANTE)
# --------------------------------
if "df_controle_novo" not in st.session_state:
    st.session_state["df_controle_novo"] = pd.DataFrame()

# ---------------------------
# APLICAÇÃO DO FILTRO
# ---------------------------

if aplicar_filtro:
    st.session_state["filtrou"] = True  # marca que houve filtro

    df_filtrado = df_base[
        (df_base["Data da requisição"] >= pd.to_datetime(data_inicial)) &
        (df_base["Data da requisição"] <= pd.to_datetime(data_final))
    ]

    if bos_escolhidos:
        df_filtrado = df_filtrado[
            df_filtrado[bo_col].astype(str).isin(bos_escolhidos)
        ]

    # Exibe resultado final
    st.subheader("📊 Resultados filtrados")
    st.dataframe(df_filtrado[colunas_exibir], use_container_width=True)

    st.session_state["df_controle_novo"] = pd.DataFrame({
        "Carimbo de data/hora": df_filtrado["Carimbo de data/hora"],
        "Perito": df_filtrado["Perito"],
        "Data da requisição": df_filtrado["Data da requisição"],
        "Protocolo": df_filtrado["Protocolo"],
        "BO": df_filtrado["CHAVE_CONTROLE"],
        "REP": "",
        "D.P. requisitante": df_filtrado["D.P. requisitante"],
        "Autoridade requisitante": df_filtrado["Autoridade requisitante"],
        "D.P. do fato": df_filtrado["D.P. do fato"],
        "Natureza do fato": df_filtrado["Natureza do fato"],
        "Endereço do local": df_filtrado["Endereço do local"],
        "Data de chegada": df_filtrado["Data de chegada"],
        "Status": "",
        "Observação": "",
    })
st.divider()
st.subheader("🗂️ Controle")

df_controle_novo = st.session_state["df_controle_novo"]

st.info(f"Registros selecionados para controle: {len(df_controle_novo)}")

if st.button("📥 Atualizar controle (Excel)"):

    if df_controle_novo.empty:
        st.error("Nenhum registro encontrado com os filtros aplicados.")
        st.stop()

    import os
    os.makedirs("dados", exist_ok=True)

    if os.path.exists(CAMINHO_EXCEL):
        df_existente = pd.read_excel(CAMINHO_EXCEL)

        df_merge = pd.merge(
            df_existente,
            df_controle_novo,
            on="BO",
            how="outer",
            suffixes=("_old", "")
        )

        df_final = pd.DataFrame()
        df_final["BO"] = df_merge["BO"]

        for col in df_controle_novo.columns:
            if col == "BO":
                continue

            col_old = f"{col}_old"

            if col_old in df_merge.columns:
                df_final[col] = df_merge[col_old].combine_first(df_merge[col])
            else:
                df_final[col] = df_merge[col]

    else:
        df_final = df_controle_novo.copy()

    df_final.to_excel(CAMINHO_EXCEL, index=False)

    st.success(
        f"Controle atualizado com {len(df_controle_novo)} registros.")
