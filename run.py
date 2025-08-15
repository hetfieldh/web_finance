# web_finance/run.py

import os

from dotenv import load_dotenv

# Constrói o caminho absoluto para o arquivo .env
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, ".env")

# Carrega o .env a partir do caminho específico
load_dotenv(dotenv_path=dotenv_path)

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_ENV") == "development")
