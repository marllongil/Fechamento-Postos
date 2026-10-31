def format_currency(val: float) -> str:
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def generate_whatsapp_summary(data_str: str, premmia: dict, saqua: dict) -> str:
    lines = [
        f"*FECHAMENTO DIÁRIO*",
        f"*Data:* {data_str}",
        ""
    ]
    
    if premmia and premmia.get("total_tx", 0) > 0:
        lines.append("*APP PREMMIA*")
        lines.append(f"- Total Transações: {premmia['total_tx']}")
        for k, v in premmia["breakdown"].items():
            lines.append(f"  - {k} ({v['qtd']}): {format_currency(v['total'])}")
        
        lines.append(f"*RECEBIDO (Cartão APP + Pix): {format_currency(premmia['recebido'])}*")
        
        if premmia['descontos'] > 0:
            lines.append(f"  - Descontos Concedidos: {format_currency(premmia['descontos'])}")
            
        lines.append(f"Total Geral Premmia: {format_currency(premmia['total_geral'])}")
        lines.append("")
        
    if saqua and saqua.get("total_bruto", 0) > 0:
        lines.append("*MOEDA SAQUÁ*")
        for conta, dados in saqua["contas"].items():
            lines.append(f"- {conta} ({dados['qtd_vendas']} vendas):")
            lines.append(f"  - Bruto: {format_currency(dados['vendas_brutas'])}")
            lines.append(f"  - Taxas ({dados['pct_taxa']:.2f}%): {format_currency(dados['taxas'])}")
            lines.append(f"  - Líquido: {format_currency(dados['liquido'])}")
            
        lines.append(f"*TOTAL BRUTO SAQUÁ: {format_currency(saqua['total_bruto'])}*")
        lines.append(f"  - Total Taxas: {format_currency(saqua['total_taxas'])}")
        lines.append(f"Total Líquido Creditado: {format_currency(saqua['total_liquido'])}")
        lines.append("")
        
    return "\n".join(lines)
