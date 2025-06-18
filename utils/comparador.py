import pandas as pd
import unicodedata

def normalizar(texto):
    """Remove acentos e normaliza texto para comparação."""
    if isinstance(texto, str):
        return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').strip().lower()
    return texto

def busca_flexivel(row_xml, df_invoice):
    """
    Procura linha na Invoice que tenha ref, cor e tamanho dentro do xProd do XML.
    Retorna o índice do match ou None se não achar.
    """
    ref_xml = normalizar(str(row_xml.get("ref_xml", "")))
    xProd_xml = normalizar(str(row_xml.get("xProd", "")))
    for idx, row_inv in df_invoice.iterrows():
        ref_inv = normalizar(str(row_inv.get("ref", "")))
        cor_inv = normalizar(str(row_inv.get("cor", "")))
        tam_inv = normalizar(str(row_inv.get("tamanho", "")))
        if (
            ref_inv and ref_inv in xProd_xml and
            cor_inv and cor_inv in xProd_xml and
            tam_inv and tam_inv in xProd_xml
        ):
            return idx
    return None

def confrontar(itens_xml, itens_invoice):
    if not itens_xml or not itens_invoice:
        return pd.DataFrame([{"Erro": "Itens vazios em um dos arquivos"}])

    df_xml = pd.DataFrame(itens_xml)
    df_invoice = pd.DataFrame(itens_invoice)

    # Para cada linha do XML, busca na invoice uma linha correspondente (por ref, cor, tamanho)
    invoice_idxs = []
    for idx_xml, row_xml in df_xml.iterrows():
        idx_inv = busca_flexivel(row_xml, df_invoice)
        invoice_idxs.append(idx_inv)

    df_xml["idx_invoice"] = invoice_idxs

    # Monta lista de linhas matched ou vazias, para evitar warning do concat
    linhas = []
    for idx in df_xml["idx_invoice"]:
        if pd.notnull(idx) and idx in df_invoice.index:
            linha = df_invoice.loc[idx].add_suffix("_invoice")
            linhas.append(linha)
        else:
            vazio = pd.Series({col + "_invoice": None for col in df_invoice.columns})
            linhas.append(vazio)
    dados_invoice_matched = pd.DataFrame(linhas).reset_index(drop=True)

    # Junta os dados
    df_merged = pd.concat([df_xml.reset_index(drop=True), dados_invoice_matched], axis=1)

    # Função de verificação
    def verificar_diferenca(linha, campo_xml, campo_invoice):
        val_xml = linha.get(campo_xml)
        val_inv = linha.get(campo_invoice)
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

    # Quais campos comparar
    campos_para_verificar = [
        ("total pares", "total pares_invoice"),
        ("unit price", "unit price_invoice"),
        ("valor total", "valor total_invoice"),
        ("ncm", "ncm_invoice"),
    ]

    for campo_xml, campo_invoice in campos_para_verificar:
        if campo_xml in df_merged.columns and campo_invoice in df_merged.columns:
            df_merged[f"verificação {campo_xml}"] = df_merged.apply(
                lambda row: verificar_diferenca(row, campo_xml, campo_invoice), axis=1
            )
        else:
            df_merged[f"verificação {campo_xml}"] = "⚠️ Coluna ausente"

    # xProd para exibição
    df_merged["xProd_exibicao"] = df_merged["xProd"].combine_first(df_merged.get("xProd_invoice"))

    # Seleção de colunas finais (ajuste conforme seu fluxo)
    colunas_final = [
        "nItem", "xProd_exibicao", "ref_xml", "total pares", "unit price", "valor total", "ncm",
        "ref_invoice", "cor_invoice", "tamanho_invoice", "total pares_invoice", "unit price_invoice", "valor total_invoice", "ncm_invoice",
        "verificação total pares", "verificação unit price", "verificação valor total", "verificação ncm",
    ]
    colunas_final = [col for col in colunas_final if col in df_merged.columns]

    df_final = df_merged[colunas_final].copy()
    df_final.rename(columns={"xProd_exibicao": "xProd"}, inplace=True)
    return df_final
