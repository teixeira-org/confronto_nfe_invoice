import pandas as pd

def processar(excel_file, usar_grade=False):
    try:
        df = pd.read_excel(excel_file, sheet_name="CI", header=0, dtype=str)
    except Exception as e:
        return [], {"erro": f"Erro ao ler a aba 'CI': {str(e)}"}

    # Padronizar nomes das colunas
    df.columns = [str(col).strip().lower() for col in df.columns]

    tamanhos = [str(i) for i in range(20, 46)]  # 20 até 45

    colunas_fixas = ["item", "marca", "ref", "ncm", "cor", "caixas", "total pares", "preco unit", "valor total"]
    for col in colunas_fixas + tamanhos:
        if col not in df.columns:
            return [], {"erro": f"Coluna obrigatória ausente: {col}"}

    itens = []
    total_pares = 0
    total_nota = 0.0

    for _, row in df.iterrows():
        marca = str(row.get("marca", "")).strip()
        ref = str(row.get("ref", "")).strip()
        ncm = str(row.get("ncm", "")).strip()
        cor = str(row.get("cor", "")).strip()
        if "-" in cor:
          cor = cor.split("-", 1)[1].strip()

        preco_unit_raw = str(row.get("preco unit", "0")).replace(",", ".").strip()
        preco_unit = float(preco_unit_raw) if preco_unit_raw.replace('.', '', 1).isdigit() else 0.0
        caixas_raw = str(row.get("caixas", "1")).strip()
        caixas = int(caixas_raw) if caixas_raw.isdigit() else 1

        for tamanho in tamanhos:
            qtd_str = str(row.get(tamanho, "0")).strip()
            qtd = int(qtd_str) if qtd_str.isdigit() else 0
            if qtd > 0:
                if usar_grade:
                    quantidade_final = qtd * caixas
                else:
                    quantidade_final = qtd
                valor_total = round(preco_unit * quantidade_final, 2)
                itens.append({
                    "ref": ref,
                    "ncm": ncm,
                    "cor": cor,
                    "tamanho": tamanho,
                    "total pares": quantidade_final,
                    "preço unitário": preco_unit,
                    "valor total": valor_total,
                })

                total_pares += quantidade_final
                total_nota += valor_total

    return itens, {
        "total pares": total_pares,
        "valor total nota": round(total_nota, 2),
        "usou_grade": usar_grade
    }
