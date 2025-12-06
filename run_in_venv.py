import argparse
import logging
import os
import platform
import re
import subprocess
import sys
import shutil
from pathlib import Path
from typing import List, Optional


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


logger = logging.getLogger(__name__)

info = logger.info
warning = logger.warning
debug = logger.debug

_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARN": logging.WARNING,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

_LEVEL_RE = re.compile(r'^\s*(?:\[(?P<bracket>[A-Za-z]+)\]|\b(?P<word>[A-Za-z]+):?)')


def _detect_line_level(line: str, default_level: int) -> int:
    """
    Попытаться распознать уровень из начала строки, иначе вернуть default_level.
    Форматы, которые понимаем: "DEBUG ...", "INFO: ...", "[WARNING] ..." и т.п.
    """
    m = _LEVEL_RE.match(line)
    if not m:
        return default_level
    tag = (m.group("bracket") or m.group("word") or "").upper()
    return _LEVEL_MAP.get(tag, default_level)


def log_system_brief() -> None:
    info("OS: %s %s (%s)", platform.system(), platform.release(), platform.architecture()[0])
    info("CWD: %s", os.getcwd())
    info("Python: %s %s (%s)", platform.python_implementation(), platform.python_version(), sys.executable)


def in_venv() -> bool:
    # True если мы запущены внутри virtualenv / venv
    return hasattr(sys, "real_prefix") or getattr(sys, "base_prefix", None) != getattr(sys, "prefix", None)


def _check_python_candidate(path: Path) -> Optional[Path]:
    """
    Попытка выполнить `python --version` через кандидат, вернуть Path если успешно.
    """
    if not path or not path.exists():
        return None
    try:
        proc = run_cmd_capture([str(path), "--version"])
        if proc.returncode == 0:
            return path
    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        return None
    return None


def get_system_python_executable() -> Path:
    current = Path(sys.executable)
    if not in_venv():
        return current

    warning("run_in_venv.py запущен из виртуального окружения, пытаюсь найти глобальный python и использовать его для poetry...")

    base = getattr(sys, "base_prefix", None) or getattr(sys, "real_prefix", None)
    candidates: List[Path] = []

    if base:
        base_path = Path(base)
        if os.name == "nt":
            candidates.append(base_path / "python.exe")
            candidates.append(base_path / "Scripts" / "python.exe")
        else:
            candidates.append(base_path / "bin" / "python3")
            candidates.append(base_path / "bin" / "python")

    for name in ("python3", "python"):
        which_path = shutil.which(name)
        if which_path:
            candidates.append(Path(which_path))

    if os.name != "nt":
        for p in ("/usr/bin/python3", "/usr/local/bin/python3", "/usr/bin/python"):
            candidates.append(Path(p))

    # проверяем кандидатов
    for cand in candidates:
        valid = _check_python_candidate(cand)
        if valid:
            info("Использую системный python для работы с poetry: %s", str(valid))
            return valid

    warning("Не нашел системный python, буду работать с тем, который запустил текущее исполнение: %s", str(current))
    return current


def get_project_root() -> Path:
    """
    Путь к корню проекта
    """
    return Path(__file__).resolve().parent


def _stream_subprocess(args: List[str], cwd: Optional[Path] = None, env: Optional[dict] = None,
                       default_level: int = logging.DEBUG) -> subprocess.CompletedProcess:
    """
    Запускает процесс и стримит stdout/stderr в текущий logger.
    Каждая строка анализируется на предмет префикса уровня и логируется соответствующим уровнем.
    Возвращает subprocess.CompletedProcess с накопленным stdout.
    """
    proc = subprocess.Popen(
        [str(a) for a in args],
        cwd=str(cwd) if cwd else None,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # упрощаем: объединяем потоки
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    out_lines: List[str] = []
    if proc.stdout is not None:
        try:
            for raw_line in proc.stdout:
                # сохраняем и логируем построчно
                line = raw_line.rstrip("\n")
                out_lines.append(line + "\n")
                level = _detect_line_level(line, default_level)
                logger.log(level, line)
        except KeyboardInterrupt:
            proc.kill()
            proc.wait()
            raise

    return_code = proc.wait()
    completed = subprocess.CompletedProcess(args, return_code, stdout="".join(out_lines))
    return completed


def log_command(func):
    """
    Декоратор, логирует команду перед выполнением. Поддерживает произвольные kwargs (например default_level).
    """
    def wrapper(args: List[str], cwd: Optional[Path] = None, **kwargs):
        logger.debug("CMD: %s", " ".join(str(a) for a in args))
        proc = func(args, cwd=cwd, **kwargs)
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, args, output=proc.stdout)
        return proc
    return wrapper


@log_command
def run_cmd_capture(args: List[str], cwd: Optional[Path] = None, env: Optional[dict] = None,
                    default_level: int = logging.DEBUG) -> subprocess.CompletedProcess:
    """
    Запускает команду, возвращает CompletedProcess. default_level указывает исходный уровень для строк без префикса.
    """
    return _stream_subprocess(args, cwd=cwd, env=env, default_level=default_level)


def get_pip_version(python_executable: Path) -> Optional[str]:
    """
    Версия pip
    """
    try:
        proc = run_cmd_capture([str(python_executable), "-m", "pip", "--version"])
        return proc.stdout.strip() if proc.stdout else None
    except subprocess.CalledProcessError:
        return None


def maybe_upgrade_pip(python_executable: Path) -> subprocess.CompletedProcess:
    """
    Попытка обновить pip
    """
    cmd = [str(python_executable), "-m", "pip", "install", "--upgrade", "pip"]
    return run_cmd_capture(cmd)


def ensure_poetry_installed(python_executable: Path) -> subprocess.CompletedProcess:
    """
    Устанавливает poetry если его нет
    """
    # проверим наличие poetry через python -m poetry --version
    try:
        return run_cmd_capture([str(python_executable), "-m", "poetry", "--version"])
    except subprocess.CalledProcessError:
        pass
    cmd = [str(python_executable), "-m", "pip", "install", "--upgrade", "poetry"]
    return run_cmd_capture(cmd)


def poetry_env_use(python_executable: Path) -> subprocess.CompletedProcess:
    cmd = [str(python_executable), "-m", "poetry", "env", "use", str(python_executable)]
    return run_cmd_capture(cmd)


def poetry_lock(python_executable: Path, project_root: Path) -> subprocess.CompletedProcess:
    args = [str(python_executable), "-m", "poetry", "lock"]
    return run_cmd_capture(args, cwd=project_root)


def poetry_sync(python_executable: Path, project_root: Path, no_root: bool = True, is_dev_env: bool = True) -> subprocess.CompletedProcess:
    args = [str(python_executable), "-m", "poetry", "sync", "--no-interaction"]
    if no_root:
        args.append("--no-root")
    if not is_dev_env:
        # не устанавливаем dev-зависимости
        args.append("--without=dev")
    return run_cmd_capture(args, cwd=project_root)


def get_poetry_venv_path(python_executable: Path, project_root: Path) -> Path:
    """
    Возвращает путь к виртуальному окружению poetry для проекта
    """
    proc = run_cmd_capture([str(python_executable), "-m", "poetry", "env", "info", "-p"], cwd=project_root)
    v = proc.stdout.strip() if proc.stdout else ""
    return Path(v)


def get_python_in_venv(venv_path: Path) -> Path:
    """
    Возвращает путь к python внутри указанного virtualenv
    """
    if os.name == "nt":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def run_in_venv(venv_python: Path, project_root: Path) -> int:
    """
    Запускает run.py через python виртуального окружения
    """
    run_script = project_root / "run.py"
    if not run_script.exists():
        raise SystemExit(2)
    cmd = [str(venv_python), str(run_script)] + sys.argv[1:]
    debug("CMD: %s", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(project_root))


def main() -> None:
    setup_logging()
    log_system_brief()
    project_root = get_project_root()
    python_exec = get_system_python_executable()
    pip_ver = get_pip_version(python_exec)
    debug("pip: %s", pip_ver or "unknown")

    # По умолчанию ставим dev-окружение
    is_dev_env = True
    logging.getLogger(__name__).setLevel(logging.DEBUG)

    maybe_upgrade_pip(python_exec)
    ensure_poetry_installed(python_exec)
    poetry_env_use(python_exec)
    poetry_lock(python_exec, project_root)
    poetry_sync(python_exec, project_root, no_root=True, is_dev_env=is_dev_env)
    venv_path = get_poetry_venv_path(python_exec, project_root)
    venv_python = get_python_in_venv(venv_path)
    if not venv_python.exists():
        proc_retry = poetry_sync(python_exec, project_root, no_root=True, is_dev_env=is_dev_env)
        if proc_retry.returncode != 0:
            raise subprocess.CalledProcessError(proc_retry.returncode, proc_retry.args)
        venv_path = get_poetry_venv_path(python_exec, project_root)
        venv_python = get_python_in_venv(venv_path)
    if not venv_python.exists():
        raise SystemExit(3)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--migrate", action="store_true", help="Run 'flask db upgrade' in project venv before running app")
    parser.add_argument("--seed", action="store_true", help="Run 'flask seed' in project venv before running app (idempotent)")
    args, _ = parser.parse_known_args()

    # окружение для flask-команд
    env = os.environ.copy()
    env.setdefault("FLASK_APP", "run.py")

    # Выполняем опциональные команды через venv_python
    if args.migrate:
        info("Running 'flask db upgrade' ...")
        run_cmd_capture([str(venv_python), "-m", "flask", "db", "upgrade"], cwd=project_root, env=env, default_level=logging.INFO)

    if args.seed:
        info("Running 'flask seed' ...")
        run_cmd_capture([str(venv_python), "-m", "flask", "seed"], cwd=project_root, env=env, default_level=logging.INFO)

    rc = run_in_venv(venv_python, project_root)
    if rc != 0:
        raise SystemExit(rc)


if __name__ == "__main__":
    main()
