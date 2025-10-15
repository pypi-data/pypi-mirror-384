import os  # google_drive.py da lib - Operações do sistema operacional
import base64  # Codificação/decodificação base64 para manipulação de dados
from googleapiclient.discovery import build  # Construção do cliente da API do Google
from googleapiclient.http import MediaFileUpload  # Upload de arquivos para APIs do Google
from googleapiclient.http import MediaIoBaseUpload  # Upload de streams/buffers para APIs do Google
from googleapiclient.errors import HttpError  # Tratamento de erros HTTP das APIs do Google
from io import BytesIO  # Manipulação de streams de bytes em memória
from google.oauth2 import service_account  # Autenticação com conta de serviço do Google
from .utilitarios.validations.GoogleDriveValidator import (
    InitParamsValidator,
    CreateFolderValidator,
    ListFolderValidator,
    UploadValidator,
)
from pydantic import ValidationError  # Exceções de validação do Pydantic
from typing import Iterable, Optional, Dict, List, Union, Any  # Type hints para melhor documentação


class GoogleDrive:
    """
    Classe responsável por gerenciar operações no Google Drive usando padrão Singleton.
    
    Esta classe implementa o padrão Singleton, garantindo que apenas uma instância
    seja criada durante a execução da aplicação. Fornece funcionalidades para:
    - Upload de arquivos para o Google Drive
    - Criação e listagem de pastas
    - Autenticação usando conta de serviço do Google
    - Operações de compartilhamento e permissões
    
    Note:
        Como implementa Singleton, todas as instâncias criadas retornarão
        a mesma referência de objeto, compartilhando estado e configurações.
    
    Attributes:
        _instance (Optional[GoogleDrive]): Instância única da classe (padrão Singleton)
        service: Cliente autenticado da API do Google Drive
        version (str): Versão da API do Google Drive sendo utilizada
        scopes (List[str]): Escopos de permissão para acesso ao Google Drive
        with_subject (str): Email do usuário para delegação de credenciais
        page_size (int): Número máximo de itens retornados por página nas consultas
    
    Examples:
        >>> # Primeira instância
        >>> drive1 = GoogleDrive(token=service_account_info, with_subject="user@domain.com")
        >>> 
        >>> # Segunda instância (retorna a mesma referência)
        >>> drive2 = GoogleDrive(token=other_token, with_subject="other@domain.com")
        >>> print(drive1 is drive2)  # True - mesma instância
    """

    _instance: Optional['GoogleDrive'] = None  # Atributo de classe para armazenar a única instância

    def __new__(cls, *args, **kwargs) -> 'GoogleDrive':
        """
        Implementa o padrão Singleton para garantir instância única.
        
        Este método garante que apenas uma instância da classe GoogleDrive
        seja criada durante toda a execução da aplicação, independentemente
        de quantas vezes o construtor seja chamado.
        
        Args:
            *args: Argumentos posicionais passados para o construtor
            **kwargs: Argumentos nomeados passados para o construtor
            
        Returns:
            GoogleDrive: A única instância da classe GoogleDrive
            
        Note:
            Na primeira chamada, uma nova instância é criada e armazenada.
            Nas chamadas subsequentes, a mesma instância é retornada.
        """
        # Verifica se já existe uma instância da classe
        if cls._instance is None:
            # Cria e armazena a instância na primeira chamada
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        token: Dict[str, Any],
        with_subject: str,
        scopes: List[str] = ["https://www.googleapis.com/auth/drive"],
        version: str = "v3",
    ) -> None:
        """
        Inicializa uma instância da classe GoogleDrive com autenticação de conta de serviço.
        
        Configura a autenticação usando uma conta de serviço do Google Cloud e
        estabelece conexão com a API do Google Drive. A autenticação é delegada
        para um usuário específico usando o parâmetro with_subject.
        
        Args:
            token (Dict[str, Any]): Dicionário contendo as credenciais da conta de serviço.
                Deve incluir campos como 'type', 'project_id', 'private_key_id',
                'private_key', 'client_email', 'client_id', 'auth_uri', 'token_uri', etc.
            with_subject (str): Email do usuário para o qual as credenciais serão delegadas.
                Este usuário deve ter permissões adequadas no domínio da organização.
            scopes (List[str], optional): Lista de escopos de permissão para acesso ao Google Drive.
                Padrão: ["https://www.googleapis.com/auth/drive"] (acesso completo).
                Outros exemplos: 
                - "https://www.googleapis.com/auth/drive.readonly" (somente leitura)
                - "https://www.googleapis.com/auth/drive.file" (apenas arquivos criados pela app)
            version (str, optional): Versão da API do Google Drive a ser utilizada.
                Padrão: "v3" (versão mais recente estável).
                
        Raises:
            ValueError: Se os dados de entrada falharem na validação do Pydantic.
                Inclui detalhes sobre quais campos são inválidos e por quê.
            
        Attributes:
            __token (Dict[str, Any]): Credenciais da conta de serviço (privado)
            version (str): Versão da API sendo utilizada
            scopes (List[str]): Escopos de permissão configurados
            with_subject (str): Email do usuário delegado
            page_size (int): Limite de itens por página (padrão: 1000)
            service: Cliente autenticado da API do Google Drive
        
        Examples:
            >>> # Configuração básica
            >>> token = {
            ...     "type": "service_account",
            ...     "project_id": "my-project",
            ...     "private_key": "-----BEGIN PRIVATE KEY-----\n...",
            ...     "client_email": "service@my-project.iam.gserviceaccount.com",
            ...     # ... outros campos obrigatórios
            ... }
            >>> drive = GoogleDrive(
            ...     token=token,
            ...     with_subject="user@domain.com"
            ... )
            >>>
            >>> # Configuração com escopos customizados
            >>> drive = GoogleDrive(
            ...     token=token,
            ...     with_subject="admin@domain.com",
            ...     scopes=["https://www.googleapis.com/auth/drive.readonly"],
            ...     version="v3"
            ... )
        """

        try:
            # Validação dos parâmetros usando Pydantic para garantir tipos e formatos corretos
            InitParamsValidator(
                token=token, with_subject=with_subject, scopes=scopes, version=version
            )
        except ValidationError as e:
            raise ValueError(
                "Erro na validação dos dados de input da inicialização da instância:",
                e.errors(),
            )
        
        # Armazenamento das configurações validadas
        self.__token = token  # Credenciais privadas da conta de serviço
        self.version = version  # Versão da API do Google Drive
        self.scopes = scopes  # Escopos de permissão para autenticação
        self.with_subject = with_subject  # Email do usuário para delegação
        self.page_size = 1000  # Limite padrão de itens por página nas consultas
        
        # Criação do cliente autenticado da API do Google Drive
        self.service = self.__create_service()

    def __create_service(self) -> Union[Any, bool]:
        """
        Cria e configura o cliente de serviço do Google Drive.
        
        Este método privado estabelece a conexão autenticada com a API do Google Drive
        usando as credenciais da conta de serviço configuradas durante a inicialização.
        O processo inclui autenticação delegada e construção do objeto de serviço.
        
        Returns:
            Union[Any, bool]: 
                - Objeto do serviço Google Drive se a conexão for bem-sucedida
                - False se ocorrer qualquer erro durante o processo de criação
        
        Raises:
            Exception: Capturada internamente e retorna False em caso de erro.
                Possíveis causas de erro incluem:
                - Credenciais inválidas ou malformadas
                - Problemas de conectividade de rede
                - Configurações incorretas de escopo ou versão da API
                - Falhas na delegação de credenciais
        
        Note:
            Este é um método privado (prefixo __) e não deve ser chamado diretamente
            fora da classe. É usado automaticamente durante a inicialização.
        
        Examples:
            >>> # Uso interno durante __init__
            >>> self.service = self.__create_service()
            >>> if self.service:
            ...     print("Conexão com Google Drive estabelecida")
            ... else:
            ...     print("Falha na conexão com Google Drive")
        """

        try:
            # Autentica usando as credenciais da conta de serviço com delegação de usuário
            auth = self.__autentica(self.with_subject)
            
            # Constrói o cliente da API do Google Drive com as credenciais autenticadas
            service = build(f"drive", f"{self.version}", credentials=auth)
            return service
        except Exception as e:
            # Em caso de erro, retorna False para indicar falha na criação do serviço
            # O erro específico é capturado mas não re-lançado para manter a interface limpa
            return False

    def __autentica(self, with_subject: str) -> Union[service_account.Credentials, bool]:
        """
        Realiza autenticação delegada usando conta de serviço do Google Cloud.
        
        Este método privado configura a autenticação OAuth2 usando uma conta de serviço
        e delega as credenciais para um usuário específico. É necessário quando uma
        aplicação precisa acessar recursos do Google Drive em nome de um usuário
        específico da organização.
        
        Args:
            with_subject (str): Email do usuário para o qual as credenciais serão delegadas.
                Este usuário deve existir no domínio da organização e ter as permissões
                adequadas para acessar os recursos solicitados.
        
        Returns:
            Union[service_account.Credentials, bool]:
                - Objeto de credenciais delegadas se a autenticação for bem-sucedida
                - False se ocorrer qualquer erro durante o processo de autenticação
        
        Raises:
            Exception: Capturada internamente e retorna False em caso de erro.
                Possíveis causas de erro incluem:
                - Token de conta de serviço inválido ou malformado
                - Usuário especificado não existe no domínio
                - Escopos insuficientes para a delegação
                - Conta de serviço sem permissão de delegação
        
        Note:
            - Este é um método privado (prefixo __) usado internamente pela classe
            - Requer que a conta de serviço tenha permissão de delegação configurada
            - O usuário delegado deve fazer parte do mesmo domínio da organização
        
        Examples:
            >>> # Uso interno - autentica para um usuário específico
            >>> credentials = self.__autentica("user@company.com")
            >>> if credentials:
            ...     print("Autenticação delegada bem-sucedida")
            ... else:
            ...     print("Falha na autenticação delegada")
        """

        try:
            # Cria credenciais da conta de serviço a partir do token fornecido
            credentials = service_account.Credentials.from_service_account_info(
                self.__token, scopes=self.scopes
            )
            
            # Delega as credenciais para o usuário especificado
            # Isso permite que a aplicação aja em nome do usuário
            delegated_credencial = credentials.with_subject(with_subject)
            return delegated_credencial

        except Exception as e:
            # Em caso de erro, retorna False para indicar falha na autenticação
            # O erro específico é capturado mas não re-lançado para manter a interface limpa
            return False

    def upload(self, folder_id: str, name: str, file_path: str, mimetype: str) -> Optional[Dict[str, Any]]:
        """
        Realiza upload de um arquivo para uma pasta específica no Google Drive.

        Este método faz upload de arquivos locais para o Google Drive, criando uma nova
        entrada na pasta especificada. Suporta todos os tipos de arquivo através da
        especificação do tipo MIME apropriado.

        Args:
            folder_id (str): ID único da pasta no Google Drive onde o arquivo será armazenado.
                Formato típico: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
            name (str): Nome que o arquivo terá no Google Drive (pode ser diferente do nome local).
                Exemplo: "documento_final.pdf", "relatorio_2025.xlsx"
            file_path (str): Caminho absoluto ou relativo para o arquivo no sistema local.
                Exemplo: "/home/user/documents/file.pdf", "C:\\Users\\user\\file.xlsx"
            mimetype (str): Tipo MIME do arquivo que define como ele será interpretado.
                Exemplos comuns:
                - "text/plain" - Arquivo de texto simples
                - "text/html" - Arquivo HTML
                - "image/jpeg" - Imagem JPEG
                - "image/png" - Imagem PNG
                - "audio/mpeg" - Arquivo de áudio MP3
                - "video/mp4" - Arquivo de vídeo MP4
                - "application/pdf" - Documento PDF
                - "application/vnd.ms-excel" - Planilha Excel
                - "application/octet-stream" - Arquivo binário genérico

        Returns:
            Optional[Dict[str, Any]]: 
                - Dicionário com informações do arquivo carregado se bem-sucedido:
                  {"id": "arquivo_id", "name": "nome_arquivo", "parents": ["pasta_id"], ...}
                - None se o arquivo local não for encontrado

        Raises:
            ValueError: Se os parâmetros de entrada falharem na validação do Pydantic.
                Inclui detalhes sobre quais campos são inválidos.
            HttpError: Se ocorrer erro na comunicação com a API do Google Drive.
                Pode indicar problemas de permissão, quota ou conectividade.

        Examples:
            >>> # Upload de um documento PDF
            >>> resultado = drive.upload(
            ...     folder_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
            ...     name="contrato_assinado.pdf",
            ...     file_path="/documents/contrato.pdf",
            ...     mimetype="application/pdf"
            ... )
            >>> if resultado:
            ...     print(f"Arquivo carregado com ID: {resultado['id']}")
            
            >>> # Upload de uma imagem
            >>> resultado = drive.upload(
            ...     folder_id="pasta_fotos_id",
            ...     name="foto_evento.jpg",
            ...     file_path="C:\\fotos\\evento.jpg",
            ...     mimetype="image/jpeg"
            ... )

        Note:
            - O arquivo deve existir no caminho especificado antes do upload
            - O folder_id deve referenciar uma pasta existente e acessível
            - O tipo MIME deve corresponder ao tipo real do arquivo para funcionamento adequado
            - Arquivos com mesmo nome na mesma pasta não são sobrescritos, são duplicados
        """
        try:
            # Validação dos parâmetros usando Pydantic para garantir tipos corretos
            UploadValidator(
                folder_id=folder_id, name=name, file_path=file_path, mimetype=mimetype
            )
        except ValidationError as e:
            raise ValueError(
                "Erro na validação dos dados para realizar o upload do arquivo",
                e.errors(),
            )

        # Metadados do arquivo: nome e pasta de destino no Google Drive
        file_metadata = {"name": name, "parents": [folder_id]}
        
        # Verifica se o arquivo existe no sistema local antes de tentar upload
        if not os.path.exists(file_path):
            return None  # Retorna None se arquivo não encontrado

        try:
            # Configura o objeto de mídia para upload com suporte a resumo
            media = MediaFileUpload(file_path, mimetype=mimetype, resumable=True)
            
            # Executa o upload do arquivo para o Google Drive
            file = (
                self.service.files()
                .create(
                    body=file_metadata,  # Metadados (nome, pasta pai)
                    media_body=media,    # Conteúdo do arquivo
                    fields="id",        # Campos a retornar (apenas ID para eficiência)
                    supportsAllDrives=True,  # Suporte a drives compartilhados
                )
                .execute()
            )

            # Retorna informações do arquivo carregado em formato padronizado
            return {"success": True, "result": file}
        except Exception as e:
            # Em caso de erro, retorna informações do erro em formato padronizado
            return {"success": False, "result": None, "error": str(e)}

    def _validate_folder_existence(self, folder: str, id_folder: str) -> Optional[Dict[str, Any]]:
        """
        Verifica se uma pasta específica existe dentro de uma pasta pai no Google Drive.
        
        Este método privado busca por uma pasta com nome específico dentro de uma pasta
        pai identificada por seu ID. É usado internamente para evitar duplicação de
        pastas antes de criar novas.
        
        Args:
            folder (str): Nome exato da pasta a ser verificada.
                Exemplo: "Documentos 2025", "Relatórios Mensais"
            id_folder (str): ID da pasta pai onde buscar.
                Formato típico: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        
        Returns:
            Optional[Dict[str, Any]]:
                - Dicionário com informações da pasta se encontrada:
                  {"id": "pasta_id", "name": "nome_pasta", "mimeType": "application/vnd.google-apps.folder"}
                - None se a pasta não for encontrada na pasta pai
        
        Raises:
            ValueError: Se ocorrer erro durante a busca pela pasta.
                Pode indicar problemas de conectividade, permissões ou IDs inválidos.
        
        Note:
            - Este é um método privado (prefixo _) usado internamente pela classe
            - A busca é case-sensitive (sensível a maiúsculas/minúsculas)
            - Apenas pastas não movidas para lixeira são consideradas
            - Suporta drives compartilhados da organização
        
        Examples:
            >>> # Busca pasta "Relatórios" dentro da pasta pai
            >>> pasta = self._validate_folder_existence("Relatórios", "parent_folder_id")
            >>> if pasta:
            ...     print(f"Pasta encontrada: {pasta['id']}")
            ... else:
            ...     print("Pasta não existe")
        """
        
        # Query para buscar itens na pasta pai que não estão na lixeira
        query = f"'{id_folder}' in parents and trashed=false"

        try:
            # Executa busca na API do Google Drive
            response = (
                self.service.files()
                .list(
                    q=query,  # Query de busca
                    spaces="drive",  # Espaço de busca (drive principal)
                    fields="nextPageToken, files(id, name, mimeType)",  # Campos retornados
                    pageToken=None,  # Token de paginação (primeira página)
                    includeItemsFromAllDrives=True,  # Incluir drives compartilhados
                    supportsAllDrives=True,  # Suporte a drives compartilhados
                )
                .execute()
            )

            # Extrai lista de arquivos/pastas da resposta
            items = response.get("files", [])

            # Procura por pasta com nome específico
            for item in items:
                # Verifica se é uma pasta (tipo MIME específico) e nome corresponde
                if (
                    item["mimeType"] == "application/vnd.google-apps.folder"
                    and item["name"] == folder
                ):
                    return item  # Retorna informações da pasta encontrada

            return None  # Pasta não encontrada

        except Exception as e:
            # Lança erro com contexto específico sobre a falha na busca
            raise ValueError(f"Erro tentando procurar pela pasta: {e}")

    def create_folder(
        self, name: str, parent_folder_id: str, validate_existence: bool = False
    ) -> Dict[str, Any]:
        """
        Cria uma nova pasta no Google Drive dentro de uma pasta pai especificada.

        Este método permite criar pastas no Google Drive com opção de verificar
        se a pasta já existe antes da criação. É útil para organizar arquivos
        em estruturas hierárquicas de pastas.

        Args:
            name (str): Nome da pasta a ser criada.
                Exemplo: "Relatórios 2025", "Documentos Importantes"
            parent_folder_id (str): ID da pasta pai onde a nova pasta será criada.
                Formato típico: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
                Use "root" para criar na raiz do drive
            validate_existence (bool, optional): Se True, verifica se a pasta já existe
                antes de tentar criar uma nova. Se a pasta existir, retorna suas
                informações ao invés de criar duplicata. Padrão: False.

        Returns:
            Dict[str, Any]: Dicionário padronizado com resultado da operação:
                - success (bool): True se operação bem-sucedida, False caso contrário
                - result (Dict[str, Any] | None): Informações da pasta criada/encontrada
                  incluindo ID, nome e outros metadados
                - error (str | None): Mensagem de erro se success=False

        Raises:
            ValueError: Se os parâmetros de entrada falharem na validação do Pydantic.
                Inclui detalhes sobre quais campos são inválidos.

        Examples:
            >>> # Criar pasta sem verificar existência
            >>> resultado = drive.create_folder(
            ...     name="Nova Pasta",
            ...     parent_folder_id="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
            ... )
            >>> if resultado["success"]:
            ...     print(f"Pasta criada com ID: {resultado['result']['id']}")

            >>> # Criar pasta verificando se já existe
            >>> resultado = drive.create_folder(
            ...     name="Documentos",
            ...     parent_folder_id="root",
            ...     validate_existence=True
            ... )
            >>> print(f"Status: {resultado['success']}")

        Note:
            - Se validate_existence=True e a pasta existir, não será criada duplicata
            - Nomes de pastas são case-sensitive no Google Drive
            - A pasta pai deve existir e ser acessível com as credenciais atuais
            - Suporta drives compartilhados da organização
        """
        try:
            # Validação dos parâmetros usando Pydantic
            CreateFolderValidator(
                name=name,
                parent_folder_id=parent_folder_id,
                validate_existence=validate_existence,
            )
        except ValidationError as e:
            raise ValueError(
                "Erro na validação dos dados de input da criação da pasta:",
                e.errors(),
            )

        status_existence = None

        # Verifica existência da pasta se solicitado
        if validate_existence:
            status_existence = self._validate_folder_existence(name, parent_folder_id)

        # Cria pasta apenas se não existir (ou se verificação não foi solicitada)
        if status_existence is None:
            try:
                # Metadados da nova pasta
                folder_metadata = {
                    "name": name,
                    "parents": [parent_folder_id],
                    "mimeType": "application/vnd.google-apps.folder",  # Tipo MIME para pastas
                }
                
                # Executa criação da pasta via API
                folder = (
                    self.service.files()
                    .create(
                        body=folder_metadata, 
                        fields="id", 
                        supportsAllDrives=True  # Suporte a drives compartilhados
                    )
                    .execute()
                )
                return {"success": True, "result": folder}
            except Exception as e:
                return {"success": False, "result": None, "error": str(e)}

        # Retorna pasta existente se encontrada
        return {"success": True, "result": status_existence}

    def list_items_folder(
        self,
        query: str = "",
        spaces: str = "drive",
        fields: str = "nextPageToken, files(id, name)",
    ) -> Dict[str, Any]:
        """
        Lista arquivos e pastas no Google Drive com base em critérios de busca especificados.

        Este método permite buscar e listar conteúdos do Google Drive usando queries
        personalizadas. Suporta busca em drives pessoais e compartilhados, com
        controle sobre quais campos são retornados para otimizar performance.

        Args:
            query (str, optional): Critério de busca para filtrar arquivos e pastas.
                Padrão: "" (lista todos os itens acessíveis).
                Exemplos de queries:
                - "'1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms' in parents and trashed=false"
                  (itens em pasta específica, não na lixeira)
                - "name contains 'relatório'" (arquivos com 'relatório' no nome)
                - "mimeType='application/pdf'" (apenas arquivos PDF)
                - "modifiedTime > '2025-01-01T00:00:00'" (modificados após data)
                Consulte: https://developers.google.com/drive/api/v3/ref-search-terms

            spaces (str, optional): Especifica locais de armazenamento para consulta.
                Padrão: "drive".
                Opções disponíveis:
                - "drive": Drive principal do usuário
                - "appDataFolder": Pasta de dados da aplicação
                - "photos": Google Fotos (se aplicável)

            fields (str, optional): Campos a serem retornados na resposta da API.
                Padrão: "nextPageToken, files(id, name)".
                Exemplos de campos:
                - "files(id, name, size, modifiedTime)" (informações básicas + tamanho/data)
                - "files(id, name, mimeType, parents)" (inclui tipo MIME e pastas pai)
                - "nextPageToken, files(*)" (todos os campos disponíveis)
                Consulte: https://developers.google.com/drive/api/v3/reference/files

        Returns:
            Dict[str, Any]: Dicionário padronizado com resultado da operação:
                - success (bool): True se operação bem-sucedida, False caso contrário
                - result (Dict[str, Any] | None): Dados retornados da API se success=True:
                  * files (List[Dict]): Lista de arquivos/pastas encontrados
                  * nextPageToken (str): Token para próxima página (se houver)
                - error (str | None): Mensagem de erro se success=False

        Raises:
            ValueError: Se os parâmetros de entrada falharem na validação do Pydantic.

        Examples:
            >>> # Listar todos os itens na raiz do drive
            >>> resultado = drive.list_items_folder()
            >>> if resultado["success"]:
            ...     arquivos = resultado["result"]["files"]
            ...     for arquivo in arquivos:
            ...         print(f"Nome: {arquivo['name']}, ID: {arquivo['id']}")

            >>> # Listar apenas PDFs em uma pasta específica
            >>> resultado = drive.list_items_folder(
            ...     query="'pasta_id' in parents and mimeType='application/pdf'",
            ...     fields="files(id, name, size, modifiedTime)"
            ... )

            >>> # Buscar arquivos por nome
            >>> resultado = drive.list_items_folder(
            ...     query="name contains 'contrato' and trashed=false"
            ... )

        Note:
            - Resultados são limitados pelo page_size configurado na inicialização
            - Use nextPageToken para navegar entre páginas de resultados extensos
            - Queries são case-insensitive para busca por nome
            - Suporta drives compartilhados automaticamente
        """
        try:
            # Validação dos parâmetros usando Pydantic
            ListFolderValidator(query=query, fields=fields, spaces=spaces)
        except ValidationError as e:
            raise ValueError(
                "Erro na validação dos dados de input da lista:", e.errors()
            )
            
        try:
            # Executa consulta na API do Google Drive
            results = (
                self.service.files()
                .list(
                    q=query,  # Query de busca
                    spaces=spaces,  # Espaços de armazenamento
                    pageSize=self.page_size,  # Limite de itens por página
                    fields=fields,  # Campos a retornar
                    supportsAllDrives=True,  # Suporte a drives compartilhados
                    includeItemsFromAllDrives=True,  # Incluir itens de drives compartilhados
                )
                .execute()
            )
            return {"success": True, "result": results}
        except HttpError as hr:
            # Erro específico da API HTTP (ex: 403 Forbidden, 404 Not Found)
            return {"success": False, "result": None, "error": str(hr)}
        except Exception as e:
            # Outros erros gerais (rede, parsing, etc.)
            return {"success": False, "result": None, "error": str(e)}

    def download_google_files(self, file: str, mimeType: str, path: str):
        """
        Obtém o conteúdo de um arquivo armazenado no Google Drive. Aceito somente para extensões Google

        Esta função acessa o Google Drive usando a API e lê os dados do arquivo especificado, retornando-os como um objeto binário de memória (`BytesIO`).

        Parâmetros:
            - file (str): Dicionário contendo informações do arquivo no Google Drive, incluindo as chaves:
                - `"name"`: Nome do arquivo.
                - `"id"`: ID do arquivo.

        Retorna:
            - BytesIO: Objeto em memória contendo os dados do arquivo.
            - None: Caso ocorra um erro ao tentar abrir ou ler o arquivo.

        Logs:
            - Registra mensagens indicando o início e o término da leitura do arquivo.
            - Em caso de falha, registra o erro ocorrido.

        Exceções:
            - Qualquer erro durante o processo será capturado e registrado no log. A função retornará `None` nesses casos.

        Dependências:
            - A função assume a existência de um atributo `self.service` configurado para interagir com a API do Google Drive.
        """
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            request = self.service.files().export_media(
                fileId=file.get("id"), mimeType=mimeType
            )
            file_path = f"{path}{file['name']}"
            with open(file_path, "wb") as f:
                f.write(request.execute())
            return {
                "success": True,
                "result": file_path,
                "error": None,
            }

        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    def download_others_files(self, file: str, path: str):
        """
        Obtém o conteúdo de um arquivo armazenado nos seguintes formatos:
        .xlsx, .pdf, .jpg, etc.

        Esta função acessa o Google Drive usando a API e lê os dados do arquivo especificado, retornando-os como um objeto binário de memória (`BytesIO`).

        Parâmetros:
            - file (str): Dicionário contendo informações do arquivo no Google Drive, incluindo as chaves:
                - `"name"`: Nome do arquivo.
                - `"id"`: ID do arquivo.
            - mimeType (str): Tipo do arquivo, por exemplo: xlsx = application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
            - path (str): diretório onde será salvo o arquivo.

        Retorna:
            - BytesIO: Objeto em memória contendo os dados do arquivo.
            - None: Caso ocorra um erro ao tentar abrir ou ler o arquivo.

        Logs:
            - Registra mensagens indicando o início e o término da leitura do arquivo.
            - Em caso de falha, registra o erro ocorrido.

        Exceções:
            - Qualquer erro durante o processo será capturado e registrado no log. A função retornará `None` nesses casos.

        Dependências:
            - A função assume a existência de um atributo `self.service` configurado para interagir com a API do Google Drive.
        """
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            request = self.service.files().get_media(fileId=file.get("id"))
            file_path = f"{path}{file["name"]}"
            with open(file_path, "wb") as f:
                f.write(request.execute())
            return {
                "success": True,
                "result": file_path,
            }

        except Exception as e:
            return {"success": False, "result": None}

    def get_base_data(self, id_sheet: str, page: str) -> list:
        """
        Retorna os dados da planilha especificada.
        Parâmetros:
        - drive_client: Cliente do Google Drive.
        - id_sheet: ID da planilha.
        - page: Nome da página da planilha.
        Retorna:
        - Uma lista contendo os valores da planilha.
        Exemplo de uso:
        >>> drive_client = ...
        >>> id_sheet = "abc123"
        >>> page = "Sheet1"
        >>> data = get_base_data(drive_client, id_sheet, page)
        """
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(spreadsheetId=id_sheet, range=page).execute()
            values = result.get("values", [])
            return {"success": True, "result": values}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    def delete_file(self, id_file:str):
        """
        Exclui um arquivo do Google Drive pelo seu ID.
        Args:
            id_file (str): O ID do arquivo a ser excluído.
        Returns:
            dict: Um dicionário indicando se a exclusão foi bem-sucedida.
                - {"success": True} se o arquivo foi excluído com sucesso.
                - {"success": False, "error": <mensagem de erro>} se ocorreu uma exceção.
        """

        try:
            self.service.files().delete(fileId=id_file, supportsAllDrives=True).execute()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _find_file_in_folder_by_name(self, parent_folder_id: str, name: str) -> Optional[dict]:
        """
        Retorna o primeiro arquivo (não excluído) com 'name' dentro de 'parent_folder_id',
        ou None se não existir.
        """
        # Escapa aspas simples no nome para a query
        safe_name = name.replace("'", r"\'")
        q = (
            f"'{parent_folder_id}' in parents and "
            f"name = '{safe_name}' and "
            f"trashed = false"
        )
        try:
            resp = (
                self.service.files()
                .list(
                    q=q,
                    spaces="drive",
                    pageSize=1,
                    fields="files(id, name, mimeType, size, webViewLink, parents)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute()
            )
            files = resp.get("files", [])
            return files[0] if files else None
        except Exception as e:
            # Padroniza retorno de erro
            return None

    def ensure_folder(self, parent_folder_id: str, name: str) -> str:
        """
        Usa o método create_folder(validate_existence=True) para retornar o ID de 'name'
        dentro de 'parent_folder_id', criando se não existir.
        """
        resp = self.create_folder(
            name=name,
            parent_folder_id=parent_folder_id,
            validate_existence=True,
        )

        if not resp or not resp.get("success"):
            raise RuntimeError(f"Falha ao garantir pasta '{name}': {resp}")
        # A classe retorna em "result" um dict com ao menos "id"
        folder = resp["result"]
        folder_id = folder.get("id")
        if not folder_id:
            # Algumas respostas podem ser {'success': True, 'result': {'id': '...'}} ou já o objeto
            # Se por algum motivo vier diferente, trate aqui
            raise RuntimeError(f"Resposta inesperada ao criar/buscar pasta: {folder}")
        return folder_id

    def ensure_path(self, path: str, parent_folder_id: str = "root") -> str:
        """
        Percorre/cria cada nível de 'path' dentro de 'parent_folder_id'.
        Retorna o ID da última pasta.
        """
        current_parent = parent_folder_id
        for part in [p for p in path.split("/") if p.strip()]:
            current_parent = self.ensure_folder(current_parent, part)
        return current_parent

    def upload_pdf_to_drive_path(
        self,
        local_pdf_path: str,
        drive_folder_path: str,
        parent_folder_id: str = "root",
        rename_as: Optional[str] = None,
    ) -> dict:
        """
        - Garante a hierarquia 'drive_folder_path' (ex: "MeusPdfs/2025/09")
        - Sobe o PDF com mimetype application/pdf
        - Se rename_as for fornecido, usa esse nome no Drive (com .pdf); caso contrário, basename do arquivo local.

        Retorna o dict padronizado da classe: {"success": True/False, "result": {...} | None, "error": str | None}
        """
        if not os.path.exists(local_pdf_path):
            return {"success": False, "result": None, "error": f"Arquivo não encontrado: {local_pdf_path}"}

        folder_id = self.ensure_path(drive_folder_path, parent_folder_id=parent_folder_id)

        # nome do arquivo no Drive
        base = os.path.basename(local_pdf_path)
        if rename_as:
            name = rename_as if rename_as.lower().endswith(".pdf") else f"{rename_as}.pdf"
        else:
            name = base

        # mimetype do PDF
        mimetype = "application/pdf"

        return self.upload(
            folder_id=folder_id,
            name=name,
            file_path=local_pdf_path,
            mimetype=mimetype,
        )

    def _gdrive_upload_or_update_media(
        self,
        folder_id: str,
        name: str,
        mimetype: str,
        file_handle: BytesIO,
        overwrite: bool = True,
    ) -> dict:
        """
        Se overwrite=True, procura por (name, folder_id) e:
        - se existir: faz update do conteúdo (mantém o mesmo fileId)
        - se não existir: cria
        Se overwrite=False, sempre cria (comportamento atual).
        """
        try:
            media = MediaIoBaseUpload(
                file_handle,
                mimetype=mimetype,
                resumable=True,
                chunksize=1024 * 1024,
            )
            if overwrite:
                existing = self._find_file_in_folder_by_name(folder_id, name)
                if existing:
                    file_id = existing["id"]
                    file = (
                        self.service.files()
                        .update(
                            fileId=file_id,
                            media_body=media,
                            fields="id, name, mimeType, size, webViewLink, parents",
                            supportsAllDrives=True,
                        )
                        .execute()
                    )
                    return {"success": True, "result": file, "error": None}

            # cria se não houver existente ou overwrite=False
            file_metadata = {"name": name, "parents": [folder_id]}
            file = (
                self.service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, name, mimeType, size, webViewLink, parents",
                    supportsAllDrives=True,
                )
                .execute()
            )
            return {"success": True, "result": file, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    def upload_pdf_bytes_to_drive_path(
        self,
        content: bytes,
        drive_folder_path: str,
        parent_folder_id: str = "root",
        name: str | None = None,
        overwrite: bool = True,  # << novo parâmetro
    ) -> dict:
        """
        Recebe o conteúdo do PDF em bytes e faz upload para a pasta indicada (criando hierarquia se necessário).
        """
        if not isinstance(content, (bytes, bytearray)) or not content:
            return {"success": False, "result": None, "error": "Parâmetro 'content' vazio ou inválido."}
        folder_id = self.ensure_path(drive_folder_path, parent_folder_id=parent_folder_id)

        # Nome do arquivo no Drive
        final_name = (name or "arquivo.pdf")
        if not final_name.lower().endswith(".pdf"):
            final_name += ".pdf"

        fh = BytesIO(content)
        #return self._gdrive_upload_media(folder_id=folder_id, name=final_name, mimetype="application/pdf", file_handle=fh)
        return self._gdrive_upload_or_update_media(
            folder_id=folder_id,
            name=final_name,
            mimetype="application/pdf",
            file_handle=fh,
            overwrite=overwrite,
        )

    def upload_pdf_base64_to_drive_path(
        self,
        b64_content: str,
        drive_folder_path: str,
        parent_folder_id: str = "root",
        name: str | None = None,
        strict: bool = True,
        overwrite: bool = True,  # << novo parâmetro
    ) -> dict:
        """
        Recebe o conteúdo do PDF como string Base64 e faz upload para a pasta indicada (criando hierarquia se necessário).
        - strict=True usa validação estrita no b64 (recomendado).
        - aceita strings com ou sem prefixo data URL (ex.: 'data:application/pdf;base64,...').
        """
        if not isinstance(b64_content, str) or not b64_content.strip():
            return {"success": False, "result": None, "error": "Parâmetro 'b64_content' vazio ou inválido."}

        # Remove prefixo data URL se existir
        # ex.: data:application/pdf;base64,JVBERi0xLjQKJ...
        if ";base64," in b64_content:
            b64_content = b64_content.split(";base64,", 1)[1]

        try:
            content = base64.b64decode(b64_content, validate=strict)
        except Exception as e:
            return {"success": False, "result": None, "error": f"Base64 inválido: {e}"}

        return self.upload_pdf_bytes_to_drive_path(
            content=content,
            drive_folder_path=drive_folder_path,
            parent_folder_id=parent_folder_id,
            name=name,
            overwrite=overwrite,
        )
