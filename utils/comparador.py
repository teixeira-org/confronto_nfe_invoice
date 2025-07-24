import pandas as pd
import unicodedata
import re
import os

def normalizar(texto):
    if not isinstance(texto, str):
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8")
    texto = re.sub(r"[-/]", " ", texto)
    texto = re.sub(r"[^a-z0-9 ]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def carregar_cores_validas(caminho="utils/cores_validas.txt"):
    with open(caminho, "r", encoding="utf-8") as f:
        return set(linha.strip() for linha in f if linha.strip())

CORES_VALIDAS = carregar_cores_validas(os.path.join(os.path.dirname(__file__), "cores_validas.txt"))

def detectar_cores_na_string(cor_normalizada, CORES_VALIDAS):
    cores_encontradas = []
    for cor in CORES_VALIDAS:
        if cor in cor_normalizada:
            cores_encontradas.append(cor)
    cores_encontradas = sorted(cores_encontradas, key=lambda x: cor_normalizada.find(x))
    return " ".join(cores_encontradas)

def agrupar_itens(df, lado="xml"):
    """Agrupa por ref, ncm, cor, tamanho e, se for do XML, mantém o item/nItem para rastreio."""
    if df.empty:
        return df
    agrupa = ["ref", "ncm", "cor", "tamanho"]
    if lado == "xml" and "item" in df.columns:
        df["item"] = df["item"].astype(str)
        agrupado = df.groupby(agrupa, as_index=False).agg({
            "item": "first",
            "total pares": "sum",
            "preço unitário": "mean",
            "valor total": "sum",
        })
    else:
        agrupado = df.groupby(agrupa, as_index=False).agg({
            "total pares": "sum",
            "preço unitário": "mean",
            "valor total": "sum",
        })
    return agrupado

def preparar_df(itens, lado="xml"):
    df = pd.DataFrame(itens)
    for col in ["ref", "ncm", "cor", "tamanho"]:
        if col in df.columns:
            df[col] = df[col].apply(normalizar)
            if col == "cor":
                df[col] = df[col].apply(lambda c: detectar_cores_na_string(c, CORES_VALIDAS) or c)
        else:
            df[col] = ""
    return agrupar_itens(df, lado=lado)

def confrontar(itens_xml, itens_invoice):
    df_xml = preparar_df(itens_xml, lado="xml")
    df_invoice = preparar_df(itens_invoice, lado="invoice")

    merge_cols = ["ref", "ncm", "cor", "tamanho"]
    df_merge = pd.merge(
        df_xml, df_invoice,
        on=merge_cols,
        how="outer",
        suffixes=('_xml', '_invoice'),
        indicator=True
    )

    if "item" not in df_merge.columns:
        df_merge["item"] = ""

    def verif(val_xml, val_inv):
        if pd.isnull(val_xml) and not pd.isnull(val_inv):
            return "Ausente"
        if pd.isnull(val_inv) and not pd.isnull(val_xml):
            return "Ausente"
        try:
            return "✅ OK" if round(float(val_xml), 2) == round(float(val_inv), 2) else f"❌ {val_xml} ≠ {val_inv}"
        except:
            return f"❌ {val_xml} ≠ {val_inv}"

    df_merge["verificação total pares"] = df_merge.apply(
        lambda row: verif(row.get("total pares_xml"), row.get("total pares_invoice")), axis=1)
    df_merge["verificação preço unitário"] = df_merge.apply(
        lambda row: verif(row.get("preço unitário_xml"), row.get("preço unitário_invoice")), axis=1)
    df_merge["verificação valor total"] = df_merge.apply(
        lambda row: verif(row.get("valor total_xml"), row.get("valor total_invoice")), axis=1)

    df_merge = df_merge.rename(columns={
        "ref_xml": "ref xml", "ref_invoice": "ref invoice",
        "ncm_xml": "ncm xml", "ncm_invoice": "ncm invoice",
        "cor_xml": "cor xml", "cor_invoice": "cor invoice",
        "total pares_xml": "total pares xml", "total pares_invoice": "total pares invoice",
        "preço unitário_xml": "preço unitário xml", "preço unitário_invoice": "preço unitário invoice",
        "valor total_xml": "valor total xml", "valor total_invoice": "valor total invoice",
        "item": "item"
    })

    colunas_final = [
        "item", "ref xml", "ref invoice", "ncm xml", "ncm invoice", "cor xml", "cor invoice",
        "tamanho", "total pares xml", "total pares invoice",
        "preço unitário xml", "preço unitário invoice",
        "valor total xml", "valor total invoice",
        "verificação total pares", "verificação preço unitário", "verificação valor total"
    ]
    colunas_final = [c for c in colunas_final if c in df_merge.columns]

    try:
        df_merge["item_ord"] = df_merge["item"].astype(int)
        df_merge = df_merge.sort_values("item_ord")
        df_merge = df_merge.drop(columns=["item_ord"])
    except Exception:
        pass

    return df_merge[colunas_final].copy()
