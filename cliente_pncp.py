# cliente_pncp.py | módulo auxiliar 2
import requests
from datetime import datetime, timedelta
from modelos import Contratacao # Importa a classe do outro módulo

API_URL = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

class PncpClient:
    """
    Cliente para interagir com a API do PNCP.

    """
    
    def __init__(self, timeout=30):
        self.api_url = API_URL
        self.timeout = timeout

    def _validar_e_formatar_datas(self, d_inicial_str, d_final_str):
        """Valida o período e formata as datas para a API."""
        date_format = "%Y-%m-%d"
        try:
            d_inicial = datetime.strptime(d_inicial_str, date_format)
            d_final = datetime.strptime(d_final_str, date_format)
        except ValueError:
            raise ValueError("Formato de data inválido. Use AAAA-MM-DD.")
        
        if d_final - d_inicial > timedelta(days=365):
            raise ValueError("O período não pode ser maior que 365 dias.")
        
        # Formato da API (sem hífens)
        return d_inicial_str.replace('-', ''), d_final_str.replace('-', '')

    def buscar_contratacoes(self, data_inicial, data_final, codigo_modalidade, uf=None, pagina=1, palavra_chave=None):
        """
        Busca contratações na API e retorna uma lista de objetos Contratacao.
        """
        try:
            data_ini_fmt, data_fim_fmt = self._validar_e_formatar_datas(data_inicial, data_final)
        except ValueError as e:
            print(f"Erro de data: {e}")
            return [] # Retorna lista vazia em caso de erro de validação

        params = {
            'dataInicial': data_ini_fmt,
            'dataFinal': data_fim_fmt,
            'codigoModalidadeContratacao': codigo_modalidade,
            'pagina': pagina,
            'tamanhoPagina': 50
        }
        if uf:
            params['uf'] = uf.upper()

        try:
            response = requests.get(self.api_url, params=params, timeout=self.timeout)
            response.raise_for_status() # Lança exceção para erros HTTP (4xx, 5xx)
            
            json_data = response.json()
            resultados_brutos = json_data.get('data', [])
            
            # Converte a lista de dicionários em uma lista de objetos Contratacao
            lista_contratacoes = [Contratacao(item) for item in resultados_brutos]
            
            # Filtro por palavra-chave 
            if palavra_chave:
                palavra_chave_lower = palavra_chave.lower()
                
                resultados_filtrados = [
                    c for c in lista_contratacoes 
                    if palavra_chave_lower in c.objeto.lower()
                ]
                return resultados_filtrados
            else:
                return lista_contratacoes

        except requests.exceptions.Timeout:
            print("Erro: A API do PNCP demorou muito a responder.")
            return []
        except requests.exceptions.RequestException as e:
            print(f"Erro ao contatar a API do PNCP: {e}")
            return []