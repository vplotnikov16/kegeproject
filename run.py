from dotenv import load_dotenv
from flask import Flask

from app.config import Config

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    @app.route('/')
    def index_page():
        return 'DEVELOPMENT' if app.config['DEBUG'] else 'PRODUCTION'

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(app.config['HOST'], app.config['PORT'])
