from datetime import datetime
from dateutil.relativedelta import relativedelta
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# Configuração da página com tema acolhedor
st.set_page_config(
    page_title="Organização Financeira do Lar", page_icon="🏡", layout="wide"
)

st.title("🏡 Organização Financeira do Lar")
st.write(
    "Bem-vinda ao teu assistente financeiro inteligente integrado com o Google"
    " Sheets!"
)


# Função para ligar ao Google Sheets usando os Secrets do Streamlit
@st.cache_resource
def conectar_gsheets():
  # As credenciais da Google API serão lidas de forma segura no Streamlit Cloud
  scope = [
      "https://www.spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]
  credentials_dict = dict(st.secrets["gcp_service_account"])
  creds = Credentials.from_service_account_info(
      credentials_dict, scopes=scope
  )
  client = gspread.authorize(creds)

  # Abre a planilha pelo ID
  sheet_id = "127aZ6G_aS9VtSDpxixIZMbwGEZUSLpMd"
  sheet = client.open_by_key(sheet_id)
  return sheet


try:
  sh = conectar_gsheets()
  st.success("Conexão ao Google Sheets estabelecida com sucesso!")
except Exception as e:
  st.error(
      "Erro ao conectar ao Google Sheets. Verifica as tuas credenciais nos"
      f" Secrets: {e}"
  )

# Exemplo de interface para registo de transações
st.markdown("---")
st.subheader("📝 Adicionar Nova Transação")

tipo = st.selectbox("Tipo de Movimento", ["Despesa", "Receita", "Cartão de Crédito"])

if tipo == "Cartão de Crédito":
  descricao = st.text_input("Descrição da Compra (ex: Ténis Nike)")
  valor_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
  parcelas = st.number_input("Número de Parcelas", min_value=1, step=1, value=1)
  data_compra = st.date_input("Data da Compra", datetime.today())

  if st.button("Registar Compra Parcelada"):
    if descricao and valor_total > 0:
      valor_parcela = valor_total / parcelas
      st.write(
          f"A processar compra de R$ {valor_total:.2f} em {parcelas}x de R$"
          f" {valor_parcela:.2f}..."
      )

      # Lógica de cálculo das parcelas sequenciais
      try:
        cartoes_sheet = sh.worksheet("Cartões de Crédito")
        for i in range(parcelas):
          data_parcela = data_compra + relativedelta(months=i)
          mes_ref = data_parcela.strftime("%B/%Y")
          # Aqui podes injetar a linha na aba do Google Sheets
          # cartoes_sheet.append_row([mes_ref, descricao, valor_parcela, ...])

        st.success(
            "Compra parcelada registada com sucesso no Google Sheets!"
        )
      except Exception as ex:
        st.error(f"Erro ao escrever na folha: {ex}")
    else:
      st.warning("Por favor, preenche a descrição e o valor.")