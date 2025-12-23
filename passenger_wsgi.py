import sys
import os

from app import create_app

INTERP = os.path.expanduser("/var/www/u3364214/data/.cache/pypoetry/virtualenvs/kegeproject-eddUrg6P-py3.10/bin/python")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.append(os.getcwd())

application = create_app()
