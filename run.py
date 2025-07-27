# web_finance/run.py

import os
from app import create_app
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Cria a instância da aplicação Flask
app = create_app()

# Executa o servidor Flask
if __name__ == "__main__":
    # Inicia o aplicativo em modo de depuração se for ambiente de desenvolvimento
    app.run(debug=os.environ.get("FLASK_ENV") == "development")
