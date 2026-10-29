import io
import pandas as pd

def load_spreadsheet_in_memory(uploaded_file) -> pd.DataFrame:
    """Lê arquivos CSV, XLSX, XLS e ODS estritamente na memória RAM."""
    filename = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()
    
    if filename.endswith(".csv"):
        for enc in ["utf-8-sig", "latin1", "cp1252", "utf-8"]:
            try:
                uploaded_file.seek(0)
                return pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python", encoding=enc)
            except Exception:
                continue
        uploaded_file.seek(0)
        return pd.read_csv(io.BytesIO(file_bytes), encoding="latin1")
    elif filename.endswith((".xlsx", ".xls", ".ods")):
        return pd.read_excel(io.BytesIO(file_bytes))
    else:
        try:
            return pd.read_excel(io.BytesIO(file_bytes))
        except Exception:
            return pd.read_csv(io.BytesIO(file_bytes), encoding="latin1")


def clean_currency_series(series: pd.Series) -> pd.Series:
    """Converte valores monetários para float com suporte a formato brasileiro e Arrow."""
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").fillna(0.0).astype(float)
    
    # Tratamento para texto com vírgula (R$ 1.250,00 -> 1250.00)
    str_s = series.astype(str).str.strip().str.replace("R$", "", regex=False).str.strip()
    has_comma = str_s.str.contains(",", regex=False)
    
    cleaned = str_s.copy()
    cleaned[has_comma] = str_s[has_comma].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    
    return pd.to_numeric(cleaned, errors="coerce").fillna(0.0).astype(float)


def parse_premmia(uploaded_files, target_date_str: str) -> dict:
    """Processa as planilhas do App Premmia para a data especificada (DD/MM/AAAA)."""
    consolidated_rows = []
    
    for f in uploaded_files:
        df = load_spreadsheet_in_memory(f)
        
        date_col = next((c for c in df.columns if "data" in str(c).lower()), None)
        val_col = next((c for c in df.columns if "valor" in str(c).lower()), None)
        pay_col = next((c for c in df.columns if "forma" in str(c).lower() or "pagamento" in str(c).lower()), None)
        
        if not (date_col and val_col and pay_col):
            continue
            
        df["_dt"] = pd.to_datetime(df[date_col], format="mixed", dayfirst=True, errors="coerce")
        df_filtered = df[df["_dt"].dt.strftime("%d/%m/%Y") == target_date_str].copy()
        
        if df_filtered.empty:
            continue

        df_filtered["_val"] = clean_currency_series(df_filtered[val_col])
            
        for _, row in df_filtered.iterrows():
            consolidated_rows.append({
                "cliente": str(row.get("Nome", "Não informado")),
                "forma_pagamento": str(row[pay_col]).strip(),
                "valor": row["_val"]
            })
            
    if not consolidated_rows:
        return {"total_tx": 0, "breakdown": {}, "recebido": 0.0, "descontos": 0.0, "pontos": 0.0, "vales": 0.0, "total_geral": 0.0}

    df_res = pd.DataFrame(consolidated_rows)
    
    breakdown = {}
    for forma, grp in df_res.groupby("forma_pagamento"):
        breakdown[forma] = {
            "qtd": len(grp),
            "total": grp["valor"].sum()
        }
        
    recebido = df_res[df_res["forma_pagamento"].str.upper().isin(["CARTÃO APP", "CARTAO APP", "PIX"])]["valor"].sum()
    descontos = df_res[df_res["forma_pagamento"].str.upper() == "DESCONTO"]["valor"].sum()
    pontos = df_res[df_res["forma_pagamento"].str.upper() == "PONTOS"]["valor"].sum()
    vales = df_res[df_res["forma_pagamento"].str.upper() == "VALE-PREMMIA"]["valor"].sum()
    total_geral = df_res["valor"].sum()
    
    return {
        "total_tx": len(df_res),
        "breakdown": breakdown,
        "recebido": recebido,
        "descontos": descontos,
        "pontos": pontos,
        "vales": vales,
        "total_geral": total_geral
    }


def parse_moeda_saqua(uploaded_files, target_date_str: str) -> dict:
    """Processa as contas do Moeda Saquá identificando a conta e calculando taxas e líquidos."""
    contas_data = {}
    
    for f in uploaded_files:
        df = load_spreadsheet_in_memory(f)
        
        mov_col = next((c for c in df.columns if str(c).strip().upper() == "MOVIMENTO"), None)
        date_col = next((c for c in df.columns if "DATA" in str(c).strip().upper()), None)
        val_col = next((c for c in df.columns if str(c).strip().upper() == "VALOR"), None)
        
        acc_col = next((c for c in df.columns if str(c).strip().upper() == "CONTA 1"), None)
        if not acc_col:
            acc_col = next((c for c in df.columns if "CONTA" in str(c).strip().upper() and "NOME" not in str(c).strip().upper()), None)
        
        if not (mov_col and date_col and val_col):
            continue
            
        conta_num = "Conta Desconhecida"
        if acc_col and not df[acc_col].dropna().empty:
            conta_num = f"Conta {str(df[acc_col].dropna().iloc[0]).strip()}"
        else:
            conta_num = f.name
            
        df["_dt"] = pd.to_datetime(df[date_col], format="mixed", dayfirst=True, errors="coerce")
        df_filtered = df[df["_dt"].dt.strftime("%d/%m/%Y") == target_date_str].copy()
        
        if df_filtered.empty:
            continue

        df_filtered["_val"] = clean_currency_series(df_filtered[val_col])
            
        creditos = df_filtered[df_filtered[mov_col] == "C"]["_val"].sum()
        qtd_creditos = len(df_filtered[df_filtered[mov_col] == "C"])
        taxas = df_filtered[df_filtered[mov_col] == "T"]["_val"].sum()
        
        liquido = creditos + taxas
        pct_taxa = (abs(taxas) / creditos * 100) if creditos > 0 else 2.00
        
        if conta_num not in contas_data:
            contas_data[conta_num] = {
                "vendas_brutas": creditos,
                "qtd_vendas": qtd_creditos,
                "taxas": taxas,
                "pct_taxa": pct_taxa,
                "liquido": liquido
            }
        else:
            contas_data[conta_num]["vendas_brutas"] += creditos
            contas_data[conta_num]["qtd_vendas"] += qtd_creditos
            contas_data[conta_num]["taxas"] += taxas
            contas_data[conta_num]["liquido"] += liquido
            
    total_bruto = sum(c["vendas_brutas"] for c in contas_data.values())
    total_taxas = sum(c["taxas"] for c in contas_data.values())
    total_liquido = sum(c["liquido"] for c in contas_data.values())
    pct_total = (abs(total_taxas) / total_bruto * 100) if total_bruto > 0 else 0.0
    
    return {
        "contas": contas_data,
        "total_bruto": total_bruto,
        "total_taxas": total_taxas,
        "pct_taxa": pct_total,
        "total_liquido": total_liquido
    }
