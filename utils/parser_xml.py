import xml.etree.ElementTree as ET
import re
import unicodedata
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

def processar(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    ns = {"ns": "http://www.portalfiscal.inf.br/nfe"}
    itens = []
    total_pares = 0
    total_nota = 0.0

    for det in root.findall(".//ns:det", ns):
        # ⚠️ Não remova essa linha! O campo 'item' representa o número original do item da NF-e (nItem),
        # essencial para rastreabilidade do confronto e exibição amigável no frontend!
        nItem = det.attrib.get("nItem", "")
        prod = det.find("ns:prod", ns)
        if prod is not None:
            xProd = prod.findtext("ns:xProd", default="", namespaces=ns)
            NCM = prod.findtext("ns:NCM", default="", namespaces=ns)

            ref, cor, tamanho = None, None, None
            match_ref = re.search(r'REF\s+([A-Za-z0-9]+)', xProd)
            match_cor_tam = re.search(r'\b([A-ZÇÃÕÉÊÍÓÚa-zçãõéêíóú]+)\s+(\d{2})\s+REF', xProd)

            if match_ref and match_cor_tam:
                ref = match_ref.group(1)
                cor = match_cor_tam.group(1)
                tamanho = match_cor_tam.group(2)
            else:
                # Novo padrão: ... REF não existe, ex: "25K10301 NATURAL 38"
                match = re.search(r'([A-Z0-9]+)\s+([A-ZÇÃÕÉÊÍÓÚa-zçãõéêíóú\/\- ]+)\s+(\d{2})$', xProd)
                if match:
                    ref = match.group(1)
                    cor = match.group(2)
                    tamanho = match.group(3)

            ref = normalizar(ref)
            ncm = normalizar(NCM)
            cor_norm = normalizar(cor)
            cor_oficial = detectar_cores_na_string(cor_norm, CORES_VALIDAS)
            cor = cor_oficial or cor_norm
            tamanho = normalizar(tamanho)

            try:
                qCom = float(str(prod.findtext("ns:qCom", "0", namespaces=ns)).replace(",", "."))
                vUnCom = float(str(prod.findtext("ns:vUnCom", "0", namespaces=ns)).replace(",", "."))
                vProd = float(str(prod.findtext("ns:vProd", "0", namespaces=ns)).replace(",", "."))
            except:
                qCom = vUnCom = vProd = 0.0

            total_pares += qCom
            total_nota += vProd

            itens.append({
                "item": nItem,  # ⚠️ ESSENCIAL para rastreabilidade no resultado!
                "ref": ref,
                "ncm": ncm,
                "cor": cor,
                "tamanho": tamanho,
                "total pares": qCom,
                "preço unitário": vUnCom,
                "valor total": vProd,
            })

    resumo = {
        "total pares": total_pares,
        "valor total xml": round(total_nota, 2),
        "itens": len(itens)
    }
    return itens, resumo
