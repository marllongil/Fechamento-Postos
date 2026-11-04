import time
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

# Inicializa as variáveis de controle de sessão
if "login_state" not in st.session_state:
    st.session_state.login_state = "pending"
if "toast_shown" not in st.session_state:
    st.session_state.toast_shown = False
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

is_auth = (st.session_state.login_state == "authenticated")

# ==========================================
# INJEÇÃO DE CSS E ANIMAÇÕES
# ==========================================
st.markdown('''
<style>
    /* Esconder cabeçalho e rodapé do Streamlit */
    header[data-testid="stHeader"] { display: none !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container { padding-top: 2rem !important; }
    
    /* Abas fixas */
    div[data-testid="stTabs"] {
        position: sticky; top: 0rem; z-index: 990;
        background-color: #f4f6f8; padding-bottom: 15px; padding-top: 15px; 
        border-bottom: 1px solid #e2e8f0; border-radius: 0 0 10px 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: transparent;
        border-radius: 4px 4px 0px 0px; padding-top: 10px; padding-bottom: 10px;
        font-size: 16px; font-weight: 600;
    }
    
    /* Estilos dos Cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff; padding: 15px 10px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04); border: 1px solid #e2e8f0;
        transition: all 0.3s ease; white-space: nowrap !important; overflow: visible !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: clamp(1.2rem, 1.8vw, 1.8rem) !important;
        white-space: normal !important; word-break: break-all !important; overflow: visible !important;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px); box-shadow: 0 10px 15px rgba(0,0,0,0.1); border-color: #0056b3;
    }
    .stDataFrame {
        box-shadow: 0 4px 6px rgba(0,0,0,0.04); border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0;
    }
    
    /* Botões */
    div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button {
        transition: all 0.3s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-radius: 8px;
    }
    div[data-testid="stButton"] button:hover, div[data-testid="stDownloadButton"] button:hover {
        transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        background-color: #004494; color: #ffffff; border-color: #004494;
    }
    button[kind="secondary"] { border-color: #e2e8f0; }
    
    /* AJUSTE DO TOAST (NOTIFICAÇÃO) PARA NÃO CORTAR O TEXTO */
    div[data-testid="stToast"] {
        min-width: 380px !important;
        padding: 15px !important;
    }
    div[data-testid="stToast"] [data-testid="stMarkdownContainer"] p {
        display: block !important;
        white-space: normal !important;
        -webkit-line-clamp: unset !important;
        overflow: visible !important;
        font-size: 15px;
    }
    
    /* Animação de Entrada do Dashboard */
    @keyframes fadeInUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
    div[data-testid="stMetric"], .stDataFrame, .js-plotly-plot, .stTextArea { animation: fadeInUp 0.6s ease-out forwards; }

    /* ========================================================= */
    /* ESTILOS DO MODAL OVERLAY (PSEUDO-LOGIN)                   */
    /* ========================================================= */
    
    div[data-testid="stVerticalBlock"]:has(#login-modal-marker),
    div[data-testid="stVerticalBlock"]:has(#login-animating) {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 550px; /* MAIS LARGO E MENOS APERTADO */
        max-width: 95vw;
        z-index: 9999;
        background: #ffffff;
        padding: 40px; /* MAIS RESPIRO INTERNO */
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    
    /* FUNDO SÓLIDO E LIMPO (SEM BLUR POLUÍDO) */
    div[data-testid="stApp"]:has(#login-modal-marker)::before,
    div[data-testid="stApp"]:has(#login-animating)::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: #f4f6f8;
        z-index: 9998;
    }
    
    div[data-testid="stVerticalBlock"]:has(#login-modal-marker) [data-testid="stForm"],
    div[data-testid="stVerticalBlock"]:has(#login-animating) [data-testid="stForm"] {
        border: none;
        padding: 0;
        box-shadow: none;
    }
    
    /* ANIMAÇÃO LIMPA: DESLIZA DIRETO PRO LADO E SOME */
    div[data-testid="stVerticalBlock"]:has(#login-animating) {
        animation: slideOutRight 0.3s forwards ease-in;
    }
    
    @keyframes slideOutRight {
        0% { transform: translate(-50%, -50%); opacity: 1; }
        100% { transform: translate(150vw, -50%); opacity: 0; }
    }
</style>
''', unsafe_allow_html=True)

# ==========================================
# SISTEMA DE NOTIFICAÇÃO (TOAST)
# ==========================================
if st.session_state.login_state == "pending" and not st.session_state.toast_shown:
    # TEXTO SEM EMOJIS - Aparecerá perfeitamente na lateral sem precisar clicar
    st.toast("Obrigado por usar nosso aplicativo! Para acessá-lo, caso se sinta à vontade, preencha os dados na tela. Isso nos ajuda a manter a organização do fechamento de caixa.")
    st.session_state.toast_shown = True

# ==========================================
# CAIXA MODAL DE LOGIN
# ==========================================
if st.session_state.login_state in ["pending", "animating"]:
    modal_container = st.empty()
    with modal_container.container():
        if st.session_state.login_state == "pending":
            st.markdown('<div id="login-modal-marker"></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div id="login-animating"></div>', unsafe_allow_html=True)
            
        st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>Acesso ao Sistema</h3>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            # REMOVIDOS OS PLACEHOLDERS DE EXEMPLO
            nome = st.text_input("Seu Nome")
            cargo = st.text_input("Sua Função ou Cargo")
            posto = st.text_input("Nome do Posto")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submit_btn = st.form_submit_button("Acessar", use_container_width=True)
            
            if submit_btn:
                if nome and cargo and posto:
                    st.session_state.user_nome = nome
                    st.session_state.user_cargo = cargo
                    st.session_state.user_posto = posto
                    st.session_state.login_state = "animating"
                    st.rerun()
                else:
                    st.error("Por favor, preencha todos os campos.")

    if st.session_state.login_state == "animating":
        time.sleep(0.35)
        st.session_state.login_state = "authenticated"
        st.rerun()

# ==========================================
# TELA PRINCIPAL (DASHBOARD)
# ==========================================
user_posto = st.session_state.get("user_posto", "Sistema de Fechamento")
user_nome = st.session_state.get("user_nome", "Visitante")
user_cargo = st.session_state.get("user_cargo", "Operador")

st.title(f"Fechamento Financeiro Diário - {user_posto}")
st.caption(f"Operador(a): {user_nome} ({user_cargo}) | Processamento Seguro em Memória")

col_date, col_logout = st.columns([2, 4])
with col_date:
    selected_date = st.date_input("Fechamento referente a:", value=date.today(), format="DD/MM/YYYY", disabled=not is_auth)

with col_logout:
    st.write("")
    if st.button("Trocar Usuário ou Sair", key="logout_btn", disabled=not is_auth):
        st.session_state.login_state = "pending"
        st.session_state.toast_shown = False
        st.rerun()
        
target_date_str = selected_date.strftime("%d/%m/%Y")

tab_premmia, tab_saqua, tab_pos = st.tabs(["App Premmia", "Moeda Saquá", "Maquininhas de Cartão"])

with tab_premmia:
    premmia_files = st.file_uploader("Upload Conferência Premmia", type=["xlsx", "xls", "csv", "ods"], accept_multiple_files=True, key=f"premmia_uploader_{st.session_state.uploader_key}", disabled=not is_auth)

with tab_saqua:
    saqua_files = st.file_uploader("Upload Extratos Moeda Saquá", type=["xlsx", "xls", "csv", "ods"], accept_multiple_files=True, key=f"saqua_uploader_{st.session_state.uploader_key}", disabled=not is_auth)

with tab_pos:
    st.info("Módulo em desenvolvimento. Estará disponível em breve.")
    st.file_uploader("Upload desabilitado", disabled=True, key="pos_disabled")

# PROCESSAMENTO
if (saqua_files or premmia_files) and is_auth:
    st.markdown("---")
    
    col_dash_title, col_dash_btn = st.columns([4, 1])
    with col_dash_title:
        st.header(f"Dashboard de Fechamento - {target_date_str}")
    with col_dash_btn:
        if st.button("Limpar Dashboard", use_container_width=True):
            st.session_state.uploader_key += 1
            st.rerun()
    
    try:
        res_premmia = parse_premmia(premmia_files, target_date_str) if premmia_files else None
    except Exception as e:
        st.error(f"Erro técnico no Premmia: {e}")
        res_premmia = None

    try:
        res_saqua = parse_moeda_saqua(saqua_files, target_date_str) if saqua_files else None
    except Exception as e:
        st.error(f"Erro técnico no Moeda Saquá: {e}")
        res_saqua = None

    if res_premmia is not None and res_premmia.get("total_tx", 0) == 0:
        st.warning(f"Lemos a planilha do App Premmia, mas não achamos nenhuma venda no dia {target_date_str}.")
        
    if res_saqua is not None and res_saqua.get("total_bruto", 0) == 0:
        st.warning(f"Lemos os extratos do Moeda Saquá, mas não achamos nenhuma venda no dia {target_date_str}.")

    dash_col1, dash_col2 = st.columns(2)
    show_premmia = res_premmia and res_premmia.get("total_tx", 0) > 0
    show_saqua = res_saqua and res_saqua.get("total_bruto", 0) > 0

    if show_premmia:
        cont_p = dash_col1 if show_saqua else st.container()
        with cont_p:
            st.subheader("App Premmia")
            p1, p2, p3 = st.columns(3)
            p1.metric("Recebido (APP + Pix)", format_currency(res_premmia['recebido']))
            p2.metric("Descontos", format_currency(res_premmia["descontos"]))
            p3.metric("Total Geral", format_currency(res_premmia["total_geral"]))

            df_chart_p = pd.DataFrame([{"Forma": k, "Valor": v["total"]} for k, v in res_premmia["breakdown"].items() if v["total"] > 0])
            if not df_chart_p.empty:
                fig_p = px.pie(df_chart_p, values='Valor', names='Forma', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_p.update_traces(textposition='inside', textinfo='percent+label')
                fig_p.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=280, showlegend=False)
                st.plotly_chart(fig_p, use_container_width=True)

            table_p = [{"Pagamento": f, "Qtd": i['qtd'], "Valor": format_currency(i["total"])} for f, i in res_premmia["breakdown"].items()]
            st.dataframe(pd.DataFrame(table_p), use_container_width=True, hide_index=True)

    if show_saqua:
        cont_s = dash_col2 if show_premmia else st.container()
        with cont_s:
            st.subheader("Moeda Saquá")
            s1, s2, s3 = st.columns(3)
            s1.metric("Total Bruto", format_currency(res_saqua['total_bruto']))
            s2.metric("Taxas (2%)", format_currency(res_saqua["total_taxas"]))
            s3.metric("Líquido", format_currency(res_saqua["total_liquido"]))

            df_chart_s = pd.DataFrame({"Categoria": ["Líquido Creditado", "Taxas Retidas"], "Valor": [res_saqua["total_liquido"], abs(res_saqua["total_taxas"])]})
            fig_s = px.pie(df_chart_s, values='Valor', names='Categoria', hole=0.6, color_discrete_sequence=["#10b981", "#ef4444"])
            fig_s.update_traces(textposition='inside', textinfo='percent+label')
            fig_s.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=280, showlegend=False)
            st.plotly_chart(fig_s, use_container_width=True)

            table_rows = [{"Conta": c, "Qtd": d["qtd_vendas"], "Bruto": format_currency(d["vendas_brutas"]), "Taxas": format_currency(d["taxas"]), "Líquido": format_currency(d["liquido"])} for c, d in res_saqua["contas"].items()]
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    if show_premmia or show_saqua:
        st.markdown("---")
        st.markdown("### Exportar Fechamento")
        resumo_whatsapp = generate_whatsapp_summary(target_date_str, res_premmia, res_saqua)
        st.text_area("Copiar para WhatsApp:", value=resumo_whatsapp, height=220)
        st.download_button(label="Baixar Resumo (.txt)", data=resumo_whatsapp, file_name=f"fechamento_{target_date_str.replace('/', '-')}.txt", mime="text/plain")
