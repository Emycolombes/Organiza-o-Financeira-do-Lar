from datetime import datetime
import base64
import os
import gspread
from gspread.utils import rowcol_to_a1
from google.oauth2.service_account import Credentials
import streamlit as st

# Tenta carregar a logo do projeto (arquivo "logo.png" na raiz do repositório).
# Se ainda não existir, usa um emoji como alternativa, sem quebrar a app.
CAMINHO_LOGO = os.path.join(os.path.dirname(__file__), "logo.png")
LOGO_BASE64 = None
if os.path.exists(CAMINHO_LOGO):
  with open(CAMINHO_LOGO, "rb") as f:
    LOGO_BASE64 = base64.b64encode(f.read()).decode()

# Configuração da página com tema acolhedor
st.set_page_config(
    page_title="Organização Financeira do Lar",
    page_icon=CAMINHO_LOGO if LOGO_BASE64 else "🏡",
    layout="wide",
)

# Paleta de cores do projeto "Finanças do Lar na Prática" (ACEC/IntegraCon)
AZUL_MARINHO = "#101453"
VERDE = "#63C446"
VERDE_ESCURO = "#28800D"
DOURADO = "#FFDE59"
AZUL_CLARO_FUNDO = "#EDFAFF"

st.markdown(
    f"""
    <style>
    /* Botões no estilo do projeto: azul-marinho com hover verde */
    div.stButton > button {{
        background-color: {AZUL_MARINHO};
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        padding: 0.5em 1.5em;
    }}
    div.stButton > button:hover {{
        background-color: {VERDE_ESCURO};
        color: white;
    }}
    /* Subtítulos de secção com sublinhado verde, como na cartilha */
    h3 {{
        color: {AZUL_MARINHO} !important;
        border-bottom: 3px solid {VERDE};
        padding-bottom: 0.2em;
    }}
    /* Caixas de sucesso em verde */
    div[data-testid="stAlertContainer"][data-baseweb="notification"] {{
        border-radius: 10px;
    }}
    /* Fundo geral suave nos separadores/expander */
    section[data-testid="stSidebar"] {{
        background-color: {AZUL_CLARO_FUNDO};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Cabeçalho estilizado, inspirado no banner do infográfico do projeto,
# com a logo oficial ao lado do texto
logo_html = (
    f'<img src="data:image/png;base64,{LOGO_BASE64}" '
    'style="height: 100px; margin-right: 1.2em; border-radius: 10px;" />'
    if LOGO_BASE64
    else ""
)
st.markdown(
    f"""
    <div style="
        background-color: {AZUL_MARINHO};
        padding: 2em 1.5em;
        border-radius: 12px;
        margin-bottom: 1.5em;
        display: flex;
        align-items: center;
    ">
        {logo_html}
        <div>
            <p style="
                color: white;
                font-size: 1.1em;
                font-weight: 600;
                letter-spacing: 0.1em;
                margin-bottom: 0;
            ">ORGANIZAÇÃO</p>
            <p style="
                color: {VERDE};
                font-size: 2.6em;
                font-weight: 900;
                line-height: 1.05;
                margin: 0;
                text-transform: uppercase;
            ">Financeira <span style="color: white;">do Lar</span></p>
            <p style="
                color: {AZUL_CLARO_FUNDO};
                font-size: 1em;
                margin-top: 0.8em;
                margin-bottom: 0;
            ">🏡 Bem-vinda ao seu assistente financeiro inteligente, integrado com o Google Sheets!</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)



MESES_PT = [
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
]

ITENS_DESPESA = [
    "Taxas da casa", "Água", "Luz", "Gás", "Reparos na casa", "Farmácia",
    "Combustível", "Educação", "Ração PET", "Assinaturas", "Açougue",
    "Delivery", "Roupas e calçados", "Internet", "Supermercado",
    "Plano de Saúde",
]

FORMAS_PAGAMENTO = [
    "Dinheiro / PIX", "Cartão de Débito", "Cartão de Crédito",
    "Boleto Bancário", "Transferência",
]

DESCRICOES_RECEITA = ["Salário Mensal", "Renda extra"]


# Função para extrair o ID da planilha a partir de um link colado ou de um ID puro
def extrair_sheet_id(texto):
  texto = texto.strip()
  if "/d/" in texto:
    return texto.split("/d/")[1].split("/")[0]
  return texto


# Função para ligar ao Google Sheets usando os Secrets do Streamlit
# O cache é feito por sheet_id, para que cada pessoa fique ligada à sua
# própria planilha sem interferir com as ligações de outras pessoas.
@st.cache_resource
def conectar_gsheets(sheet_id):
  scope = [
      "https://www.googleapis.com/auth/spreadsheets",
      "https://www.googleapis.com/auth/drive",
  ]
  credentials_dict = dict(st.secrets["gcp_service_account"])
  creds = Credentials.from_service_account_info(
      credentials_dict, scopes=scope
  )
  client = gspread.authorize(creds)
  sheet = client.open_by_key(sheet_id)
  return sheet


EMAIL_CONTA_SERVICO = dict(st.secrets["gcp_service_account"]).get(
    "client_email", "(email da conta de serviço)"
)

st.markdown("---")
st.subheader("🔗 Conecte sua planilha")
st.write(
    "Cole aqui o link (ou apenas o ID) da sua planilha do Google Sheets,"
    " criada a partir do modelo. Antes de colar, garanta que já"
    " compartilhou a planilha com este e-mail, com permissão de"
    f" **Editor**: `{EMAIL_CONTA_SERVICO}`"
)

# Tenta pré-preencher com o ID guardado no link (parâmetro ?sheet=... na URL)
id_guardado = st.query_params.get("sheet", "")
link_planilha = st.text_input("Link ou ID da sua planilha", value=id_guardado)

sh = None
if link_planilha:
  sheet_id = extrair_sheet_id(link_planilha)
  try:
    sh = conectar_gsheets(sheet_id)
    st.success("Conexão ao Google Sheets estabelecida com sucesso!")
    if st.query_params.get("sheet") != sheet_id:
      st.query_params["sheet"] = sheet_id
    st.info(
        "🔖 Guarde este link (o endereço que aparece agora na barra do"
        " navegador) nos seus favoritos — da próxima vez que você abrir, a"
        " sua planilha já vai estar conectada automaticamente, sem precisar"
        " colar o link de novo."
    )
  except Exception as e:
    st.error(
        "Erro ao conectar ao Google Sheets. Confirme que o link está certo"
        f" e que você compartilhou a planilha com {EMAIL_CONTA_SERVICO} como"
        f" Editor. Detalhe do erro: {e}"
    )
else:
  st.info("Cole o link da sua planilha acima para começar a usar o bot.")


def encontrar_linha_despesa(worksheet, mes, item):
  """Procura, dentro do bloco do mês, a linha cujo Item corresponde."""
  valores = worksheet.get_all_values()
  for i, linha in enumerate(valores, start=1):
    if len(linha) >= 2 and linha[1].strip().upper() == mes and linha[0].strip() == item:
      return i
  return None


def encontrar_linha_receita(worksheet, mes, descricao):
  """Procura, dentro do bloco do mês, a primeira linha da Descrição
  indicada que ainda não tenha Valor preenchido (R$ 0,00)."""
  valores = worksheet.get_all_values()
  for i, linha in enumerate(valores, start=1):
    if (
        len(linha) >= 6
        and linha[1].strip().upper() == mes
        and linha[2].strip() == descricao
        and linha[5].strip() in ("R$ 0,00", "", "0", "0,00")
    ):
      return i
  return None


def atualizar_celula(worksheet, row, col, value):
  """Escreve numa célula usando USER_ENTERED, para que o Google Sheets
  interprete números e datas da mesma forma que interpretaria uma pessoa
  a escrever à mão — essencial para que as fórmulas do Resumo Mensal
  (SUMIFS, etc.) consigam somar os valores corretamente."""
  worksheet.update(
      range_name=rowcol_to_a1(row, col),
      values=[[value]],
      value_input_option="USER_ENTERED",
  )


if sh:
  # Interface para registo de transações
  st.markdown("---")
  st.subheader("📝 Adicionar Nova Transação")

  tipo = st.selectbox("Tipo de Movimento", ["Despesa", "Receita", "Cartão de Crédito"])

  if tipo == "Despesa":
    mes = st.selectbox("Mês de Referência", MESES_PT)
    item = st.selectbox("Item", ITENS_DESPESA)
    valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
    forma_pagamento = st.selectbox("Forma de Pagamento", FORMAS_PAGAMENTO)
    data_pagamento = st.date_input("Data de Pagamento", datetime.today(), format="DD/MM/YYYY")

    if st.button("Registrar Despesa"):
      if valor > 0:
        try:
          despesas_sheet = sh.worksheet("Despesas Mensais")
          linha = encontrar_linha_despesa(despesas_sheet, mes, item)
          if linha:
            atualizar_celula(despesas_sheet, linha, 3, valor)
            atualizar_celula(despesas_sheet, linha, 4, data_pagamento.strftime("%d/%m/%Y"))
            atualizar_celula(despesas_sheet, linha, 6, forma_pagamento)
            atualizar_celula(despesas_sheet, linha, 7, "PAGO")
            st.success(f"Despesa '{item}' de {mes} registrada com sucesso!")
          else:
            st.error(
                f"Não encontrei a linha de '{item}' para {mes} na planilha."
                " Confirma se o mês/item existem exatamente assim na aba"
                " 'Despesas Mensais'."
            )
        except Exception as ex:
          st.error(f"Erro ao escrever na folha: {ex}")
      else:
        st.warning("Por favor, indique um valor maior que zero.")

  elif tipo == "Receita":
    mes = st.selectbox("Mês de Referência", MESES_PT)
    descricao = st.selectbox("Descrição", DESCRICOES_RECEITA)
    categoria = st.text_input("Categoria (ex: Salário, Renda Extra, Rendimentos)")
    valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
    forma_recebimento = st.selectbox(
        "Forma de Recebimento",
        ["Dinheiro / PIX", "PIX", "Transferência", "Cartão de Débito", "Boleto Bancário"],
    )
    data_recebimento = st.date_input("Data", datetime.today(), format="DD/MM/YYYY")

    if st.button("Registrar Receita"):
      if valor > 0:
        try:
          receitas_sheet = sh.worksheet("Receitas")
          linha = encontrar_linha_receita(receitas_sheet, mes, descricao)
          if linha:
            atualizar_celula(receitas_sheet, linha, 1, data_recebimento.strftime("%d/%m/%Y"))
            if categoria:
              atualizar_celula(receitas_sheet, linha, 4, categoria)
            atualizar_celula(receitas_sheet, linha, 5, forma_recebimento)
            atualizar_celula(receitas_sheet, linha, 6, valor)
            st.success(f"Receita '{descricao}' de {mes} registrada com sucesso!")
          else:
            st.warning(
                f"Todas as linhas de '{descricao}' para {mes} já têm valor"
                " preenchido, ou não encontrei o bloco desse mês."
            )
        except Exception as ex:
          st.error(f"Erro ao escrever na folha: {ex}")
      else:
        st.warning("Por favor, indique um valor maior que zero.")

  elif tipo == "Cartão de Crédito":
    cartao = st.text_input("Cartão (ex: Nubank, Sicoob, Sicredi, Trigg)")
    descricao = st.text_input("Descrição da Compra (ex: Tênis Nike)")
    categoria = st.text_input("Categoria (ex: Vestuário, Escritório)")
    valor_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
    parcelas = st.number_input("Número de Parcelas", min_value=1, step=1, value=1)
    data_compra = st.date_input("Data da Compra", datetime.today(), format="DD/MM/YYYY")

    if st.button("Registrar Compra Parcelada"):
      if cartao and descricao and valor_total > 0:
        valor_parcela = valor_total / parcelas
        try:
          cartoes_sheet = sh.worksheet("Cartões de Crédito")
          data_str = data_compra.strftime("%d/%m/%Y")
          for i in range(int(parcelas)):
            mes_idx = (data_compra.month - 1 + i) % 12
            mes_ref = MESES_PT[mes_idx]
            valor_total_cel = valor_total if i == 0 else ""
            n_parcelas_restantes = int(parcelas) - i
            observacao = f"PARCELA {i + 1}"
            cartoes_sheet.append_row(
                [
                    data_str,
                    cartao,
                    descricao,
                    categoria,
                    valor_total_cel,
                    n_parcelas_restantes,
                    valor_parcela,
                    mes_ref,
                    observacao,
                ],
                value_input_option="USER_ENTERED",
            )
          st.success(
              f"Compra parcelada registrada com sucesso ({int(parcelas)}x de"
              f" R$ {valor_parcela:.2f})!"
          )
        except Exception as ex:
          st.error(f"Erro ao escrever na folha: {ex}")
      else:
        st.warning("Por favor, preencha o cartão, a descrição e o valor.")

st.markdown(
    f"""
    <div style="
        background-color: {AZUL_MARINHO};
        padding: 1em;
        border-radius: 12px;
        margin-top: 2em;
        text-align: center;
    ">
        <p style="color: white; font-weight: 700; letter-spacing: 0.05em; margin: 0;">
            PROJETO INTEGRACON • ACEC UNESPAR CAMPUS PARANAGUÁ
        </p>
        <p style="color: {AZUL_CLARO_FUNDO}; font-size: 0.85em; margin: 0.3em 0 0 0;">
            Finanças do Lar na Prática
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
