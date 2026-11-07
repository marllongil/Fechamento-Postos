def format_currency(val: float) -> str:
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def generate_whatsapp_summary(data_str: str, premmia: dict, saqua: dict, posto: str, operador: str, cargo: str) -> str:
    lines = [
        f"*FECHAMENTO - {posto.upper()}*",
        f"Data: {data_str}",
        ""
    ]
    
    if premmia and premmia.get("total_tx", 0) > 0:
        lines.append("*APP PREMMIA*")
        bruto_p = premmia.get('total_geral', 0.0)
        liquido_p = premmia.get('recebido', 0.0)
        deducoes_p = bruto_p - liquido_p
        
        lines.append(f"Total Bruto: {format_currency(bruto_p)}")
        lines.append(f"Taxas e Descontos: {format_currency(deducoes_p)}")
        lines.append(f"Total Líquido: {format_currency(liquido_p)}")
        lines.append("")
        
    if saqua and saqua.get("total_bruto", 0) > 0:
        lines.append("*MOEDA SAQUÁ*")
        bruto_s = saqua.get('total_bruto', 0.0)
        taxas_s = abs(saqua.get('total_taxas', 0.0))
        liquido_s = saqua.get('total_liquido', 0.0)
        pct_s = saqua.get('pct_taxa', 0.0)
        
        lines.append(f"Total Bruto: {format_currency(bruto_s)}")
        lines.append(f"Taxas e Descontos ({pct_s:.2f}%): {format_currency(taxas_s)}")
        lines.append(f"Total Líquido: {format_currency(liquido_s)}")
        lines.append("")
        
    lines.append(f"Relatório gerado por: {operador} / {cargo}")
        
    return "\n".join(lines)
