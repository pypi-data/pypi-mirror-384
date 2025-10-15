from __future__ import annotations
from pydantic import BaseModel, field_validator, model_validator, ValidationError, Field, ConfigDict
from typing import Optional, Mapping, Any, Annotated

NonEmptyStr = Annotated[str, Field(min_length=1)]
PositiveInt = Annotated[int, Field(gt=0)]

class InitParamsValidator(BaseModel):
    """
    Garante que ao menos um entre `creds_dict` e `creds_file` foi informado.
    """
    creds_dict: Optional[Mapping[str, Any]] = None
    creds_file: Optional[str] = None

    @model_validator(mode="after")
    def check_others_input(self):
        has_dict = isinstance(self.creds_dict, Mapping) and bool(self.creds_dict)
        has_file = isinstance(self.creds_file, str) and bool(self.creds_file.strip())

        if not (has_dict or has_file):
            raise ValueError(
                "Pelo menos um dos parâmetros 'creds_dict' (dict não vazio) "
                "ou 'creds_file' (caminho/string não vazia) deve ser fornecido."
            )
        return self

class ListFilesValidator(BaseModel):
    """
    Classe ListFilesValidator
    Valida os dados relacionados ao nome de um bucket no Google Cloud Platform (GCP).
    Atributos:
        bucket_name (str): Nome do bucket que será validado. Deve ser uma string não vazia.
    Métodos:
        check_str_name(cls, value, info):
            Valida se o valor fornecido para o nome do bucket é uma string não vazia.
            Levanta um ValueError se a validação falhar.
    """

    bucket_name:str

    @field_validator("bucket_name")
    def check_str_name(cls, value, info):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("O nome do bucket deve ser uma string não vazia.")
        return value
    
class GetFilesValidator(BaseModel):

    model_config = ConfigDict(strict=True)  # não faz coerção: "1024" não vira 1024

    bucket_name: NonEmptyStr
    filename: NonEmptyStr
    destination: NonEmptyStr
    chunksize: PositiveInt
    download_as: NonEmptyStr = 'file'  # 'file' ou 'bytes'

    # Opcional: se você quiser mensagens personalizadas além das do Field
    @field_validator("bucket_name", "filename", "destination", "download_as")
    def _not_blank(cls, v, info):
        if not v.strip():
            raise ValueError(f"O parametro '{info.field_name}' não pode ser vazio/whitespace.")
        return v
    
class _GetFilesValidator(BaseModel):
    """
    Classe GetFilesValidator
    Valida os parâmetros necessários para operações relacionadas a arquivos em um bucket GCP.
    Atributos:
        bucket_name (str): Nome do bucket GCP. Deve ser uma string não vazia.
        filename (str): Nome do arquivo. Deve ser uma string não vazia.
        destination (str): Caminho de destino. Deve ser uma string.
        chunksize (int): Tamanho dos chunks para processamento. Deve ser um inteiro.
    Métodos:
        check_str_name(cls, value, info):
            Valida se os campos 'bucket_name' e 'filename' são strings não vazias.
            Lança ValueError se a validação falhar.
        check_destination(cls, value, info):
            Valida se o campo 'destination' é uma string.
            Lança ValueError se a validação falhar.
        check_chunksize(cls, value, info):
            Valida se o campo 'chunksize' é um inteiro.
            Lança ValueError se a validação falhar.
    """

    bucket_name:str
    filename:str
    destination:str
    chunksize:int

    @field_validator("bucket_name","filename")
    def check_str_name(cls, value, info):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"O parametro '{info.field_name}' deve ser uma string e não um {type(value)} e não vazio")
        return value
    
    @field_validator("destination")
    def check_destination(cls, value, info):
        if not isinstance(value, str) or value is not None:
            raise ValueError(f"O parametro '{info.field_name}' deve ser uma string e não um {type(value)}")
        return value
    
    @field_validator("chunksize")
    def check_chunksize(cls, value, info):
        if not isinstance(value, int):
            raise ValueError(f"O parametro '{info.field_name}' deve ser um inteiro e não um {type(value)}")
        return value
    
class UploadFilesValidator(BaseModel):
    """
    Classe UploadFilesValidator
    Valida os parâmetros necessários para o upload de arquivos em um bucket GCP.
    Atributos:
        bucket_name (str): Nome do bucket onde o arquivo será armazenado.
        filename (str): Nome do arquivo a ser enviado.
        destination (str): Caminho de destino dentro do bucket.
    Métodos:
        check_str_name(cls, value, info):
            Valida se os campos 'bucket_name' e 'filename' são strings não vazias.
            Levanta um ValueError caso a validação falhe.
        check_destination(cls, value, info):
            Valida se o campo 'destination' é uma string.
            Levanta um ValueError caso a validação falhe.
    """

    bucket_name:str
    filename:str
    destination:str

    @field_validator("bucket_name","filename")
    def check_str_name(cls, value, info):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"O parametro '{info.field_name}' deve ser uma string e não um {type(value)} e não vazio")
        return value
    
    #@field_validator("destination")
    #def check_destination(cls, value, info):
    #    if not isinstance(value, str) or value is not None:
    #        raise ValueError(f"O parametro '{info.field_name}' deve ser uma string e não um {type(value)}")
    #    return value
    
    @field_validator("destination")
    def check_destination(cls, value, info):
        # CORREÇÃO: checar None e vazio (antes estava 'value is not None')
        if value is None or not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"O parametro '{info.field_name}' deve ser uma string não vazia; recebido {type(value)}"
            )
        return value.strip()    

class DeleteFilesValidator(BaseModel):
    """
    Classe DeleteFilesValidator
    Valida os parâmetros necessários para a exclusão de arquivos em um bucket GCP.
    Atributos:
        bucket_name (str): Nome do bucket onde os arquivos estão armazenados.
        filename (str): Nome do arquivo a ser excluído.
    Métodos:
        check_str_name(cls, value, info):
            Valida se os valores fornecidos para os campos 'bucket_name' e 'filename' 
            são strings não vazias. Levanta um ValueError caso a validação falhe.
    """

    bucket_name:str
    filename:str

    @field_validator("bucket_name","filename")
    def check_str_name(cls, value, info):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"O parametro '{info.field_name}' deve ser uma string e não um {type(value)} e não vazio")
        return value