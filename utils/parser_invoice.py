import pandas as pd
import unicodedata
import re
import os
from decimal import Decimal

def normalizar(texto):
    if not isinstance(texto, str):
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8")
    texto = re.sub(r"[-/,]", " ", texto)
    texto = re.sub(r"[^a-z0-9 ]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def carregar_cores_validas(caminho="utils/cores_validas.txt"):
    with open(caminho, "r", encoding="utf-8") as f:
        return set(linha.strip() for linha in f if linha.strip())

CORES_VALIDAS = carregar_cores_validas(os.path.join(os.path.dirname(__file__), "cores_validas.txt"))

def detectar_cores_na_string(texto, CORES_VALIDAS):
    texto_norm = normalizar(texto)
    cores_ordenadas = sorted(CORES_VALIDAS, key=lambda x: -len(x))
    cores_encontradas = []
    texto_work = f" {texto_norm} "
    for cor in cores_ordenadas:
        cor_espaco = f" {cor} "
        if cor_espaco in texto_work:
            cores_encontradas.append(cor)
            texto_work = texto_work.replace(cor_espaco, " ")
    return " ".join(cores_encontradas)

def extrair_ref_invoice(ref_invoice):
    ref_completa = ref_invoice
    ref_base = ref_invoice.split(".", 1)[0] if "." in ref_invoice else ref_invoice
    return ref_completa, ref_base

def processar(excel_file, usar_grade=False):
    try:
        df = pd.read_excel(excel_file, sheet_name="CI", header=0, dtype=str)
    except Exception as e:
        return [], {"erro": f"Erro ao ler a aba 'CI': {str(e)}"}

    df.columns = [str(col).strip().lower() for col in df.columns]
    tamanhos = [str(i) for i in range(20, 46)]  # 20 até 45

    colunas_fixas = ["item", "marca", "ref", "ncm", "cor", "caixas", "total pares", "preco unit", "valor total"]
    for col in colunas_fixas + tamanhos:
        if col not in df.columns:
            return [], {"erro": f"Coluna obrigatória ausente: {col}"}

    itens = []
    total_pares = Decimal("0.0")
    total_nota = Decimal("0.0")

    for _, row in df.iterrows():
        ref_raw = str(row.get("ref", ""))
        ref_completa, ref_base = extrair_ref_invoice(ref_raw)
        ncm = str(row.get("ncm", ""))
        marca = str(row.get("marca", ""))
        cor_original = str(row.get("cor", ""))
        cor_base = detectar_cores_na_string(cor_original, CORES_VALIDAS)
        preco_unit_raw = str(row.get("preco unit", "0")).replace(",", ".").strip()
        try:
            preco_unit = Decimal(preco_unit_raw)
        except Exception:
            preco_unit = Decimal("0.0")
        caixas_raw = str(row.get("caixas", "1")).strip()
        caixas = int(caixas_raw) if caixas_raw.isdigit() else 1

        for tamanho in tamanhos:
            qtd_str = str(row.get(tamanho, "0")).strip()
            qtd = int(qtd_str) if qtd_str.isdigit() else 0
            if qtd > 0:
                quantidade_final = qtd * caixas if usar_grade else qtd
                valor_total = preco_unit * Decimal(quantidade_final)
                itens.append({
                    "marca": marca,
                    "ref invoice (completa)": ref_completa,        # exibição
                    "ref invoice (base)": ref_base,                # para match
                    "ncm invoice": ncm,
                    "cor invoice (original)": cor_original,        # exibição
                    "cor invoice (base)": cor_base,                # para match
                    "tamanho": tamanho,
                    "total pares invoice": float(quantidade_final),
                    "preco unit invoice": f"{preco_unit:.10f}".rstrip("0").rstrip("."),
                    "valor total invoice": float(valor_total),
                })
                total_pares += Decimal(str(quantidade_final))
                total_nota += valor_total

    # --- Agrupamento correto ---
    df_itens = pd.DataFrame(itens)
    if not df_itens.empty:
        campos_agrupamento = ["marca", "ref invoice (base)", "ncm invoice", "cor invoice (base)", "tamanho"]
        campos_soma = ["total pares invoice", "valor total invoice"]
        campos_primeiro = ["ref invoice (completa)", "cor invoice (original)", "preco unit invoice"]
        agg_dict = {col: "first" for col in campos_primeiro}
        agg_dict.update({col: "sum" for col in campos_soma})
        grouped = df_itens.groupby(campos_agrupamento, as_index=False).agg(agg_dict)
        # Formatar soma como string com até 10 casas decimais
        for col in campos_soma:
            grouped[col] = grouped[col].apply(lambda v: f"{v:.10f}".rstrip("0").rstrip("."))
        #print("Agrupamento da Invoice (debug):")
        #print(grouped)
        itens = grouped.to_dict("records")

    return itens, {
        "total pares": float(total_pares),
        "valor total nota": float(total_nota),
        "usou_grade": usar_grade
    }
