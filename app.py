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

st.markdown('''
<style>
    /* Esconder TODO o cabeçalho branco superior e menus do Streamlit */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Remover o espaço vazio que fica sobrando no topo após esconder o header */
    .block-container {
        padding-top: 2rem !important;
    }
    
    /* 2. Abas Bloqueadas/Fixas no topo (Sticky) - Agora coladas exatamente no topo */
    div[data-testid="stTabs"] {
        position: sticky;
        top: 0rem; /* Colado perfeitamente no topo */
        z-index: 999;
        background-color: #f4f6f8;
        padding-bottom: 15px;
        padding-top: 15px; /* Adicionado um respiro superior */
        border-bottom: 1px solid #e2e8f0;
        border-radius: 0 0 10px 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    
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

    /* 3. Caixas mais bonitas (Sombras e Efeitos de Hover) */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px 10px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
        white-space: nowrap !important;
        overflow: visible !important;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: clamp(1.2rem, 1.8vw, 1.8rem) !important;
        white-space: normal !important;
        word-break: break-all !important;
        overflow: visible !important;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px rgba(0,0,0,0.1);
        border-color: #0056b3;
    }
    
    .stDataFrame {
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
    }

    div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button {
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-radius: 8px;
    }
    div[data-testid="stButton"] button:hover, div[data-testid="stDownloadButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        background-color: #004494;
        color: #ffffff;
        border-color: #004494;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    div[data-testid="stMetric"], .stDataFrame, .js-plotly-plot, .stTextArea {
        animation: fadeInUp 0.6s ease-out forwards;
    }
</style>
''', unsafe_allow_html=True)

st.title("Fechamento Financeiro Diário")
st.caption("Processamento Seguro em Memória (Nenhum dado é salvo no servidor)")

col_date, _ = st.columns([2, 4])
with col_date:
    selected_date = st.date_input(
        "Fechamento referente a:",
        value=date.today(),
        format="DD/MM/YYYY"
    )

target_date_str = selected_date.strftime("%d/%m/%Y")

tab_premmia, tab_saqua, tab_pos = st.tabs(["App Premmia", "Moeda Saquá", "Maquininhas de Cartão"])

with tab_premmia:
    premmia_files = st.file_uploader(
        f"Upload Conferência Premmia ({target_date_str})",
        type=["xlsx", "xls", "csv", "ods"],
        accept_multiple_files=True,
        key="premmia_uploader"
    )
    if len(premmia_files) > 5:
        st.warning("Limite de 5 arquivos por vez excedido. Apenas os 5 primeiros serão processados.")
        premmia_files = premmia_files[:5]

with tab_saqua:
    saqua_files = st.file_uploader(
        f"Upload Extratos Moeda Saquá ({target_date_str})",
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

    dash_col1, dash_col2 = st.columns(2)
    show_premmia = res_premmia and res_premmia["total_tx"] > 0
    show_saqua = res_saqua and res_saqua["total_bruto"] > 0

    if show_premmia:
        cont_p = dash_col1 if show_saqua else st.container()
        with cont_p:
            st.subheader("App Premmia")
            
            p1, p2, p3 = st.columns(3)
            p1.metric("Recebido (APP + Pix)", format_currency(res_premmia['recebido']))
            p2.metric("Descontos", format_currency(res_premmia["descontos"]))
            p3.metric("Total Geral", format_currency(res_premmia["total_geral"]))

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
            s1.metric("Total Bruto", format_currency(res_saqua['total_bruto']))
            s2.metric("Taxas", format_currency(res_saqua["total_taxas"]))
            s3.metric("Líquido", format_currency(res_saqua["total_liquido"]))

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
