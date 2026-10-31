from datetime import date
import streamlit as st
import pandas as pd
import plotly.express as px

from core.parsers import parse_premmia, parse_moeda_saqua
from core.formatters import format_currency, generate_whatsapp_summary

st.set_page_config(
    page_title="Fechamento Financeiro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Customizado para aparência profissional White-Label
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-size: 16px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.title("Fechamento Financeiro Diário")
st.caption("Processamento Seguro em Memória (Nenhum dado é salvo no servidor)")

# 1. SELEÇÃO DA DATA
st.markdown("### Seleção da Data")
col_date, _ = st.columns([2, 4])
with col_date:
    selected_date = st.date_input(
        "Fechamento referente a:",
        value=date.today(),
        format="DD/MM/YYYY"
    )

target_date_str = selected_date.strftime("%d/%m/%Y")

st.markdown("---")
st.markdown(f"### Inserir Planilhas do dia **{target_date_str}**")

# Layout com Abas em vez de Colunas
tab_premmia, tab_saqua, tab_pos = st.tabs(["App Premmia", "Moeda Saquá", "Maquininhas de Cartão"])

with tab_premmia:
    premmia_files = st.file_uploader(
        "Upload Conferência Premmia (Até 5 arquivos)",
        type=["xlsx", "xls", "csv", "ods"],
        accept_multiple_files=True,
        key="premmia_uploader"
    )
    if len(premmia_files) > 5:
        st.warning("Limite de 5 arquivos por vez excedido. Apenas os 5 primeiros serão processados.")
        premmia_files = premmia_files[:5]

with tab_saqua:
    saqua_files = st.file_uploader(
        "Upload Extratos Moeda Saquá (Até 5 arquivos)",
        type=["xlsx", "xls", "csv", "ods"],
        accept_multiple_files=True,
        key="saqua_uploader"
    )
    if len(saqua_files) > 5:
        st.warning("Limite de 5 arquivos por vez excedido. Apenas os 5 primeiros serão processados.")
        saqua_files = saqua_files[:5]

with tab_pos:
    st.info("Módulo em desenvolvimento. Estará disponível em breve.")
    st.file_uploader("Upload desabilitado", disabled=True, key="pos_disabled")


# PROCESSAMENTO E DASHBOARD
if saqua_files or premmia_files:
    st.markdown("---")
    st.header(f"Dashboard de Fechamento - {target_date_str}")
    
    try:
        res_premmia = parse_premmia(premmia_files, target_date_str) if premmia_files else None
    except Exception as e:
        st.error("Erro ao ler as planilhas do App Premmia. Verifique se os arquivos estão corretos.")
        res_premmia = None

    try:
        res_saqua = parse_moeda_saqua(saqua_files, target_date_str) if saqua_files else None
    except Exception as e:
        st.error("Erro ao ler os extratos do Moeda Saquá. Verifique se os arquivos estão corretos.")
        res_saqua = None

    # Divisão de tela inteligente (se tiver as 2 planilhas, divide no meio. Se tiver 1, ocupa tudo)
    dash_col1, dash_col2 = st.columns(2)
    show_premmia = res_premmia and res_premmia["total_tx"] > 0
    show_saqua = res_saqua and res_saqua["total_bruto"] > 0

    if show_premmia:
        cont_p = dash_col1 if show_saqua else st.container()
        with cont_p:
            st.subheader("App Premmia")
            
            p1, p2, p3 = st.columns(3)
            p1.markdown(f"**Recebido (APP + Pix)**\n### {format_currency(res_premmia['recebido'])}")
            p2.metric("Descontos", format_currency(res_premmia["descontos"]))
            p3.metric("Total Geral", format_currency(res_premmia["total_geral"]))

            # Gráfico Donut para Premmia
            if res_premmia["recebido"] > 0:
                df_chart_p = pd.DataFrame([
                    {"Forma": k, "Valor": v["total"]} 
                    for k, v in res_premmia["breakdown"].items() if v["total"] > 0
                ])
                fig_p = px.pie(df_chart_p, values='Valor', names='Forma', hole=0.6,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_p.update_traces(textposition='inside', textinfo='percent+label')
                fig_p.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=280, showlegend=False)
                st.plotly_chart(fig_p, use_container_width=True)

            table_p = []
            for forma, info in res_premmia["breakdown"].items():
                table_p.append({
                    "Pagamento": forma,
                    "Qtd": f"{info['qtd']}",
                    "Valor": format_currency(info["total"])
                })
            st.dataframe(pd.DataFrame(table_p), use_container_width=True, hide_index=True)


    if show_saqua:
        cont_s = dash_col2 if show_premmia else st.container()
        with cont_s:
            st.subheader("Moeda Saquá")
            
            s1, s2, s3 = st.columns(3)
            s1.markdown(f"**Total Bruto**\n### {format_currency(res_saqua['total_bruto'])}")
            s2.metric("Taxas (2%)", format_currency(res_saqua["total_taxas"]))
            s3.metric("Líquido", format_currency(res_saqua["total_liquido"]))

            # Gráfico Donut para Moeda Saquá
            if res_saqua["total_bruto"] > 0:
                df_chart_s = pd.DataFrame({
                    "Categoria": ["Líquido Creditado", "Taxas Retidas"],
                    "Valor": [res_saqua["total_liquido"], abs(res_saqua["total_taxas"])]
                })
                fig_s = px.pie(df_chart_s, values='Valor', names='Categoria', hole=0.6,
                             color_discrete_sequence=["#10b981", "#ef4444"])
                fig_s.update_traces(textposition='inside', textinfo='percent+label')
                fig_s.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=280, showlegend=False)
                st.plotly_chart(fig_s, use_container_width=True)

            table_rows = []
            for conta, dados in res_saqua["contas"].items():
                table_rows.append({
                    "Conta": conta,
                    "Qtd": dados["qtd_vendas"],
                    "Bruto": format_currency(dados["vendas_brutas"]),
                    "Taxas": format_currency(dados["taxas"]),
                    "Líquido": format_currency(dados["liquido"])
                })
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    # EXPORTAÇÃO
    st.markdown("---")
    st.markdown("### Exportar Fechamento")
    resumo_whatsapp = generate_whatsapp_summary(target_date_str, res_premmia, res_saqua)
    st.text_area("Copiar para WhatsApp:", value=resumo_whatsapp, height=220)
    st.download_button(
        label="Baixar Resumo (.txt)",
        data=resumo_whatsapp,
        file_name=f"fechamento_{target_date_str.replace('/', '-')}.txt",
        mime="text/plain"
    )
else:
    st.info("Selecione a data e insira as planilhas nas abas acima para gerar o dashboard.")
