import pandas as pd
import unicodedata

def normalizar(texto):
    """Remove acentos e normaliza texto para comparação."""
    if isinstance(texto, str):
        return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').strip().lower()
    return texto

def confrontar(itens_xml, itens_invoice):
    if not itens_xml or not itens_invoice:
        return pd.DataFrame([{"Erro": "Itens vazios em um dos arquivos"}])

    df_xml = pd.DataFrame(itens_xml)
    df_invoice = pd.DataFrame(itens_invoice)

    # Normaliza colunas para merge
    df_xml['xProd_normalizado'] = df_xml['xProd_match'].apply(normalizar)
    df_invoice['xProd_normalizado'] = df_invoice['xProd_match'].apply(normalizar)

    # Merge
    df_merged = pd.merge(
        df_xml, df_invoice,
        on="xProd_normalizado",
        suffixes=('_xml', '_invoice'),
        how='outer',
        indicator=True
    )

    # Função de verificação
    def verificar_diferenca(linha, campo):
        val_xml = linha.get(f"{campo}_xml")
        val_inv = linha.get(f"{campo}_invoice")
        if pd.isnull(val_xml) or pd.isnull(val_inv):
            return "⚠️ Ausente"
        try:
            if round(float(val_xml), 2) != round(float(val_inv), 2):
                return f"❌ {val_xml} ≠ {val_inv}"
            else:
                return "✅ OK"
        except:
            if str(val_xml).strip() != str(val_inv).strip():
                return f"❌ {val_xml} ≠ {val_inv}"
            else:
                return "✅ OK"

    # Verificações
    campos_para_verificar = ["total pares", "unit price", "valor total", "ncm"]
    for campo in campos_para_verificar:
        col_xml = f"{campo}_xml"
        col_invoice = f"{campo}_invoice"
        if col_xml in df_merged.columns and col_invoice in df_merged.columns:
            df_merged[f"verificação {campo}"] = df_merged.apply(lambda row: verificar_diferenca(row, campo), axis=1)
        else:
            df_merged[f"verificação {campo}"] = "⚠️ Coluna ausente"

    # Campo de exibição
    df_merged["xProd_exibicao"] = df_merged["xProd_xml"].combine_first(df_merged["xProd_invoice"])

    # Seleção de colunas
    colunas_final = [
        "nItem",
        "xProd_exibicao",
        "ref_xml", "total pares_xml", "unit price_xml", "valor total_xml", "ncm_xml",
        "ref",     "total pares_invoice", "unit price_invoice", "valor total_invoice", "ncm_invoice",
        "verificação total pares", "verificação unit price", "verificação valor total", "verificação ncm",
        "_merge"
    ]

    # Garantir apenas colunas existentes
    colunas_final = [col for col in colunas_final if col in df_merged.columns]

    # Resultado final
    df_final = df_merged[colunas_final].copy()
    df_final.rename(columns={
        "xProd_exibicao": "xProd",
        "_merge": "origem"
    }, inplace=True)

    return df_final
