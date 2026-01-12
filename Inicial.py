import streamlit as st

# -------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -------------------------------
st.set_page_config(
    page_title="Sistema de Laudos Periciais",
    layout="wide"
)

# --------------------------------------------------
# PÁGINA INICIAL / APRESENTAÇÃO
# --------------------------------------------------

st.title("📘 Sistema de Gerenciamenteo de Laudos Periciais - NCCP")
st.markdown("### Bem-vindo ao assistente de elaboração de laudos")

st.markdown(
    """
Este sistema foi desenvolvido para **auxiliar o Perito Criminal** na organização
e geração de laudos a partir de informações preenchidas no **AutoLaudo**.

- **Objetivo:** agilizar a elaboração do laudo, mantendo **padrão**, **segurança**
  e **rastreamento das informações**.  
- **Importante:** esta aplicação é **uma ferramenta de apoio** à confecção do laudo.
  A análise técnica e a responsabilidade pelo conteúdo permanecem **exclusivamente
  com o perito responsável**.
"""
)

st.markdown("### Como o sistema está organizado")

st.markdown(
    """
1. **Resumo dos atendimentos (`Resumo`)**  
   Consulte os registros vindos da planilha, filtre por perito, datas e BO e visualize as principais informações do atendimento.
   Ao aplicar os filtros, você pode atualizar o arquivo de controle em Excel com os registros selecionados.

2. **Controle de Laudos (`Controle`)**  
   Gerencie o controle de laudos através de uma planilha editável. Visualize e edite campos como REP, Status e Observações,
   filtre por período e salve as alterações diretamente no arquivo Excel de controle.

3. **Estatísticas Interativas (`Estatísticas`)**  
   Explore os dados através de gráficos interativos com Plotly. Visualize indicadores gerais, distribuição por natureza,
   evolução temporal, preservação do local, análise por DP requisitante e autoridade, além de diversos outros gráficos
   interativos. Filtre por perito e período para análises personalizadas.

4. **Complemento de dados com PDF SAEP (`Importação SAEP`) - Em construção 🚧**  
   Caso haja necessidade, carregue o PDF do SAEP para complementar automaticamente campos da planilha, como
   histórico, quesitos e dados de endereço.

5. **Geração do Laudo em DOCX (`Gerar Laudo`) - Em construção 🚧**  
   Selecione o BO desejado, confira os dados e gere o laudo em formato **.docx**,
   que será salvo em sua máquina e também disponibilizado para download.
"""
)

st.markdown("### Dicas rápidas de navegação")

st.write("- Use o **menu lateral** (barra à esquerda) para alternar entre as páginas do sistema.")
st.write("- As páginas seguem a **ordem natural de trabalho**: consulta ➜ controle ➜ estatísticas ➜ complemento de dados ➜ geração do laudo.")
st.write("- Em caso de dúvida, leia sempre os **textos explicativos** no topo de cada página.")
st.write("- Na página de **Resumo**, após aplicar filtros, você pode atualizar o arquivo de controle diretamente.")
st.write("- Na página de **Estatísticas**, passe o mouse sobre os gráficos para ver detalhes e valores interativos.")


st.write("---")
st.caption(
    "Sistema idealizado pelo Perito Criminal Diogo Murrer para auxilio aos peritos do NCCP.")
