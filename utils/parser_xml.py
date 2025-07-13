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

            # Robustez: funciona com ou sem "REF" no xProd
            ref, cor, tamanho = None, None, None
            match_ref = re.search(r'REF\s+([A-Za-z0-9]+)', xProd)
            match_cor_tam = re.search(r'\b([A-ZÇÃÕÉÊÍÓÚa-zçãõéêíóú]+)\s+(\d{2})\s+REF', xProd)

            if match_ref and match_cor_tam:
                ref = match_ref.group(1)
                cor = match_cor_tam.group(1)
                tamanho = match_cor_tam.group(2)
            else:
                # Novo padrão: ... REF não existe, ex: "25K10301 NATURAL 38"
                match = re.search(r'([A-Z0-9]+)\s+([A-ZÇÃÕÉÊÍÓÚa-zçãõéêíóú]+)\s+(\d{2})$', xProd)
                if match:
                    ref = match.group(1)
                    cor = match.group(2)
                    tamanho = match.group(3)

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
