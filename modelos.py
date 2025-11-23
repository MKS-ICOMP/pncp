# modulo auxiliar 1
from datetime import datetime

class Contratacao:
    """
    Representa uma contratação do PNCP.
    """
    
    def __init__(self, data_dict):
        """
        Método Mágico __init__: O construtor.
        Usado para parsear o dicionário JSON da API.
        """
        # Usamos .get() com valores padrão para evitar KeyErrors se um campo faltar
        self.id = data_dict.get('numeroControlePNCP', 'ID N/A')
        self.objeto = data_dict.get('objetoCompra', 'N/A')
        self.orgao      = data_dict.get('orgaoEntidade',    {}).get('razaoSocial', 'Órgão N/A')

        # Acessando dados aninhados com segurança
        self.uf         = data_dict.get('unidadeOrgao',     {}).get('ufSigla', 'UF N/A')
        self.municipio  = data_dict.get('unidadeOrgao',     {}).get('municipio', {}).get('municipioNome', 'Município N/A')
        self.valor      = data_dict.get('valorTotalEstimado', 0)
        
        # Tratamento da data
        data_str = data_dict.get('dataPublicacaoPncp', '')
        self.data_publicacao = None
        if data_str:
            try:
                # Converte a string de data para um objeto datetime
                self.data_publicacao = datetime.fromisoformat(data_str)
            except ValueError:
                self.data_publicacao = None # Ignora datas em formato inválido

    # --- Sobrecarga de Métodos Mágicos ---

    def __str__(self):
        """
        Define a representação
        Chamado automaticamente quando usamos print(contratacao) ou str(contratacao).
        """
        data_fmt = self.data_publicacao.strftime('%d/%m/%Y') if self.data_publicacao else 'N/A'
        # Formata o valor como moeda brasileira
        valor_fmt = f"R$ {self.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        return (
            f"ID:       {self.id}\n"
            f"Objeto:   {self.objeto[:70]}...\n"
            f"Órgão:    {self.orgao} ({self.uf} - {self.municipio})\n"
            f"Publicado:{data_fmt} | Valor: {valor_fmt}"
        )

    def __repr__(self):
        """
        Representação "técnica" para debug.
        """
        return f"<Contratacao(id={self.id}, orgao='{self.orgao}')>"

    def __eq__(self, other):
        """
        Define o critério de igualdade (==).
        Duas contratações são iguais se seus IDs forem iguais.
        """
        if not isinstance(other, Contratacao):
            return False
        return self.id == other.id