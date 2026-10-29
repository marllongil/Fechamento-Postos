# ⛽ Fecho Financeiro Diário

Aplicação web desenvolvida em **Python** e **Streamlit** concebida para automatizar a leitura, filtragem e conciliação de relatórios e extratos financeiros diários do **App Premmia** e da **Moeda Saquá**.

---

## 📌 Funcionalidades

- **Seleção Dinâmica por Data:** Filtro centralizado que processa estritamente as transações do dia selecionado, descartando sobras de dias posteriores.
- **Leitura do App Premmia:** 
  - Consolidação por forma de pagamento (Cartão APP, Pix, Desconto, Vale-Premmia, Pontos).
  - Cálculo automático de pagamentos recebidos, descontos e total geral.
- **Leitura da Moeda Saquá:** 
  - Reconhecimento automático de contas bancárias a partir dos extratos (ex.: Conta `00 300007785` e Conta `00 300003670`).
  - Apuração de vendas brutas, retenção de taxa (2,00%) e valor líquido creditado.
- **Suporte a Múltiplos Ficheiros:** Carregamento de até 5 folhas de cálculo por slot, suportando formatos `.csv`, `.xlsx`, `.xls` e `.ods`.
- **Privacidade e Segurança (Zero-Persistence):** 
  - Todos os ficheiros são processados estritamente na memória RAM (`BytesIO`).
  - Nenhum dado de clientes, transações ou extratos é guardado em disco ou base de dados.
- **Exportação Rápida:** Geração de resumo formatado pronto a copiar para WhatsApp e descarregamento em formato `.txt`.

---

## 🛠️ Tecnologias Utilizadas

- **[Python](https://www.python.org/)** (v3.10+)
- **[Streamlit](https://streamlit.io/)** - Interface web e dashboard reativo
- **[Pandas](https://pandas.pydata.org/)** - Tratamento e agregação de dados
- **[OpenPyXL](https://openpyxl.readthedocs.io/)** / **[Odfpy](https://github.com/eea/odfpy)** - Motores de leitura para folhas de cálculo Excel e ODS

---

## 🚀 Como Executar Localmente

### 1. Clonar o repositório
```bash
git clone [https://github.com/teu-usuario/posto-fechamento-diario.git](https://github.com/teu-usuario/posto-fechamento-diario.git)
cd posto-fechamento-diario
