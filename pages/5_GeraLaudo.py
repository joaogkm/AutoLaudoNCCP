import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from docx import Document
import io
import os
from DEFs import *

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
st.title("📄 Gerar Laudo em DOCX")

st.markdown(
    """
Nesta página você irá **selecionar um BO** já cadastrado, conferir os dados
e, em seguida, **gerar o laudo em formato .docx**.

**Fluxo recomendado:**
1. Use os **filtros na barra lateral**;  
2. Verifique os registros na tabela exibida;  
3. Selecione o **BO** na seção *“Selecionar BO para gerar o laudo”*;  
4. Confirme os dados apresentados e clique em **“Gerar Laudo DOCX”**.
5. O arquivo gerado será salvo em uma pasta local e também poderá ser baixado pela própria interface.
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

if not st.session_state["filtrou"]:
    st.dataframe(df[colunas_exibir], use_container_width=True)
    st.success(f"Total de registros: {len(df)}")

    st.caption(
        "Visualização resumida dos atendimentos disponíveis para geração de laudo. "
        "Use os filtros na barra lateral para restringir o período ou focar em um BO específico."
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
st.header("📁 Selecionar BO para gerar o laudo")

st.markdown(
    """
Escolha abaixo o **BO** para o qual o laudo será gerado. Certifique-se de que os dados exibidos estão corretos
antes de confirmar a geração do documento.
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
# CARREGAR REGISTRO
# ---------------------------

# Inicializa session_state se não existir
if bo_escolhido:
    registro = df_filtrado[df_filtrado[bo_col].astype(
        str) == bo_escolhido].iloc[0]

    st.success("BO carregado! Confira os dados abaixo antes de gerar o laudo.")
    st.dataframe(registro.to_frame())

    st.write("### Dados selecionados para o laudo")
    data_req = registro.get("Data da Requisição")
    dados_do_laudo = {
        "requisicao_dia": data_req.day if pd.notna(data_req) else "",
        "requisicao_mes": data_req.month if pd.notna(data_req) else "",
        "requisicao_ano": data_req.year if pd.notna(data_req) else "",
        "Nome_Requisitante": registro.get("Nome do Requisitante", ""),
        "Orgao_Circunscricao": registro.get("Órgão Circunscrição", ""),
        "BO": registro.get("BO", ""),
        "protocolo_re": registro.get("Protocolo SAEP", ""),
        "Natureza": registro.get("Natureza", ""),
        "Endereco_Fato": registro.get("Endereço do Fato", ""),
        "local_hora_chegada": registro.get("Data do Exame", ""),
        "preservacao_instituicao": registro.get("Preservação/Instituição", ""),
        "preservacao_agente": registro.get("Nome Preservação", ""),
        "preservacao_id": registro.get("ID Preservação", ""),
        "preservacao_vtr": registro.get("Viatura", ""),
        "requisicao_objetivo_pericia": registro.get("Objetivo Pericia", ""),
        "Quesitos": registro.get("Quesitos", ""),
        "Historico": registro.get("Histórico", "")
    }

    if st.button("📝 Gerar Laudo DOCX"):
        buffer = gerar_laudo_docx(dados_do_laudo)

        # Criar pasta do laudos
        pasta_base = "laudos_gerados"
        pasta_bo = os.path.join(pasta_base, f"BO_{bo_escolhido}")

        os.makedirs(pasta_bo, exist_ok=True)

        # Caminho do arquivo a ser salvo
        caminho_arquivo = os.path.join(pasta_bo, f"laudo_{bo_escolhido}.docx")

        # Salvar o arquivo localmente
        with open(caminho_arquivo, "wb") as f:
            f.write(buffer.getvalue())

        st.success(f"Laudo gerado e salvo em: {caminho_arquivo}")

        st.caption(
            "O laudo foi salvo na pasta indicada acima. "
            "Você também pode baixá-lo diretamente pelo botão abaixo."
        )

        # Botão para download
        st.download_button(
            label="⬇️ Baixar Laudo",
            data=buffer,
            file_name=f"laudo_{bo_escolhido}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
