from dotenv import load_dotenv

from app import create_app
from app.config import Config, EnvEnum

load_dotenv()

app = create_app(Config)

if __name__ == '__main__':
    app.run(debug=app.config[EnvEnum.debug])
