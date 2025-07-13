import pandas as pd
import unicodedata

def normalizar(texto):
    """Remove acentos e normaliza texto para comparação (case-insensitive)."""
    if isinstance(texto, str):
        return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').strip().lower()
    return texto

def buscar_item(row_invoice, df_xml):
    """Busca exata usando ref, ncm, cor, tamanho (SEM marca)."""
    for idx, row_xml in df_xml.iterrows():
        if (
            normalizar(row_invoice.get("ref", "")) == normalizar(row_xml.get("ref", "")) and
            normalizar(row_invoice.get("ncm", "")) == normalizar(row_xml.get("ncm", "")) and
            normalizar(row_invoice.get("cor", "")) == normalizar(row_xml.get("cor", "")) and
            normalizar(str(row_invoice.get("tamanho", ""))) == normalizar(str(row_xml.get("tamanho", "")))
        ):
            return idx
    return None

def confrontar(itens_xml, itens_invoice):
    if not itens_xml or not itens_invoice:
        return pd.DataFrame([{"Erro": "Itens vazios em um dos arquivos"}])

    df_xml = pd.DataFrame(itens_xml)
    df_invoice = pd.DataFrame(itens_invoice)

    # Realiza o match dos itens
    xml_idxs = []
    for _, row_inv in df_invoice.iterrows():
        idx_xml = buscar_item(row_inv, df_xml)
        xml_idxs.append(idx_xml)

    df_invoice["idx_xml"] = xml_idxs

    linhas = []
    for idx in df_invoice["idx_xml"]:
        if pd.notnull(idx) and idx in df_xml.index:
            linha = df_xml.loc[idx].add_suffix("_xml")
            linhas.append(linha)
        else:
            vazio = pd.Series({col + "_xml": None for col in df_xml.columns})
            linhas.append(vazio)
    dados_xml_matched = pd.DataFrame(linhas).reset_index(drop=True)

    df_merged = pd.concat([df_invoice.reset_index(drop=True), dados_xml_matched], axis=1)

    # Checagem dos campos - NOMES EXATOS
    campos_para_verificar = [
        ("total pares", "total pares_xml"),
        ("preço unitário", "preço unitário_xml"),
        ("valor total", "valor total_xml"),
        ("ncm", "ncm_xml"),
    ]

    def verificar_diferenca(linha, campo_invoice, campo_xml):
        val_inv = linha.get(campo_invoice)
        val_xml = linha.get(campo_xml)
        if pd.isnull(val_inv) or pd.isnull(val_xml):
            return "⚠️ Ausente"
        try:
            if round(float(val_inv), 2) != round(float(val_xml), 2):
                return f"❌ {val_inv} ≠ {val_xml}"
            else:
                return "✅ OK"
        except:
            if str(val_inv).strip() != str(val_xml).strip():
                return f"❌ {val_inv} ≠ {val_xml}"
            else:
                return "✅ OK"

    # Geração das colunas de verificação
    for campo_inv, campo_xml in campos_para_verificar:
        col_name = f"verificação {campo_inv}"
        if campo_inv in df_merged.columns and campo_xml in df_merged.columns:
            df_merged[col_name] = df_merged.apply(
                lambda row: verificar_diferenca(row, campo_inv, campo_xml), axis=1
            )
        else:
            df_merged[col_name] = "⚠️ Coluna ausente"

    # Seleção das colunas finais — todos os nomes alinhados
    colunas_final = [
        "item", "ref", "ncm", "cor", "tamanho", "total pares", "preço unitário", "valor total",
        "total pares_xml", "preço unitário_xml", "valor total_xml", "ncm_xml",
        "verificação total pares", "verificação preço unitário", "verificação valor total", "verificação ncm",
    ]
    colunas_final = [col for col in colunas_final if col in df_merged.columns]

    return df_merged[colunas_final].copy()

