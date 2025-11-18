# main_app.py - módulo principal
import curses
from datetime import datetime, timedelta
from cliente_pncp import PncpClient # Importa a classe do Módulo 2
from modelos import Contratacao    # Importa a classe do Módulo 1


ARQUIVO_FAVORITOS = "favoritos.txt"


# Dicionário com as modalidades
MODALIDADES_COMUNS = {
    1: "Concorrência",
    3: "Concurso",
    4: "Pregão",
    5: "Leilão",
    6: "Dispensa de Licitação",
    7: "Inexigibilidade de Licitação",
    9: "Credenciamento",
}

# --- Funções de Arquivo ---

def salvar_favorito(contratacao):
    """Salva uma contratação no arquivo de favoritos."""
    try:
        with open(ARQUIVO_FAVORITOS, 'a', encoding='utf-8') as f:
            f.write("=" * 20 + "\n")
            f.write(str(contratacao)) # Usa o método mágico __str__
            f.write("\n")
        return True
    except IOError as e:
        return f"Erro ao salvar: {e}"

def ler_favoritos():
    """Lê e retorna o conteúdo do arquivo de favoritos."""
    try:
        with open(ARQUIVO_FAVORITOS, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Nenhum favorito salvo ainda."
    except IOError as e:
        return f"Erro ao ler favoritos: {e}"

# --- Funções Auxiliares  ---

# FUNÇÃO PARA FORMATAR DATA
def formatar_data_para_api(data_str_usuario):
    """
    Converte uma data do formato DD/MM/AAAA (usuário)
    para AAAA-MM-DD (API).
    """
    try:
        data_obj = datetime.strptime(data_str_usuario, "%d/%m/%Y")
        return data_obj.strftime("%Y-%m-%d")
    except ValueError:
        # Lança um erro que a tela_buscar pode capturar
        raise ValueError(f"Data '{data_str_usuario}' está em formato inválido. Use DD/MM/AAAA.")

# --- Funções de Interface (Curses) ---

def desenhar_menu(stdscr, selected_row_idx):
    """Desenha o menu principal no curses."""
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    
    stdscr.addstr(0, 0, "=== Monitor de Licitações PNCP ===")
    stdscr.addstr(2, 0, "Use as setas (Cima/Baixo) e (Enter) para selecionar:")

    menu = ["Buscar Novas Licitações", "Ver Favoritos Salvos", "Sair"]
    for idx, item in enumerate(menu):
        y = 4 + idx
        if idx == selected_row_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, 0, f"> {item}")
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, 0, f"  {item}")
    
    stdscr.refresh()

def pegar_input_texto(stdscr, y, x, prompt):
    """Função auxiliar para pegar input de texto DENTRO do curses."""
    stdscr.addstr(y, x, prompt)
    stdscr.refresh()
    curses.echo()
    input_str = stdscr.getstr(y, x + len(prompt), 30).decode('utf-8')
    curses.noecho()
    return input_str.strip()

def tela_buscar(stdscr):
    """Tela para coletar dados da busca e exibir resultados."""
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    
    # ajustando "curses" tela minima
    # 3 (header) + 7 (modalidades) + 1 (gap) + 1 (prompt) + 5 (inputs) + 2 (gap/msg) = 19 linhas
    MIN_HEIGHT = 19
    
    if h < MIN_HEIGHT:
        stdscr.addstr(0, 0, "Erro: Janela do terminal muito pequena.")
        stdscr.addstr(2, 0, f"Altura mínima necessária: {MIN_HEIGHT}. Altura atual: {h}.")
        stdscr.addstr(4, 0, "Por favor, aumente o tamanho da janela.")
        stdscr.addstr(6, 0, "Pressione qualquer tecla para voltar.")
        stdscr.getch()
        return # Volta ao menu principal

    stdscr.addstr(0, 0, "--- Nova Busca ---")

    # Mostrar modalidades disponíveis ---
    stdscr.addstr(2, 0, "Modalidades Comuns (para referência):")
    y_atual = 3
    for codigo, nome in MODALIDADES_COMUNS.items():
        # Garante que não escreva fora da tela
        if y_atual < h - 8: # Deixa espaço para os inputs
            stdscr.addstr(y_atual, 2, f"[{codigo}] {nome}")
            y_atual += 1
    
    y_atual += 1 # Pula uma linha
    stdscr.addstr(y_atual, 0, "Preencha os campos (pressione Enter para confirmar):")
    y_atual += 1
    
    
    try:
        # Mudar formato de data para DD/MM/AAAA 
        data_hoje = datetime.now()
        data_default_ini = (data_hoje - timedelta(days=30)).strftime('%d/%m/%Y')
        data_default_fim = data_hoje.strftime('%d/%m/%Y')
        
        # Coletando inputs do usuário 
        data_inicial_usr = pegar_input_texto(stdscr, y_atual, 0, f"Data Inicial [Padrão: {data_default_ini}]: ") or data_default_ini
        y_atual += 1
        data_final_usr = pegar_input_texto(stdscr, y_atual, 0, f"Data Final [Padrão: {data_default_fim}]: ") or data_default_fim
        y_atual += 1

        # Conversão das datas para o formato da API
        data_inicial_api = formatar_data_para_api(data_inicial_usr)
        data_final_api = formatar_data_para_api(data_final_usr)
        
        
        modalidade = pegar_input_texto(stdscr, y_atual, 0, "Digite o Código da Modalidade: ")
        y_atual += 1
        uf = pegar_input_texto(stdscr, y_atual, 0, "UF (Opcional, ex: AM): ").upper()
        y_atual += 1
        palavra = pegar_input_texto(stdscr, y_atual, 0, "Palavra-chave (Opcional): ")
        y_atual += 2 

        if not modalidade.isdigit():
            stdscr.addstr(y_atual, 0, "Erro: Modalidade deve ser um número. Pressione qualquer tecla...")
            stdscr.getch()
            return

        stdscr.addstr(y_atual, 0, "Buscando na API do PNCP... Aguarde.")
        stdscr.refresh()

        client = PncpClient()
        resultados = client.buscar_contratacoes(
            data_inicial=data_inicial_api, # Envia formato AAAA-MM-DD
            data_final=data_final_api,     # Envia formato AAAA-MM-DD
            codigo_modalidade=int(modalidade),
            uf=uf,
            palavra_chave=palavra
        )

        exibir_resultados(stdscr, resultados)

    except ValueError as e: # Captura erros de data e outros
        stdscr.clear()
        stdscr.addstr(0, 0, f"Erro na validação dos dados: {e}")
        stdscr.addstr(2, 0, "Pressione qualquer tecla para voltar.")
        stdscr.getch()
    except Exception as e:
        stdscr.clear()
        stdscr.addstr(0, 0, f"Ocorreu um erro inesperado: {e}")
        stdscr.addstr(2, 0, "Pressione qualquer tecla para voltar.")
        stdscr.getch()

def exibir_resultados(stdscr, resultados):
    """Sub-tela para navegar nos resultados da busca."""
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    idx_atual = 0

    if not resultados:
        stdscr.addstr(0, 0, "Nenhum resultado encontrado.")
        stdscr.addstr(2, 0, "Pressione 'q' para voltar.")
        # Loop  para 'q' ou 'Q'
        while True:
            key = stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                break
        return

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, f"Resultado {idx_atual + 1} de {len(resultados)}")
        stdscr.addstr(1, 0, "[Seta Baixo] Próximo | [Seta Cima] Anterior | [S] Salvar | [Q] Voltar")
        
        contratacao_atual = resultados[idx_atual]
        # Usa o __str__ da classe Contratacao
        # stdscr.addstr(3, 0, str(contratacao_atual))
        # arrumando "curses" escrevendo fora do limite da tela com "\n"
        y_desenho = 3 # Linha onde começamos a desenhar a contratação
        linhas_contratacao = str(contratacao_atual).split('\n')
        
        for linha in linhas_contratacao:
            # Garante que não vamos desenhar fora da tela (altura)
            # Deixa a última linha (h-1) livre para mensagens de status
            if y_desenho < h - 1: 
                # Garante que não vamos desenhar fora da tela (largura)
                linha_truncada = linha[:w-1] # Trunca a linha para caber
                stdscr.addstr(y_desenho, 0, linha_truncada)
                y_desenho += 1
            else:
                break # Para de desenhar se a tela estiver cheia

        stdscr.refresh()
        
        key = stdscr.getch()
        
        if key == curses.KEY_DOWN and idx_atual < len(resultados) - 1:
            idx_atual += 1
        elif key == curses.KEY_UP and idx_atual > 0:
            idx_atual -= 1
        
        # Aceitar 's' ou 'S' para Salvar
        elif key == ord('s') or key == ord('S'):
            msg = salvar_favorito(contratacao_atual)
            
            stdscr.move(h-1, 0) # Move o cursor para a linha de status (fundo)
            stdscr.clrtoeol()   # Limpa qualquer msg antiga na linha
            
            if msg is True:
                stdscr.addstr(h-1, 0, "Salvo com sucesso!")
            else:
                stdscr.addstr(h-1, 0, str(msg)) # Mostra a mensagem de erro
            
            stdscr.refresh()
            curses.napms(1000) # Pausa por 1s para o usuário ver a msg
            # A msg será apagada no próximo loop pelo stdscr.clear()
        
        #  Aceitar 'q' ou 'Q' para Sair
        elif key == ord('q') or key == ord('Q'):
            break

def tela_favoritos(stdscr):
    """Tela que exibe os favoritos salvos."""
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    
    stdscr.addstr(0, 0, "--- Favoritos Salvos (lendo de 'favoritos.txt') ---")
    
    conteudo = ler_favoritos()

    #stdscr.addstr(2, 0, conteudo)
    # arrumando "curses" escrevendo fora do limite da tela com "\n"
    y_desenho = 2 # Linha onde começamos a desenhar o conteúdo
    linhas_conteudo = conteudo.split('\n')

    for linha in linhas_conteudo:
        # Garante que não vamos desenhar fora da tela (altura)
        # Deixa a última linha (h-1) livre para a mensagem de 'voltar'
        if y_desenho < h - 2: 
            # Garante que não vamos desenhar fora da tela (largura)
            linha_truncada = linha[:w-1] # Trunca a linha para caber
            stdscr.addstr(y_desenho, 0, linha_truncada)
            y_desenho += 1
        else:
            break # Para de desenhar se a tela estiver cheia

    stdscr.addstr(h-1, 0, "Pressione 'q' para voltar ao menu...")
    
    # Loop  para 'q' ou 'Q'
    while True:
        key = stdscr.getch()
        if key == ord('q') or key == ord('Q'):
            break
    stdscr.clear()

# --- Função Principal  ---

def main(stdscr):
    """Função principal da aplicação Curses."""
    curses.curs_set(0) # Esconde o cursor
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

    current_row = 0
    menu_functions = [tela_buscar, tela_favoritos, None]

    while True:
        desenhar_menu(stdscr, current_row)
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_functions) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            
            selected_function = menu_functions[current_row]
            
            if selected_function is None: # Sair
                break
            
            selected_function(stdscr)

# --- Ponto de Entrada ---
if __name__ == "__main__":

    # Integrante 1: Markcson  markson@ufam.edu.br
    # Integrante 2: Joel Jhimmy joeljhimmy@ufam.edu.br
    
    print("Instalação necessária: pip install -r requirements.txt")
    print("Iniciando aplicação...")
    
    try:
        curses.wrapper(main)
    except Exception as e:
        curses.endwin()
        print("\nOcorreu um erro e a aplicação foi fechada:")
        print(e)