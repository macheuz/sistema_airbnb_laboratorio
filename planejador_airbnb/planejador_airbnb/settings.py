import os
from dotenv import load_dotenv


# Define o ambiente (padrão: desenvolvimento)
ENVIRONMENT = os.getenv("DJANGO_ENV", "dev")

if ENVIRONMENT == "prod":
    from .settings_prod import *
else:
    from .settings_dev import *