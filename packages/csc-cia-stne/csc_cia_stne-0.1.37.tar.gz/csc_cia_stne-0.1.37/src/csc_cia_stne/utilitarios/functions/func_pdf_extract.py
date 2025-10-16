from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from typing import Optional, Dict, Any

def extrair_x_paginas_pdf(file_path: str, pages_limit: int = 15) -> Dict[str, Any]:
    """
    Extrai as primeiras X páginas de um arquivo PDF e retorna os bytes dessas páginas.

    Args:
        file_path (str): Caminho completo do arquivo PDF original.
        pages_limit (int, optional): Número máximo de páginas a serem extraídas. 
                                    Padrão: 15.

    Returns:
        Dict[str, Any]: Dicionário contendo:
            - success (bool): True se a operação foi bem-sucedida, False caso contrário
            - error (str|None): Mensagem de erro se houver falha, None se sucesso
            - data (bytes|None): Bytes do PDF extraído se sucesso, None se erro
            - total_doc_pages (int): Número total de páginas do documento original (apenas se success=True)
            - extracted_pages (int): Número de páginas efetivamente extraídas (apenas se success=True)
    
    Note:
        - Se o PDF tiver menos páginas que pages_limit, todas serão extraídas
        - Utiliza PyPDF2 para manipulação do arquivo PDF
        - Retorna success=False em caso de erro no processamento
    
    Example:
        >>> resultado = extrair_x_paginas_pdf("documento.pdf", 10)
        >>> if resultado["success"]:
        ...     print(f"PDF extraído com {len(resultado['data'])} bytes")
        ...     print(f"Páginas extraídas: {resultado['extracted_pages']}/{resultado['total_doc_pages']}")
        ... else:
        ...     print(f"Erro: {resultado['error']}")
    
    Raises:
        Não levanta exceções diretamente - erros são capturados e retornados no dicionário.
    """
    try:
        # Lê o arquivo PDF original
        reader = PdfReader(file_path)
        writer = PdfWriter()

        # Extrai as primeiras 'pages_limit' páginas ou menos, caso o PDF tenha menos de 'pages_limit' páginas
        total_doc_pages = len(reader.pages)
        for page_num in range(min(pages_limit, total_doc_pages)):
            writer.add_page(reader.pages[page_num])

        # Salva o novo PDF em um objeto BytesIO
        pdf_bytes = BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)  # Move o cursor para o início do buffer
        resposta = {"success": True, "error": None, "data": pdf_bytes.read(), "total_doc_pages": total_doc_pages, "extracted_pages": min(pages_limit, total_doc_pages)}
        return resposta
    except Exception as e:
        resposta = {"success": False, "error": f"Erro ao extrair as primeiras {pages_limit} páginas do PDF: {str(e)}", "data": None}
        return resposta

def extrair_paginas_intervalo_pdf(file_path: str, page_start: int = 1, pages_limit: int = 15) -> Dict[str, Any]:
    """
    Extrai um número específico de páginas de um arquivo PDF a partir de uma página inicial.

    Args:
        file_path (str): Caminho completo do arquivo PDF original.
        page_start (int, optional): Página inicial para começar a extração (1-indexed). 
                                Defaults to 1.
        pages_limit (int, optional): Número máximo de páginas a serem extraídas a partir 
                                    da página inicial. Defaults to 15.

    Returns:
        Optional[bytes]: Bytes do novo PDF contendo as páginas do intervalo especificado,
                    ou None em caso de erro.
    
    Note:
        - Se page_start for maior que o número total de páginas, retorna None
        - Se o número de páginas restantes for menor que pages_limit, extrai apenas as disponíveis
        - Utiliza PyPDF2 para manipulação do arquivo PDF
        - Páginas são indexadas começando em 1 (não 0)
    
    Example:
        >>> # Extrai 5 páginas começando da página 3
        >>> pdf_bytes = extrair_paginas_intervalo_pdf("documento.pdf", 3, 5)
        >>> if pdf_bytes["success"]:
        ...     print(f"PDF extraído com {len(pdf_bytes["data"])} bytes")
    """
    try:
        # Lê o arquivo PDF original
        reader = PdfReader(file_path)
        writer = PdfWriter()
        
        # Converte page_start para índice 0-based
        start_index = page_start - 1
        
        # Verifica se a página inicial é válida
        if start_index >= len(reader.pages) or start_index < 0:
            resposta = {"success": False, "error": f"Página inicial {page_start} inválida. O PDF tem {len(reader.pages)} páginas.", "data": None}
            return resposta

        # Calcula o índice final baseado no limite de páginas
        end_index = min(start_index + pages_limit, len(reader.pages))
        
        # Extrai as páginas do intervalo especificado
        for page_num in range(start_index, end_index):
            writer.add_page(reader.pages[page_num])
        
        # Salva o novo PDF em um objeto BytesIO
        pdf_bytes = BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)  # Move o cursor para o início do buffer

        resposta = {"success": True, "error": None, "data": pdf_bytes.read()}
        return resposta

    except Exception as e:
        resposta = {"success": False, "error": f"Erro ao extrair páginas {page_start}-{page_start + pages_limit - 1} do PDF: {str(e)}", "data": None}
        return resposta
