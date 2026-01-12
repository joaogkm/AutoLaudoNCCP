import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from DEFs import *
import plotly.express as px

st.set_page_config(
    page_title="Estatísticas",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Estatísticas Interativas (Plotly)")
st.markdown(
    """
Aqui você encontra **gráficos interativos** para explorar os dados dos laudos
de forma mais dinâmica.

- Filtre por **período** e por **natureza**;  
- Analise a distribuição por natureza, a evolução diária e a preservação do local;  
- Passe o mouse sobre os gráficos para ver detalhes, valores e datas.
"""
)

# ==================================================
# CARREGAMENTO DOS DADOS
# ==================================================

df = carregar_dados_resumo()

# ==================================================
# SIDEBAR — FILTROS
# ==================================================

st.sidebar.header("🔍 Filtros de análise")

# ---------------------------
# FILTRO PERITOS
# ---------------------------
lista_peritos = sorted(df["Perito"].dropna().unique().tolist())

peritos_escolhidos = st.sidebar.multiselect(
    "Perito(s)",
    options=lista_peritos,
    default={}
)

df_base = df.copy()

if peritos_escolhidos:
    df_base = df_base[df_base["Perito"].isin(peritos_escolhidos)]

if df_base.empty:
    st.warning("⚠️ Não há dados para os filtros selecionados.")
    st.stop()

# ---------------------------
# FILTRO DATA
# ---------------------------
data_min = df_base["Data da requisição"].min().date()
data_max = df_base["Data da requisição"].max().date()

data_inicio, data_fim = st.sidebar.date_input(
    "Período",
    value=(data_min, data_max),
    min_value=data_min,
    max_value=data_max
)

df_filtrado = df_base[
    (df_base["Data da requisição"] >= pd.to_datetime(data_inicio)) &
    (df_base["Data da requisição"] <= pd.to_datetime(data_fim))
]

if df_filtrado.empty:
    st.warning("⚠️ Não há registros no período selecionado.")
    st.stop()

# ==================================================
# KPIs (INDICADORES)
# ==================================================
st.subheader("📌 Indicadores gerais")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total de Laudos", len(df_filtrado))

with col2:
    preservados = df_filtrado["Local preservado"].value_counts().get("Sim", 0)
    st.metric("Locais Preservados", preservados)

with col3:
    st.metric(
        "Naturezas Distintas",
        df_filtrado["Natureza do fato"].nunique()
    )

st.divider()

# ==================================================
# PRIMEIRA LINHA DE GRÁFICOS
# ==================================================

col1, col2, col3 = st.columns(3)

# ==================================================
# GRÁFICO 1 - LAUDOS POR NATUREZA
# ==================================================

col1, col2, col3 = st.columns(3)

with col1:
    with col1:
        st.subheader("📊 Laudos por natureza")

        contagem_natureza = (
            df_filtrado["Natureza do fato"]
            .value_counts()
            .reset_index()
        )

        contagem_natureza.columns = ["Natureza", "Quantidade"]

        fig = px.bar(
            contagem_natureza,
            x="Natureza",
            y="Quantidade",
            text="Quantidade"
        )

        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis_title="Natureza",
            yaxis_title="Quantidade"
        )

        st.plotly_chart(fig, use_container_width=True)

# ==================================================
# GRÁFICO 2 - LAUDOS POR DIA
# ==================================================
with col2:
    st.subheader("📅 Laudos ao longo do tempo")

    laudos_por_dia = (
        df_filtrado
        .groupby(df_filtrado["Data da requisição"].dt.date)
        .size()
        .reset_index(name="Quantidade")
    )

    laudos_por_dia.columns = ["Data", "Quantidade"]

    fig = px.line(
        laudos_por_dia,
        x="Data",
        y="Quantidade",
        markers=True
    )

    fig.update_layout(
        xaxis_title="Data",
        yaxis_title="Quantidade"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==================================================
# GRÁFICO 3 - PRESERVAÇÃO DO LOCAL
# ==================================================
with col3:
    st.subheader("🚓 Preservação do local")

    preservacao = (
        df_filtrado["Local preservado"]
        .value_counts()
        .reset_index()
    )

    preservacao.columns = ["Preservação", "Quantidade"]

    fig = px.pie(
        preservacao,
        names="Preservação",
        values="Quantidade",
        hole=0.4
    )

    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ==================================================
# SEGUNDA LINHA DE GRÁFICOS
# ==================================================

col1, col2, col3 = st.columns(3)

# ==================================================
# GRÁFICO 4 - DP Requisitante
# ==================================================
with col1:
    st.subheader("🚓 DP Requisitante")

    requisitante = (
        df_filtrado["D.P. requisitante"]
        .value_counts()
        .reset_index()
    )

    requisitante.columns = ["D.P. requisitante", "Quantidade"]

    fig = px.pie(
        requisitante,
        names="D.P. requisitante",
        values="Quantidade",
        hole=0.4
    )

    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ==================================================
# GRÁFICO 5 - LAUDOS POR DP do FATO
# ==================================================

with col2:
    with col2:
        st.subheader("📊 Laudos por DP do Fato")

        contagem_DP = (
            df_filtrado["D.P. do fato"]
            .value_counts()
            .reset_index()
        )

        contagem_DP.columns = ["DP do Fato", "Quantidade"]

        fig = px.bar(
            contagem_DP,
            x="Quantidade",
            y="DP do Fato",
            orientation="h",
            text="Quantidade"
        )

        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            xaxis_title="Quantidade de Laudos",
            yaxis_title="Autoridade"
        )

        st.plotly_chart(fig, use_container_width=True)

# ==================================================
# GRÁFICO 6 - AUTORIDADE REQUISITANTE - TREEMAP
# ==================================================
with col3:
    st.subheader("🧑‍💼 Autoridade Requisitante")

    if "Autoridade requisitante" in df_filtrado.columns:
        autoridade = (
            df_filtrado["Autoridade requisitante"]
            .value_counts()
            .reset_index()
        )
        autoridade.columns = ["Autoridade", "Quantidade"]
        fig = px.treemap(
            autoridade,
            path=["Autoridade"],
            values="Quantidade",
        )

    st.plotly_chart(fig, use_container_width=True)

# ==================================================
# TERCEIRA  LINHA DE GRÁFICOS
# ==================================================

col1, col2, col3 = st.columns(3)

# ==================================================
# GRÁFICO 7 - AUTORIDADE REQUISITANTE - SUNBURST
# ==================================================

with col1:
    st.subheader("☀️ Autoridade x Natureza do Fato")

    if "Autoridade requisitante" in df_filtrado.columns:
        autoridade = (
            df_filtrado["Autoridade requisitante"]
            .value_counts()
            .reset_index()
        )
        autoridade.columns = ["Autoridade", "Quantidade"]
        fig = px.sunburst(
            df_filtrado,
            path=["Autoridade requisitante", "Natureza do fato"],
        )

        st.plotly_chart(fig, use_container_width=True)


# ==================================================
# GRÁFICO 8 - AUTORIDADE REQUISITANTE - BOLHAS
# ==================================================

with col2:
    st.subheader("🫧 Volume x Diversidade de Laudos por Autoridade")

    if "Autoridade requisitante" in df_filtrado.columns:
        autoridade = (
            df_filtrado["Autoridade requisitante"]
            .value_counts()
            .reset_index()
        )

        bolhas = (
            df_filtrado
            .groupby("Autoridade requisitante")
            .agg(
                quantidade=("Autoridade requisitante", "count"),
                naturezas=("Natureza do fato", "nunique")
            )
            .reset_index()
        )

        fig = px.scatter(
            bolhas,
            x="Autoridade requisitante",
            y="quantidade",
            size="naturezas",
            labels={
                "quantidade": "Quantidade de Laudos",
                "naturezas": "Naturezas Distintas"
            }
        )

        fig.update_layout(xaxis_tickangle=-45)

        st.plotly_chart(fig, use_container_width=True)


# ==================================================
# GRÁFICO 9 - AUTORIDADE REQUISITANTE - HEATMAP
# ==================================================

with col3:
    st.subheader("🔥 Demanda por Autoridade ao Longo do Tempo")

    if "Autoridade requisitante" in df_filtrado.columns:
        autoridade = (
            df_filtrado["Autoridade requisitante"]
            .value_counts()
            .reset_index()
        )

        df_heat = df_filtrado.copy()
        df_heat["Mes"] = df_heat["Data da requisição"].dt.strftime("%m/%Y")

        heatmap = (
            df_heat
            .groupby(["Autoridade requisitante", "Mes"])
            .size()
            .reset_index(name="Quantidade")
        )

        fig = px.density_heatmap(
            heatmap,
            x="Mes",
            y="Autoridade requisitante",
            z="Quantidade",
        )

        st.plotly_chart(fig, use_container_width=True)


# ==================================================
# TABELA FINAL
# ==================================================
st.subheader("📄 Dados filtrados")
st.dataframe(df_filtrado, use_container_width=True)
