from typing import Optional, Dict, Union
from google.cloud import documentai_v1beta3 as documentai
from google.oauth2 import service_account

class GCPDocumentAIClient:
    def __init__(self, credential_json: Optional[dict] = None, processor_id: Optional[str] = None) -> None:
        """
        Inicializa o cliente do Google Cloud Document AI.

        Args:
            credential_json (Optional[dict]): Dicionário contendo as credenciais do Google Cloud.
            processor_id (Optional[str]): ID do processador do Document AI.
        
        Attributes:
            credential_json (dict): Credenciais do Google Cloud
            project_id (str): ID do projeto extraído das credenciais
            location (str): Localização do processador (fixo: "us")
            processor_id (str): ID do processador do Document AI
            client (documentai.DocumentProcessorServiceClient): Cliente do Document AI
            is_connected (bool): Status da conexão
            error (str|None): Mensagem de erro se houver falha na inicialização
        """
        self.credential_json: dict = credential_json
        self.project_id: str = self.credential_json.get("project_id")
        self.location: str = "us"
        self.processor_id: str = processor_id

        try:
            self.client: documentai.DocumentProcessorServiceClient = self._get_document_ai_client(self.credential_json)
            self.is_connected: bool = True
            self.error = None

        except Exception as e:
            error_msg = f"Erro ao inicializar o cliente do Document AI: {e}"
            self.is_connected = False
            self.error = error_msg

    def _get_document_ai_client(self, credential_json: dict) -> documentai.DocumentProcessorServiceClient:
        """
        Cria e retorna o cliente do Document AI.

        Args:
            credential_json (dict): Dicionário contendo as credenciais do Google Cloud.

        Returns:
            documentai.DocumentProcessorServiceClient: Cliente autenticado do Document AI.
        
        Raises:
            Exception: Se houver erro na autenticação ou inicialização do cliente.
        """
        try:
            credential = service_account.Credentials.from_service_account_info(credential_json)
        except Exception as e:
            error_msg = f"Erro ao criar credenciais do Document AI: {e}"
            raise Exception(error_msg)

        return documentai.DocumentProcessorServiceClient(credentials=credential)

    
    def ler_documento(self, file_bytes: bytes, mime_type: str) -> Dict[str, Union[bool, str, documentai.Document, None]]:
        """
        Processa um documento PDF usando o Google Cloud Document AI para extrair texto.

        Args:
            file_bytes (bytes): Bytes do arquivo PDF a ser processado.
            mime_type (str): Tipo MIME do arquivo (ex.: "application/pdf").

        Returns:
            Dict[str, Union[bool, str, documentai.Document, None]]: Resultado do processamento
                - success (bool): True se o processamento foi bem-sucedido
                - error (str|None): Mensagem de erro se houver falha
                - data (documentai.Document|None): Documento processado pelo Document AI
        
        Example:
            >>> client = GCPDocumentAIClient(creds, processor_id)
            >>> with open("documento.pdf", "rb") as f:
            ...     resultado = client.ler_documento(f.read(), "application/pdf")
            >>> if resultado["success"]:
            ...     texto = resultado["data"].text
            ...     print(f"Texto extraído: {texto[:100]}...")
        
        Note:
            - Utiliza o processador configurado no __init__
            - Processa o documento completo enviado em file_bytes
            - Para limitar páginas, use extrair_x_paginas_pdf antes desta função
        """
        try:
            name = self.client.processor_path(self.project_id, self.location, self.processor_id)
            request = documentai.ProcessRequest(
                name=name,
                raw_document=documentai.RawDocument(content=file_bytes, mime_type=mime_type)
            )
            
            result = self.client.process_document(request=request)
            return {"success": True, "error": None, "data": result.document}

        except Exception as e:
            error_msg = f"Erro ao processar o documento com o Document AI: {str(e)}"
            return {"success": False, "error": error_msg, "data": None}

