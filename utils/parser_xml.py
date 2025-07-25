import xml.etree.ElementTree as ET
import re
import unicodedata
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

def extrair_ref_cprod(cprod):
    ref_completa = cprod
    ref_base = cprod.split(".", 1)[0] if "." in cprod else cprod
    return ref_completa, ref_base

def processar(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    ns = {"ns": "http://www.portalfiscal.inf.br/nfe"}
    itens = []
    total_pares = Decimal("0.0")
    total_nota = Decimal("0.0")

    for det in root.findall(".//ns:det", ns):
        nItem = det.attrib.get("nItem", "")
        prod = det.find("ns:prod", ns)
        if prod is not None:
            cProd = prod.findtext("ns:cProd", default="", namespaces=ns)
            ref_completa, ref_base = extrair_ref_cprod(cProd)
            NCM = prod.findtext("ns:NCM", default="", namespaces=ns)
            xProd = prod.findtext("ns:xProd", default="", namespaces=ns)

            # Cor: extraída do xProd (campo original e base do dicionário)
            cor_original = xProd
            cor_base = detectar_cores_na_string(xProd, CORES_VALIDAS)

            # Tamanho: última sequência de dois dígitos no cProd
            tamanho = ""
            match_tam = re.search(r"\.(\d{2,})$", cProd)
            if match_tam:
                tamanho = match_tam.group(1)

            try:
                qCom = Decimal(str(prod.findtext("ns:qCom", "0", namespaces=ns)).replace(",", "."))
                vUnCom = Decimal(str(prod.findtext("ns:vUnCom", "0", namespaces=ns)).replace(",", "."))
                vProd = Decimal(str(prod.findtext("ns:vProd", "0", namespaces=ns)).replace(",", "."))
            except Exception:
                qCom = vUnCom = vProd = Decimal("0.0")

            total_pares += qCom
            total_nota += vProd

            itens.append({
                "num item xml": nItem,
                "ref xml (completa)": ref_completa,        # exibição
                "ref xml (base)": ref_base,                # para match
                "ncm xml": NCM,
                "cor xml (original)": cor_original,        # exibição (texto do xProd)
                "cor xml (base)": cor_base,                # para match
                "tamanho": tamanho,
                "total pares xml": f"{qCom:.10f}".rstrip("0").rstrip("."),
                "preco unit xml": f"{vUnCom:.10f}".rstrip("0").rstrip("."),
                "valor total xml": f"{vProd:.10f}".rstrip("0").rstrip("."),
            })

    return itens, {
        "total pares": float(total_pares),
        "valor total xml": float(total_nota),
        "itens": len(itens)
    }
