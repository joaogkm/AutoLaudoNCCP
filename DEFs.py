import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from docx import Document
import io


# ---------------------------------------------------
# CONFIGURAÇÕES INICIAIS
# ---------------------------------------------------
SHEET_ID = "1lazUBEsVNNLbwSoIB_VIIGuD6szIm7pr7jKWuEbyQH0"
RANGE = "Respostas ao formulário 1"  # aba da planilha

CAMINHO_EXCEL = "dados/controle_laudos.xlsx"

# Carregar credenciais da Service Account
credentials = service_account.Credentials.from_service_account_file(
    "service_account.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)

# ------------------------------------DEFs--------------------------------

# ---------------------------------------------------
# FUNÇÃO PARA BUSCAR DADOS DO GOOGLE SHEETS NO RESUMO
# ---------------------------------------------------


def carregar_dados_resumo():
    service = build("sheets", "v4", credentials=credentials)
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SHEET_ID, range=RANGE)
        .execute()
    )
    values = result.get("values", [])
    if not values:
        return pd.DataFrame(), None

    header = values[0]
    data = values[1:]

    num_cols = len(header)

    # 🔧 Normaliza todas as linhas
    data_normalizada = [
        linha + [""] * (num_cols - len(linha))
        for linha in data
    ]

    # 🔹 Normaliza nomes duplicados de colunas (SEM nova def)
    contador = {}
    header_normalizado = []

    for col in header:
        col = col.strip() if col else "Coluna"

        if col in contador:
            contador[col] += 1
            header_normalizado.append(f"{col}_{contador[col]}")
        else:
            contador[col] = 1
            header_normalizado.append(col)

    # cria DF com cabeçalho
    df = pd.DataFrame(data_normalizada, columns=header_normalizado)

    df["Data da requisição"] = pd.to_datetime(
        df["Data da requisição"],
        errors="coerce",
        dayfirst=True
    )
    df = df.sort_values(by="Data da requisição", ascending=True)

    # 🔹 Coluna PADRONIZADA PARA EXIBIÇÃO
    df["Data da requisição_fmt"] = df["Data da requisição"].dt.strftime(
        "%d/%m/%Y")

    # ---------------------------
    # 🔑 CHAVE ÚNICA (BO + ANO)
    # ---------------------------
    df["Ano requisicao"] = df["Data da requisição"].dt.year.astype("Int64")

    df["CHAVE_CONTROLE"] = (
        df["R.D.O."].astype(str).str.strip()
        + "_"
        + df["Ano requisicao"].astype(str)
    )

    return df

# ---------------------------------------------------
# FUNÇÃO PARA BUSCAR DADOS DO GOOGLE SHEETS NO GERAR LAUDO
# ---------------------------------------------------


def carregar_dados_geral():
    service = build("sheets", "v4", credentials=credentials)
    result = (service.spreadsheets()
              .values()
              .get(spreadsheetId=SHEET_ID, range=RANGE)
              .execute()
              )
    values = result.get("values", [])
    if not values:
        return pd.DataFrame(), None

    # cria DF com cabeçalho
    df = pd.DataFrame(values[1:], columns=values[0])

    df["Data da requisição"] = pd.to_datetime(
        df["Data da requisição"],
        errors="coerce",
        dayfirst=True
    )

    # usamos gspread para update em células específicas
    import gspread
    gc = gspread.service_account(filename="service_account.json")
    sheet = gc.open_by_key(SHEET_ID).worksheet(RANGE)

    return df, sheet

# ---------------------------
# FUNÇÃO PARA ATUALIZAR A LINHA DO BO ***** A VER SE IREMOS UTILIZAR****
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


# ---------------------------------------
# FUNCÇAO PARA GERAR LAUDO A PARTIR DO MODELO
# ---------------------------------------
def gerar_laudo_docx(dados_bo, caminho_modelo="modelo_laudo.docx"):
    doc = Document(caminho_modelo)

    for p in doc.paragraphs:
        for chave, valor in dados_bo.items():
            placeholder = "{" + chave + "}"
            if placeholder in p.text:
                p.text = p.text.replace(placeholder, str(valor))

    # Salvar para bytes (para download)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
