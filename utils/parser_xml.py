import xml.etree.ElementTree as ET
import re

def processar(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    ns = {"ns": "http://www.portalfiscal.inf.br/nfe"}
    itens = []
    total_pares = 0
    total_nota = 0.0

    for det in root.findall(".//ns:det", ns):
        nItem = det.attrib.get("nItem", "")
        prod = det.find("ns:prod", ns)
        if prod is not None:
            xProd = prod.findtext("ns:xProd", default="", namespaces=ns)
            NCM = prod.findtext("ns:NCM", default="", namespaces=ns)

            # Extrair ref base (apenas letras/números antes do primeiro ponto)
            ref = None
            match_ref = re.search(r'REF\s+([A-Za-z0-9]+)', xProd)
            if match_ref:
                ref = match_ref.group(1)

            # Extrair cor e tamanho (antes de REF)
            cor, tamanho = None, None
            match_cor_tam = re.search(r'\b([A-ZÇÃÕÉÊÍÓÚa-zçãõéêíóú]+)\s+(\d{2})\s+REF', xProd)
            if match_cor_tam:
                cor = match_cor_tam.group(1)
                tamanho = match_cor_tam.group(2)

            try:
                qCom = float(str(prod.findtext("ns:qCom", "0", namespaces=ns)).replace(",", "."))
                vUnCom = float(str(prod.findtext("ns:vUnCom", "0", namespaces=ns)).replace(",", "."))
                vProd = float(str(prod.findtext("ns:vProd", "0", namespaces=ns)).replace(",", "."))
            except:
                qCom = vUnCom = vProd = 0.0

            total_pares += qCom
            total_nota += vProd

            itens.append({
                "item": nItem,
                "ref": ref,
                "ncm": NCM,
                "cor": cor,
                "tamanho": tamanho,
                "total pares": qCom,
                "preço unitário": vUnCom,
                "valor total": vProd,
            })

    resumo = {
        "itens": len(itens),
        "total pares": total_pares,
        "valor total xml": round(total_nota, 2)
    }
    return itens, resumo
