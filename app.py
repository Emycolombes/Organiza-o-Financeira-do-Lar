from datetime import datetime
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


# Função para ligar ao Google Sheets usando os Secrets do Streamlit
@st.cache_resource
def conectar_gsheets():
  # As credenciais da Google API serão lidas de forma segura no Streamlit Cloud
  scope = [
      "https://www.googleapis.com/auth/spreadsheets",
      "https://www.googleapis.com/auth/drive",
  ]
  credentials_dict = dict(st.secrets["gcp_service_account"])
  creds = Credentials.from_service_account_info(
      credentials_dict, scopes=scope
  )
  client = gspread.authorize(creds)

  # Abre a planilha pelo ID
  sheet_id = "1bai4RSlopyqdJZCRvCXoLw0qNwhUlv0HL0v0AOe6IDc"
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


# Interface para registo de transações
st.markdown("---")
st.subheader("📝 Adicionar Nova Transação")

tipo = st.selectbox("Tipo de Movimento", ["Despesa", "Receita", "Cartão de Crédito"])

if tipo == "Despesa":
  mes = st.selectbox("Mês de Referência", MESES_PT)
  item = st.selectbox("Item", ITENS_DESPESA)
  valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
  forma_pagamento = st.selectbox("Forma de Pagamento", FORMAS_PAGAMENTO)
  data_pagamento = st.date_input("Data de Pagamento", datetime.today())

  if st.button("Registar Despesa"):
    if valor > 0:
      try:
        despesas_sheet = sh.worksheet("Despesas Mensais")
        linha = encontrar_linha_despesa(despesas_sheet, mes, item)
        if linha:
          despesas_sheet.update_cell(linha, 3, f"R$ {valor:.2f}".replace(".", ","))
          despesas_sheet.update_cell(linha, 4, data_pagamento.strftime("%d/%m/%Y"))
          despesas_sheet.update_cell(linha, 6, forma_pagamento)
          despesas_sheet.update_cell(linha, 7, "PAGO")
          st.success(f"Despesa '{item}' de {mes} registada com sucesso!")
        else:
          st.error(
              f"Não encontrei a linha de '{item}' para {mes} na planilha."
              " Confirma se o mês/item existem exatamente assim na aba"
              " 'Despesas Mensais'."
          )
      except Exception as ex:
        st.error(f"Erro ao escrever na folha: {ex}")
    else:
      st.warning("Por favor, indica um valor maior que zero.")

elif tipo == "Receita":
  mes = st.selectbox("Mês de Referência", MESES_PT)
  descricao = st.selectbox("Descrição", DESCRICOES_RECEITA)
  categoria = st.text_input("Categoria (ex: Salário, Renda Extra, Rendimentos)")
  valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
  forma_recebimento = st.selectbox(
      "Forma de Recebimento",
      ["Dinheiro / PIX", "PIX", "Transferência", "Cartão de Débito", "Boleto Bancário"],
  )
  data_recebimento = st.date_input("Data", datetime.today())

  if st.button("Registar Receita"):
    if valor > 0:
      try:
        receitas_sheet = sh.worksheet("Receitas")
        linha = encontrar_linha_receita(receitas_sheet, mes, descricao)
        if linha:
          receitas_sheet.update_cell(linha, 1, data_recebimento.strftime("%d/%m/%Y"))
          if categoria:
            receitas_sheet.update_cell(linha, 4, categoria)
          receitas_sheet.update_cell(linha, 5, forma_recebimento)
          receitas_sheet.update_cell(linha, 6, f"R$ {valor:.2f}".replace(".", ","))
          st.success(f"Receita '{descricao}' de {mes} registada com sucesso!")
        else:
          st.warning(
              f"Todas as linhas de '{descricao}' para {mes} já têm valor"
              " preenchido, ou não encontrei o bloco desse mês."
          )
      except Exception as ex:
        st.error(f"Erro ao escrever na folha: {ex}")
    else:
      st.warning("Por favor, indica um valor maior que zero.")

elif tipo == "Cartão de Crédito":
  cartao = st.text_input("Cartão (ex: Nubank, Sicoob, Sicredi, Trigg)")
  descricao = st.text_input("Descrição da Compra (ex: Ténis Nike)")
  categoria = st.text_input("Categoria (ex: Vestuário, Escritório)")
  valor_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
  parcelas = st.number_input("Número de Parcelas", min_value=1, step=1, value=1)
  data_compra = st.date_input("Data da Compra", datetime.today())

  if st.button("Registar Compra Parcelada"):
    if cartao and descricao and valor_total > 0:
      valor_parcela = valor_total / parcelas
      try:
        cartoes_sheet = sh.worksheet("Cartões de Crédito")
        data_str = data_compra.strftime("%d/%m/%Y")
        for i in range(int(parcelas)):
          mes_idx = (data_compra.month - 1 + i) % 12
          mes_ref = MESES_PT[mes_idx]
          valor_total_str = (
              f"R$ {valor_total:.2f}".replace(".", ",") if i == 0 else ""
          )
          n_parcelas_restantes = int(parcelas) - i
          observacao = f"PARCELA {i + 1}"
          cartoes_sheet.append_row([
              data_str,
              cartao,
              descricao,
              categoria,
              valor_total_str,
              n_parcelas_restantes,
              f"R$ {valor_parcela:.2f}".replace(".", ","),
              mes_ref,
              observacao,
          ])
        st.success(
            f"Compra parcelada registada com sucesso ({int(parcelas)}x de"
            f" R$ {valor_parcela:.2f})!"
        )
      except Exception as ex:
        st.error(f"Erro ao escrever na folha: {ex}")
    else:
      st.warning("Por favor, preenche o cartão, a descrição e o valor.")
