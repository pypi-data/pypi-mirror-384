import json


def validate_json(token):
    """
    Valida e converte uma string JSON em um objeto Python (dict ou list).
    Parâmetros:
        token (str, dict ou list): O JSON a ser validado, podendo ser uma string ou já um objeto Python.
    Retorna:
        dict: Um dicionário contendo:
            - "success" (bool): Indica se a validação/conversão foi bem-sucedida.
            - "data" (dict ou list, opcional): O objeto Python resultante, presente se o sucesso for True.
            - "error" (Exception, opcional): A exceção capturada, presente se o sucesso for False.
    Exemplo:
        >>> validate_json('{"chave": "valor"}')
        {'success': True, 'data': {'chave': 'valor'}}
    """

    if not isinstance(token,dict) and not isinstance(token,list):

        try:

            token = json.loads(token)

            return {
                "success":True,
                "data":token
            }

        except json.JSONDecodeError as e:

            return {
                "success":False,
                "error":e
            }

        except Exception as e:

            return {
                "success":False,
                "error":e
            }
        
    else:

        return {
                "success":True,
                "data":token
            }