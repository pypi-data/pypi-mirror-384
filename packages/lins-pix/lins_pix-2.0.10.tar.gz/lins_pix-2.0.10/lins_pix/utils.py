import json


def write_file(content: str, path_file: str, type_file: str = '.json', mode: str = 'w') -> str:
    with open(path_file + type_file, mode) as outfile:
        outfile.write(json.dumps(content, indent=4))


def read_file(path_file: str, type_file: str = '.json') -> str:
    with open(path_file + type_file, 'r', encoding='utf8') as content:
        content = content.read()
    return json.loads(content)

def response_json(response):
    response.encoding = 'utf-8'
    try:
        return response.json()
    except ValueError:
        return response.text

def msg_erro(response, kwargs):

    response_data = response_json(response)

    erro = {
        'aplicacao': 'lins-pix',
        "status_code": getattr(response, "status_code", None),
        "url": getattr(response, "url", None),
        'method': kwargs.get('method', ''),
        'params': kwargs.get('params', ''),
        'data': kwargs.get('payload', ''),
        'headers': kwargs.get('headers', ''),
        'response': response_data
    }
    return erro

def msg_simple_error(response):
    response.encoding = 'utf-8'
    try:
        response_data = response.json()
    except:
        response_data = response.text

    erro = {
        'aplicacao': 'lins-pix',
        'status_code': response.status_code,
        'url': response.url,
        'response': response_data
    }
    return erro


def msg_exception(erro, funcao):
    message = {
        'aplicacao': 'lins-pix',
        'funcao': funcao,
        'erro': erro,
    }
    return message
