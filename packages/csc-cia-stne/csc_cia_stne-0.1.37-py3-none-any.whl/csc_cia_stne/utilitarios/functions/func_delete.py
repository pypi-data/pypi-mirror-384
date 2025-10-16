import os
import shutil


def delete_file(filename:str) -> bool:
    """
    Exclui um arquivo no diretório atual com o nome especificado.
    Parâmetros:
        filename (str): O nome do arquivo a ser excluído.
    Retorna:
        dict: Um dicionário indicando o sucesso da operação. 
            - Se bem-sucedido: {"success": True}
            - Se falhar: {"success": False, "error": <mensagem de erro>}
                Possíveis mensagens de erro incluem:
                    - "Permissão negada."
                    - "Arquivo não encontrado."
                    - Mensagem de exceção genérica.
    """

    filepath = os.path.join(os.getcwd(), filename)

    if os.path.exists(filepath):

        try:
            os.remove(filepath)

            return {
                "success": True,
            }
        
        except PermissionError as e:

            return {
                "success": False,
                "error": "Permissão negada.",
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e),
            }
        
    else:

        return {
            "success": False,
            "error": "Arquivo não encontrado."
        }

def delete_folder(foldername:str):
    """
    Exclui uma pasta especificada pelo nome.
    Parâmetros:
        foldername (str): O nome da pasta a ser excluída.
    Retorna:
        dict: Um dicionário indicando se a exclusão foi bem-sucedida.
            - Se bem-sucedido: {"success": True}
            - Se a pasta não for encontrada: {"success": False, "error": "Pasta não encontrada."}
            - Se houver permissão negada: {"success": False, "error": "Permissão negada."}
            - Para outros erros: {"success": False, "error": <mensagem do erro>}
    """

    filepath = os.path.join(os.getcwd(), foldername)

    if os.path.exists(filepath):

        try:

            shutil.rmtree(filepath)

            return {
                "success": True
            }

        except PermissionError as e:

            return {
                "success": False,
                "error": "Permissão negada.",
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e),
            }
        
    else:

        return {
            "success": False,
            "error": "Pasta não encontrada."
        }