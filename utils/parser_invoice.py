import pandas as pd

def processar(excel_file, usar_grade=False):
    try:
        df = pd.read_excel(excel_file, sheet_name="CI", header=0, dtype=str)
    except Exception as e:
        return [], {"erro": f"Erro ao ler a aba 'CI': {str(e)}"}

    # Padronizar nomes das colunas
    df.columns = [int(col) if str(col).isdigit() else str(col).strip().lower() for col in df.columns]

    # Colunas obrigatórias
    colunas_fixas = ["item", "marca", "ref", "ncm", "cor", "caixas", "total pares", "preco unit", "valor total"]
    tamanhos = list(range(20, 46))

    for col in colunas_fixas + tamanhos:
        if col not in df.columns:
            return [], {"erro": f"Coluna obrigatória ausente: {col}"}

    itens = []
    total_pares = 0
    total_nota = 0.0

    for _, row in df.iterrows():
        ref = str(row.get("ref", "")).strip()
        cor = str(row.get("cor", "")).strip()
        ncm = str(row.get("ncm", "")).strip()

        preco_unit_raw = str(row.get("preco unit", "0")).strip()
        preco_unit_str = preco_unit_raw.replace(",", ".")
        try:
            preco_unit_float = float(preco_unit_str)
        except:
            preco_unit_float = 0.0

        caixas_raw = str(row.get("caixas", "1")).strip()
        caixas = int(caixas_raw) if caixas_raw.isdigit() else 1  # padrão 1

        total_item = 0.0

        for tamanho in tamanhos:
            qtd_str = str(row.get(tamanho, "0")).strip()
            qtd = int(qtd_str) if qtd_str.isdigit() else 0

            if qtd > 0:
                if usar_grade:
                    quantidade_final = qtd * caixas
                else:
                    quantidade_final = qtd

                valor_total = round(preco_unit_float * quantidade_final, 2)

                itens.append({
                    "ref": ref,
                    "cor": cor,
                    "tamanho": str(tamanho),
                    "ncm": ncm,
                    "quantidade": quantidade_final,
                    "preco_unit": preco_unit_float,
                    "valor_total": valor_total,
                    "xProd": f"{ref} - {cor} - {tamanho}",
                    "xProd_match": f"{ref} - {cor} - {tamanho}",
                    "total pares": quantidade_final,
                    "unit price": preco_unit_float,  # manter por compatibilidade
                    "valor total": valor_total,
                })
                total_pares += quantidade_final
                total_item += valor_total
        total_nota += total_item

    return itens, {
        "total pares": total_pares,
        "valor total nota": round(total_nota, 2),
        "usou_grade": usar_grade
    }
