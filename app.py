from datetime import date
import streamlit as st
import pandas as pd

from core.parsers import parse_premmia, parse_moeda_saqua
from core.formatters import format_currency, generate_whatsapp_summary

st.set_page_config(
    page_title="Fechamento Financeiro",
    page_icon="⛽",
    layout="wide"
)

st.title("⛽ Fechamento Financeiro Diário")
st.caption("• Leitura Segura em Memória (Sem Armazenamento de Dados)")

# 1. SELEÇÃO DA DATA
st.markdown("### 1. Seleção da Data")
col_date, _ = st.columns([2, 4])
with col_date:
    selected_date = st.date_input(
        "Fechamento referente a:",
        value=date.today(),
        format="DD/MM/YYYY"
    )

target_date_str = selected_date.strftime("%d/%m/%Y")

# 2. UPLOAD DOS ARQUIVOS
st.markdown("---")
st.markdown(f"### 2. Inserir Planilhas do dia **{target_date_str}**")

col_saqua, col_premmia, col_pos = st.columns(3)

with col_saqua:
    st.subheader("🪙 Moeda Saquá")
    saqua_files = st.file_uploader(
        "Upload Extratos (Até 5 arquivos)",
        type=["xlsx", "xls", "csv", "ods"],
        accept_multiple_files=True,
        key="saqua_uploader"
    )
    if len(saqua_files) > 5:
        st.warning("⚠️ Limite de 5 arquivos por slot excedido. Apenas os 5 primeiros serão processados.")
        saqua_files = saqua_files[:5]

with col_premmia:
    st.subheader("📱 App Premmia")
    premmia_files = st.file_uploader(
        "Upload Conferência (Até 5 arquivos)",
        type=["xlsx", "xls", "csv", "ods"],
        accept_multiple_files=True,
        key="premmia_uploader"
    )
    if len(premmia_files) > 5:
        st.warning("⚠️ Limite de 5 arquivos por slot excedido. Apenas os 5 primeiros serão processados.")
        premmia_files = premmia_files[:5]

with col_pos:
    st.subheader("💳 Maquininhas de Cartão")
    st.info("🚀 **Em breve** — Módulo em desenvolvimento.")
    st.file_uploader("Slot desabilitado", disabled=True, key="pos_disabled")

# 3. PROCESSAMENTO E DASHBOARD
if saqua_files or premmia_files:
    st.markdown("---")
    st.markdown(f"## 📈 Dashboard de Fechamento • {target_date_str}")
    
    res_premmia = parse_premmia(premmia_files, target_date_str) if premmia_files else None
    res_saqua = parse_moeda_saqua(saqua_files, target_date_str) if saqua_files else None

    # Moeda Saquá
    if res_saqua and res_saqua["total_bruto"] > 0:
        st.markdown("### 🪙 Moeda Saquá")
        table_rows = []
        for conta, dados in res_saqua["contas"].items():
            table_rows.append({
                "Conta": conta,
                "Transações": dados["qtd_vendas"],
                "Vendas Brutas": format_currency(dados["vendas_brutas"]),
                "Taxas": format_currency(dados["taxas"]),
                "% Taxa": f"{dados['pct_taxa']:.2f}%",
                "Valor Líquido": format_currency(dados["liquido"])
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Bruto de Vendas", format_currency(res_saqua["total_bruto"]))
        c2.metric("Total de Taxas (2%)", format_currency(res_saqua["total_taxas"]))
        c3.metric("Total Líquido Creditado", format_currency(res_saqua["total_liquido"]))

    # Premmia
    if res_premmia and res_premmia["total_tx"] > 0:
        st.markdown("### 📱 App Premmia")
        table_p = []
        for forma, info in res_premmia["breakdown"].items():
            table_p.append({
                "Forma de Pagamento": forma,
                "Quantidade": f"{info['qtd']} transações",
                "Valor": format_currency(info["total"])
            })
        st.dataframe(pd.DataFrame(table_p), use_container_width=True, hide_index=True)
        
        p1, p2, p3 = st.columns(3)
        p1.metric("Recebido (Cartão APP + Pix)", format_currency(res_premmia["recebido"]))
        p2.metric("Descontos Concedidos", format_currency(res_premmia["descontos"]))
        p3.metric("Total Geral Premmia", format_currency(res_premmia["total_geral"]))

    # 4. EXPORTAÇÃO
    st.markdown("---")
    st.markdown("### 📤 Exportar Fechamento")
    resumo_whatsapp = generate_whatsapp_summary(target_date_str, res_premmia, res_saqua)
    st.text_area("Texto formatado para WhatsApp:", value=resumo_whatsapp, height=220)
    st.download_button(
        label="📥 Baixar Resumo (.txt)",
        data=resumo_whatsapp,
        file_name=f"fechamento_{target_date_str.replace('/', '-')}.txt",
        mime="text/plain"
    )
else:
    st.info("Selecione a data e faça o upload das planilhas para gerar o dashboard.")
