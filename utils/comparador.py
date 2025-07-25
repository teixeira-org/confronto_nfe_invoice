import pandas as pd
import unicodedata
import re
import os

def normalizar(texto):
    if not isinstance(texto, str):
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8")
    texto = re.sub(r"[-/,.]", " ", texto)
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

def preparar_df(itens, origem):
    df = pd.DataFrame(itens)
    if df.empty:
        return df

    # Ajusta os campos base para comparação
    if origem == "xml":
        df['ref_base'] = df['ref xml (base)']
        df['cor_id'] = df['cor xml (base)']
    else:
        df['ref_base'] = df['ref invoice (base)']
        df['cor_id'] = df['cor invoice (base)']

    df['ncm_base'] = df[df.columns[df.columns.str.contains('ncm')][0]]
    df['tamanho_base'] = df['tamanho']
    return df

def agrupar_df(df):
    campos_agrupamento = ['ref_base', 'ncm_base', 'cor_id', 'tamanho_base']
    for col in df.columns:
        if col not in campos_agrupamento:
            df[col] = df[col].apply(lambda x: x[0] if isinstance(x, list) else x)
    return df.groupby(campos_agrupamento, as_index=False).agg(lambda x: x.iloc[0] if len(x) > 0 else "")

def verif(a, b):
    if isinstance(a, list):
        a = a[0] if a else ""
    if isinstance(b, list):
        b = b[0] if b else ""
    if pd.isnull(a) and not pd.isnull(b):
        return f"❌ Ausente no XML"
    if pd.isnull(b) and not pd.isnull(a):
        return f"❌ Ausente na Invoice"
    try:
        af, bf = str(a).replace(",", "."), str(b).replace(",", ".")
        return "✅ OK" if pd.notnull(a) and pd.notnull(b) and (float(af) == float(bf)) else f"❌ {a} ≠ {b}"
    except Exception:
        return f"❌ {a} ≠ {b}"

def confrontar(itens_xml, itens_invoice):
    df_xml = preparar_df(itens_xml, "xml")
    df_invoice = preparar_df(itens_invoice, "invoice")

    df_xml_grouped = agrupar_df(df_xml)
    df_invoice_grouped = agrupar_df(df_invoice)

    df_merge = pd.merge(
        df_xml_grouped, df_invoice_grouped,
        on=['ref_base', 'ncm_base', 'cor_id', 'tamanho_base'],
        how='outer',
        suffixes=('_xml', '_invoice'),
        indicator=True
    )

    # ⚠️ ORDEM FIXA DAS COLUNAS NO RESULTADO: NÃO ALTERAR SEM REVISAR TODA A LÓGICA DE EXIBIÇÃO!
    # num item xml | ref xml | ref invoice | verificação | ncm xml | ncm invoice | verificação | cor xml | cor invoice | verificação | total pares xml | total pares invoice | verificação | preco unit xml | preco unit invoice | verificação | valor total xml | valor total invoice | verificação

    resultado = pd.DataFrame({
        "num item xml": df_merge.get("num item xml", pd.Series([""] * len(df_merge))),
        "ref xml": df_merge.get("ref xml (completa)", pd.Series([""] * len(df_merge))),
        "ref invoice": df_merge.get("ref invoice (completa)", pd.Series([""] * len(df_merge))),
        "verificação ref": df_merge.apply(lambda row: "✅ OK" if row.get("ref xml (base)") == row.get("ref invoice (base)") else f"❌ {row.get('ref xml (base)')} ≠ {row.get('ref invoice (base)')}", axis=1),
        "ncm xml": df_merge.get("ncm xml", pd.Series([""] * len(df_merge))),
        "ncm invoice": df_merge.get("ncm invoice", pd.Series([""] * len(df_merge))),
        "verificação ncm": df_merge.apply(lambda row: "✅ OK" if str(row.get("ncm xml")) == str(row.get("ncm invoice")) else f"❌ {row.get('ncm xml')} ≠ {row.get('ncm invoice')}", axis=1),
        "cor xml (original)": df_merge.get("cor xml (original)", pd.Series([""] * len(df_merge))),
        "cor xml (base)": df_merge.get("cor xml (base)", pd.Series([""] * len(df_merge))),
        "cor invoice (original)": df_merge.get("cor invoice (original)", pd.Series([""] * len(df_merge))),
        "cor invoice (base)": df_merge.get("cor invoice (base)", pd.Series([""] * len(df_merge))),
        "verificação cor": df_merge.apply(lambda row: "✅ OK" if str(row.get("cor xml (base)")) == str(row.get("cor invoice (base)")) and str(row.get("cor xml (base)")) != "" else f"❌ {row.get('cor xml (base)')} ≠ {row.get('cor invoice (base)')}", axis=1),
        "total pares xml": df_merge.get("total pares xml", pd.Series([""] * len(df_merge))),
        "total pares invoice": df_merge.get("total pares invoice", pd.Series([""] * len(df_merge))),
        "verificação total pares": df_merge.apply(lambda row: verif(row.get("total pares xml"), row.get("total pares invoice")), axis=1),
        "preco unit xml": df_merge.get("preco unit xml", pd.Series([""] * len(df_merge))),
        "preco unit invoice": df_merge.get("preco unit invoice", pd.Series([""] * len(df_merge))),
        "verificação preco unit": df_merge.apply(lambda row: verif(row.get("preco unit xml"), row.get("preco unit invoice")), axis=1),
        "valor total xml": df_merge.get("valor total xml", pd.Series([""] * len(df_merge))),
        "valor total invoice": df_merge.get("valor total invoice", pd.Series([""] * len(df_merge))),
        "verificação valor total": df_merge.apply(lambda row: verif(row.get("valor total xml"), row.get("valor total invoice")), axis=1),
    })

    try:
        resultado["num item xml"] = resultado["num item xml"].astype(int)
        resultado = resultado.sort_values("num item xml")
    except Exception:
        pass

    return resultado.reset_index(drop=True)
