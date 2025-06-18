# 🧾 Confronto XML x Invoice

Este projeto realiza a confrontação detalhada entre arquivos XML de NF-e de exportação e planilhas no formato "Invoice" (aba CI), extraindo, comparando e destacando divergências item a item com base em campos críticos como `xProd`, `quantidade`, `valor unitário` e `valor total`.

## 🚀 Funcionalidades

- Importação de múltiplos XMLs e planilhas XLSX
- Extração inteligente com reconstrução de `xProd`
- Comparação baseada em `xProd` (normalizado)
- Controle total de divergências:
  - Diferenças de quantidade
  - Diferenças de valor unitário e total
  - Itens ausentes em uma das fontes
- Exibição do número original da linha no XML (`nItem`)
- Exportação dos erros em Excel
- Botão para reiniciar nova análise sem recarregar a página

## 🧰 Tecnologias

- Python 3.10+ (recomendado)
- Streamlit (interface web)
- Pandas (manipulação de dados)
- OpenPyXL (para exportar Excel)

## 📂 Estrutura do Projeto

```plaintext
📁 confronto_nf_xml_invoice
│
├── main.py                  # Interface principal do Streamlit
├── requirements.txt         # Dependências Python
├── utils/
│   ├── parser_xml.py        # Extração e parse dos dados do XML
│   ├── parser_invoice.py    # Extração estruturada da planilha Invoice
│   └── comparador.py        # Comparação entre XML e Invoice
