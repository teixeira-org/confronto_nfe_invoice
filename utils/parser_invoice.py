import pandas as pd
import unicodedata
import re
import os

def normalizar(texto):
    """Remove acentos, caracteres especiais e normaliza texto para comparação."""
    if not isinstance(texto, str):
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8")
    texto = re.sub(r"[-/]", " ", texto)  # transforma hífen e barra em espaço
    texto = re.sub(r"[^a-z0-9 ]", "", texto)  # remove tudo exceto letras, números e espaço
    texto = re.sub(r"\s+", " ", texto)  # reduz espaços múltiplos
    return texto.strip()

def carregar_cores_validas(caminho="utils/cores_validas.txt"):
    with open(caminho, "r", encoding="utf-8") as f:
        return set(linha.strip() for linha in f if linha.strip())

CORES_VALIDAS = carregar_cores_validas(os.path.join(os.path.dirname(__file__), "cores_validas.txt"))

def detectar_cores_na_string(cor_normalizada, CORES_VALIDAS):
    """Retorna todas as cores presentes na string normalizada, na ordem que aparecem no texto."""
    cores_encontradas = []
    for cor in CORES_VALIDAS:
        if cor in cor_normalizada:
            cores_encontradas.append(cor)
    cores_encontradas = sorted(cores_encontradas, key=lambda x: cor_normalizada.find(x))
    return " ".join(cores_encontradas)

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
    total_pares = 0
    total_nota = 0.0

    for _, row in df.iterrows():
        ref = normalizar(str(row.get("ref", "")))
        ncm = normalizar(str(row.get("ncm", "")))
        cor_raw = str(row.get("cor", ""))
        cor_norm = normalizar(cor_raw)
        cor_oficial = detectar_cores_na_string(cor_norm, CORES_VALIDAS)
        cor = cor_oficial or cor_norm
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
                    "tamanho": normalizar(tamanho),
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
