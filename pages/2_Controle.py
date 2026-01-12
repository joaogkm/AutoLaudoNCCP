import streamlit as st
import pandas as pd
import os
from DEFs import *

st.title("🗂️ Controle de Laudos")

st.markdown(
    """
    Esta página permite **gerenciar e atualizar** o controle de laudos através de uma planilha editável.
    
    - **Objetivo:** acompanhar o status dos laudos, registrar REPs e adicionar observações relevantes.
    - **Campos editáveis:** REP, Status e Observação.
    - **Campos fixos:** informações como BO, Perito, Protocolo, etc. não podem ser alterados aqui.
    """
)

st.divider()

if not os.path.exists(CAMINHO_EXCEL):
    st.warning("⚠️ Nenhum arquivo de controle encontrado.")
    st.info(
        "💡 **Dica:** Para criar um arquivo de controle, vá até a página **Resumo**, aplique os filtros desejados "
        "e clique em **'Atualizar controle (Excel)'** para gerar o arquivo inicial."
    )
    st.stop()

df = pd.read_excel(CAMINHO_EXCEL)

# Garante datetime
df["Data da requisição"] = pd.to_datetime(
    df["Data da requisição"], errors="coerce"
)

for col in ["REP", "Status", "Observação"]:
    if col in df.columns:
        df[col] = (df[col].astype(str).replace("nan", "").fillna(""))

# ==========================================
# SIDEBAR - FILTRO POR PERÍODO
# ==========================================

st.sidebar.header("📅 Filtro por período")

data_min = df["Data da requisição"].min().date()
data_max = df["Data da requisição"].max().date()

data_inicio, data_fim = st.sidebar.date_input(
    "Data da requisição",
    value=[data_min, data_max],
    min_value=data_min,
    max_value=data_max
)

aplicar_filtro = st.sidebar.button("🔎 Aplicar filtros")

if aplicar_filtro:
    df_filtrado = df[
        (df["Data da requisição"] >= pd.to_datetime(data_inicio)) &
        (df["Data da requisição"] <= pd.to_datetime(data_fim))
    ]
else:
    df_filtrado = df.copy()

# ==========================================
# INDICADORES RÁPIDOS
# ==========================================
st.subheader("📊 Visão geral")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total de registros", len(df_filtrado))

with col2:
    finalizados = len(df_filtrado[df_filtrado["Status"] ==
                      "Finalizado"]) if "Status" in df_filtrado.columns else 0
    st.metric("Finalizados", finalizados)

with col3:
    em_andamento = len(df_filtrado[df_filtrado["Status"] ==
                       "Em andamento"]) if "Status" in df_filtrado.columns else 0
    st.metric("Em andamento", em_andamento)

with col4:
    aguardando = len(df_filtrado[df_filtrado["Status"] ==
                     "Aguardando fotos"]) if "Status" in df_filtrado.columns else 0
    st.metric("Aguardando fotos", aguardando)

st.divider()

# ==========================================
# TABELA EDITÁVEL
# ==========================================
colunas_fixas = [
    "BO",
    "Perito",
    "Data da requisição",
    "Protocolo",
    "D.P. requisitante",
    "Autoridade requisitante",
    "D.P. do fato",
    "Natureza do fato",
    "Endereço do local",
    "Data de chegada"
]

colunas_editaveis = ["REP", "Status", "Observação"]

df_exibicao = df_filtrado[colunas_fixas + colunas_editaveis]

st.subheader("✏️ Atualização de controle")

st.info(
    """
    **📝 Como editar:**
    - Clique diretamente nas células das colunas **REP**, **Status** ou **Observação** para editá-las.
    - A coluna **Status** possui opções pré-definidas: Em andamento, Aguardando fotos, Finalizado.
    - As demais colunas são apenas para visualização e não podem ser alteradas.
    - Após fazer as alterações, clique no botão **"💾 Salvar alterações"** abaixo da tabela.
    """
)

df_editado = st.data_editor(
    df_exibicao,
    use_container_width=True,
    num_rows="fixed",
    column_config={
        "REP": st.column_config.TextColumn("REP"),
        "Status": st.column_config.SelectboxColumn(
            "Status",
            options=["", "Em andamento", "Aguardando fotos", "Finalizado"]
        ),
        "Observação": st.column_config.TextColumn("Observação")
    },
    disabled=colunas_fixas
)

st.caption(
    f"💡 **Dica:** Você está visualizando {len(df_filtrado)} registro(s). "
    "Use os filtros na barra lateral para refinar a visualização."
)

st.divider()

if st.button("💾 Salvar alterações", type="primary", use_container_width=True):
    df_atualizado = df.copy()

    # Atualiza apenas linhas editadas
    for _, linha in df_editado.iterrows():
        mask = df_atualizado["BO"] == linha["BO"]

        for col in colunas_editaveis:
            df_atualizado.loc[mask, col] = linha[col]

    try:
        df_atualizado.to_excel(CAMINHO_EXCEL, index=False)
        st.success("✅ Controle atualizado com sucesso!")
        st.balloons()

    except PermissionError:
        st.error(
            "❌ **Não foi possível atualizar o arquivo.**\n\n"
            "O arquivo Excel está aberto em outro programa.\n\n"
            "**Solução:** Feche o arquivo 'controle_laudos.xlsx' e tente novamente."
        )
