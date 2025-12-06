import logging

from run_in_venv import run_cmd_capture, setup_logging

setup_logging(log_format='%(message)s')
logging.getLogger().setLevel(logging.DEBUG)

run_cmd_capture(['pylint', 'app'])
run_cmd_capture(['pytest', '-q', 'tests/db'])
