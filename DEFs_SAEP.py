import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
import re
import pdfplumber


# ---------------------------
# FUNÇÃO PARA EXTRAIR TEXTO DO PDF
# ---------------------------

def extrair_texto_plumber(uploaded_pdf):
    texto = ""
    with pdfplumber.open(uploaded_pdf) as pdf:
        for pagina in pdf.pages:
            texto += pagina.extract_text() + "\n"
    return texto


# ---------------------------
# FUNÇÃO PARA EXTRAIR E CATEGORIZAR CAMPOS DO TEXTO
# ---------------------------


def extrair_campos(uploaded_pdf):
    # 1 — extrai texto com pdfplumber
    texto = extrair_texto_plumber(uploaded_pdf)

    # 2 — limpeza leve
    texto = texto.replace('\r', '').strip()

    campos = {}

    # -----------------------------
    # Órgão Circunscrição
    # padrão robusto: captura até próximo "|"
    # -----------------------------
    m = re.search(
        r"Órgão Circunscrição:\s*(.*?)\s*\|",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )
    campos["orgao_circunscricao"] = m.group(
        1).replace("\n", " ").strip() if m else None

    # -----------------------------
    # Delegado
    # -----------------------------
    m = re.search(
        r"Nome\s+do\s+Requisitante:\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ ]+)",
        texto,
        flags=re.IGNORECASE
    )
    campos["nome_requisitante"] = m.group(1).strip() if m else None

    # -----------------------------
    # Endereço do Fato
    # captura tudo até quebra de linha
    # -----------------------------
    m = re.search(
        r"Endereço do Fato:\s*(.+)",
        texto
    )
    campos["endereco_fato"] = m.group(1).strip() if m else None

    # Capturar bloco entre "Quesitos:" e "Histórico"
    m = re.search(
        r"Quesitos:\s*(.*?)\s*SUPERINTENDÊNCIA",
        texto,
        flags=re.DOTALL | re.IGNORECASE
    )

    if not m:
        return None

    bloco = m.group(1).strip()

    # -----------------------------
    # QUESITOS
    # -----------------------------
    padrao = r"(\d+)\)\s*(.*?)(?=\s*\d+\)|$)"
    matches = re.findall(padrao, bloco, flags=re.DOTALL)

    quesitos_lista = [" ".join(texto.split()) for _, texto in matches]

    # 🔥 AQUI está o segredo: transformar a lista em string única
    quesitos_string = "\n".join(
        f"{i+1}) {q}" for i, q in enumerate(quesitos_lista)
    )
    campos["quesitos"] = quesitos_string

    # -----------------------------
    # HISTORICO
    # -----------------------------
    m = re.search(
        r"Histórico:\s*(.*?)\s*Histórico Inicial PM",
        texto,
        flags=re.DOTALL | re.IGNORECASE
    )

    if not m:
        return None

    historico = m.group(1).strip()

    # Limpeza opcional: remover múltiplas quebras de linha
    historico = re.sub(r"\n\s*\n+", "\n\n", historico).strip()
    campos["historico"] = historico

    return campos


# ---------------------------
# FUNÇÃO PARA ATUALIZAR A LINHA DO BO
# ---------------------------


def atualizar_celulas_especificas(sheet, linha_sheet, dict_coluna_valor):
    """
    sheet: objeto gspread Worksheet
    linha_sheet: número da linha no Google Sheets (1-based)
    dict_coluna_valor: {"Nome da Coluna": valor}
    """
    header = sheet.row_values(1)

    for coluna_nome, valor in dict_coluna_valor.items():
        if coluna_nome in header:
            col_index = header.index(coluna_nome) + 1  # 1-based
            sheet.update_cell(linha_sheet, col_index, valor)
