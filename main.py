# ✅ ESTA LINHA TEM QUE SER A PRIMEIRA EXECUTÁVEL!
import streamlit as st
st.set_page_config(page_title="Confronto XML x Invoice", layout="wide")

import os
import pandas as pd
import io
import requests
from datetime import datetime, timedelta
from utils import parser_xml, parser_invoice, comparador
import numpy as np

st.title("📦 Confronto de XML da NF-e com Invoice (CI)")

# ---- Box da cotação do dólar no topo direito ----
def get_cotacao_usd():
    try:
        hoje = datetime.now()
        ontem = hoje - timedelta(days=1)
        url = "https://economia.awesomeapi.com.br/json/daily/USD-BRL/2"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        cotacoes = r.json()
        cotacoes_ordenadas = sorted(
            cotacoes,
            key=lambda x: x['timestamp'],
            reverse=True
        )
        cotacao_hoje = cotacoes_ordenadas[0]
        cotacao_ontem = cotacoes_ordenadas[1]
        dolar_hoje = float(cotacao_hoje['bid'])
        data_hoje_str = datetime.fromtimestamp(int(cotacao_hoje['timestamp'])).strftime('%d/%m/%Y')
        dolar_ontem = float(cotacao_ontem['bid'])
        data_ontem_str = datetime.fromtimestamp(int(cotacao_ontem['timestamp'])).strftime('%d/%m/%Y')
        return {
            "hoje": {"valor": dolar_hoje, "data": data_hoje_str},
            "ontem": {"valor": dolar_ontem, "data": data_ontem_str}
        }
    except Exception as e:
        return None

cotacoes = get_cotacao_usd()
st.markdown(" ")
_, col_cotacao = st.columns([7, 1])
if cotacoes:
    st.markdown(
        f"""
        <div style='display:flex;flex-direction:column;align-items:end; margin-top:-30px; margin-bottom:10px;'>
          <div style='background:#232931;padding:18px 32px;border-radius:18px;box-shadow:0 2px 8px #00000015;min-width:260px;'>
            <div style='font-size:1.7rem;font-weight:700;color:#3be180;margin-bottom:5px;'>
                <span style="font-size:2rem;">$</span> Dólar Comercial
            </div>
            <div style='font-size:1rem;color:#f5f5f5;margin-bottom:7px;'>
                Cotação hoje <b>({cotacoes['hoje']['data']})</b><br>
                <span style='font-size:1.3rem;color:#fff;font-weight:700;'>R$ {cotacoes['hoje']['valor']:.4f}</span>
            </div>
            <div style='font-size:1rem;color:#f5f5f5;'>
                Cotação ontem <b>({cotacoes['ontem']['data']})</b><br>
                <span style='font-size:1.3rem;color:#fff;font-weight:700;'>R$ {cotacoes['ontem']['valor']:.4f}</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.error("Não foi possível obter a cotação do dólar.")

# --- Upload dos arquivos ---
st.header("📁 Upload de Arquivos")

modelo_path = os.path.join("utils", "modelo_invoice.xlsx")
with st.expander("📥 Baixar modelo da planilha Invoice"):
    try:
        with open(modelo_path, "rb") as f:
            st.download_button(
                label="📥 Clique aqui para baixar o modelo (.xlsx)",
                data=f,
                file_name="modelo_invoice.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        st.info("Use esse modelo para colar os dados da sua Invoice no formato esperado.")
    except FileNotFoundError:
        st.error("Arquivo 'modelo_invoice.xlsx' não encontrado em `utils/`.")

col1, col2 = st.columns(2)

with col1:
    xml_file = st.file_uploader("📤 Enviar XML da NF-e", type=["xml"], key="xml")

with col2:
    invoice_file = st.file_uploader("📤 Enviar Planilha da Invoice (aba 'CI')", type=["xlsx", "xls"], key="invoice")

# --- Checkbox Grade ---
grade_mode = st.checkbox("Usar cálculo por Grade (total pares = quantidade × caixas por tamanho)")

# --- NOVO BLOCO: Conversão de moeda ---
st.markdown("### 💵 Opções de Conversão de Moeda")

col_a, col_b, col_c, col_d = st.columns([1,1,2,2])
with col_a:
    xml_em_dolar = st.checkbox("XML em dólar")
with col_b:
    invoice_em_dolar = st.checkbox("Invoice em dólar")
with col_c:
    usar_cotacao_auto = st.checkbox("Usar cotação automática (dia anterior)", value=False)
with col_d:
    cotacao_manual = st.number_input("Cotação manual (opcional)", value=0.0, format="%.4f")

if xml_em_dolar and invoice_em_dolar:
    st.error("Selecione apenas um dos campos como 'em dólar' para realizar a conversão.")
    st.stop()

cotacao_dolar = None
if usar_cotacao_auto or cotacao_manual == 0:
    cotacao_dolar = cotacoes['ontem']['valor'] if cotacoes else 1.0
else:
    cotacao_dolar = cotacao_manual if cotacao_manual > 0 else (cotacoes['ontem']['valor'] if cotacoes else 1.0)

def converter_para_reais(df, campos, cotacao):
    for campo in campos:
        if campo in df.columns:
            df[campo] = np.round(df[campo].astype(float) * cotacao, 2)
    return df

# --- Processamento após upload ---
if xml_file and invoice_file:
    st.success("✅ Arquivos carregados com sucesso.")

    # Parse dos dados
    st.header("🔍 Prévia dos Dados Carregados")

    with st.spinner("Lendo XML..."):
        dados_xml, resumo_xml = parser_xml.processar(xml_file)

    with st.spinner("Lendo Invoice..."):
        dados_invoice, resumo_invoice = parser_invoice.processar(invoice_file, usar_grade=grade_mode)

    if "erro" in resumo_invoice:
        st.error(f"Erro ao processar Invoice: {resumo_invoice['erro']}")
        st.stop()

    # -- CONVERSÃO DE MOEDA ANTES DO CONFRONTO --
    campos_monetarios = ["preço unitário", "valor total"]

    if xml_em_dolar:
        df_xml_conv = converter_para_reais(pd.DataFrame(dados_xml), campos_monetarios, cotacao_dolar)
        if "valor total xml" in resumo_xml:
            resumo_xml["valor total xml"] = round(float(resumo_xml["valor total xml"]) * cotacao_dolar, 2)
        dados_xml = df_xml_conv.to_dict("records")
    elif invoice_em_dolar:
        df_invoice_conv = converter_para_reais(pd.DataFrame(dados_invoice), campos_monetarios, cotacao_dolar)
        if "valor total nota" in resumo_invoice:
            resumo_invoice["valor total nota"] = round(float(resumo_invoice["valor total nota"]) * cotacao_dolar, 2)
        dados_invoice = df_invoice_conv.to_dict("records")

    # Mostrar resumos
    st.subheader("📑 Resumo do XML")
    st.json(resumo_xml, expanded=False)

    st.subheader("📑 Resumo da Invoice (CI)")
    st.json(resumo_invoice, expanded=False)

    # Mostrar todos os itens (marca/modelo REMOVIDA do XML)
    st.subheader("🔎 Todos os itens do XML")
    df_xml_view = pd.DataFrame(dados_xml).copy()
    if "marca" in df_xml_view.columns:
        df_xml_view = df_xml_view.drop(columns=["marca"])
    st.dataframe(df_xml_view, use_container_width=True)

    st.subheader("🔎 Todos os itens da Invoice")
    st.dataframe(pd.DataFrame(dados_invoice), use_container_width=True)

    # Confronto
    if st.button("🚨 Confrontar XML x Invoice"):
        with st.spinner("Comparando os dados..."):
            resultado = comparador.confrontar(dados_xml, dados_invoice)
            st.session_state["resultado"] = resultado
            st.session_state["mostrar_erros"] = False

    # Exibir resultado do confronto (se houver)
    if "resultado" in st.session_state:
        resultado = st.session_state["resultado"]

        st.subheader("📊 Resultado do Confronto")
        st.dataframe(resultado, use_container_width=True)

        # --- RESUMO DE ERROS ---
        erros = resultado[
            (resultado["verificação total pares"] != "✅ OK") |
            (resultado["verificação preço unitário"] != "✅ OK") |
            (resultado["verificação valor total"] != "✅ OK")
        ]
        st.session_state["erros"] = erros
        qtd_erros = len(erros)

        st.markdown("### ❗ Resumo de Divergências")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total de Itens com Erros", qtd_erros)

        with col2:
            if st.button("🔍 Exibir Apenas os Erros"):
                st.session_state["mostrar_erros"] = True

        if st.session_state.get("mostrar_erros", False):
            st.subheader("🧯 Itens com Divergência")
            st.dataframe(erros, use_container_width=True)

        if not erros.empty:
            buffer = io.BytesIO()
            erros.to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                label="📥 Baixar Erros em Excel",
                data=buffer,
                file_name="erros_confronto.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    st.markdown("---")
    if st.button("🔄 Iniciar Nova Confrontação"):
        st.session_state.clear()
        st.rerun()

else:
    st.warning("⚠️ Envie os dois arquivos para iniciar.")
