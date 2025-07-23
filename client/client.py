import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8000
DIRECTORY = "client"
# O nome do ficheiro HTML principal que deve ser aberto
HTML_FILE = "index.html" 

# URL completa para abrir no navegador
URL = f"http://localhost:{PORT}/{HTML_FILE}"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def main():
    # Verifica se o diretório do cliente existe
    if not os.path.exists(DIRECTORY):
        print(f"Erro: Diretório '{DIRECTORY}' não encontrado!")
        sys.exit(1)
    
    # Verifica se o ficheiro HTML principal existe
    file_path = os.path.join(DIRECTORY, HTML_FILE)
    if not os.path.exists(file_path):
        print(f"Erro: Ficheiro principal '{file_path}' não encontrado!")
        sys.exit(1)
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"Servidor HTTP iniciado em http://localhost:{PORT}")
            
            try:
                print(f"Abrindo o jogo em seu navegador padrão: {URL}")
                webbrowser.open_new_tab(URL)
            except webbrowser.Error:
                print(f"Não foi possível abrir o navegador automaticamente. Por favor, acesse manualmente: {URL}")
            
            print("Pressione Ctrl+C para parar o servidor.")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\nServidor parado.")
    except Exception as e:
        print(f"Erro ao iniciar o servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()