import logging

from run_in_venv import run_cmd_capture, setup_logging

setup_logging(log_format='%(message)s')
logging.getLogger().setLevel(logging.DEBUG)

run_cmd_capture(['poetry', 'run', 'locust', '-f', 'locustfile.py', '--host=http://localhost:5000'])
