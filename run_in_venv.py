"""
run_in_venv.py
----------------
Запускает проект через виртуальное окружение .venv в корне проекта.
Создает .venv, если его нет, устанавливает недостающие зависимости и запускает run.py.
"""

import logging
import os
import platform
import subprocess
import sys
from pathlib import Path


def setup_logging(log_file: str = 'run_in_venv.log'):
    """Настраивает логирование в консоль и файл."""
    logging.basicConfig(
        level=logging.INFO,
        format='[run_in_venv] %(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding='utf-8'),
        ],
    )


log = logging.getLogger(__name__).info


def log_system_info():
    """Выводит базовую информацию о системе и Python."""
    log('Исполнение скрипта: %s', Path(__file__).resolve())
    log('CWD: %s', os.getcwd())
    log('Python: %s %s', platform.python_implementation(), platform.python_version())
    log('Интерпретатор: %s', sys.executable)
    log('ОС: %s %s (%s)', platform.system(), platform.release(), platform.architecture()[0])


def is_inside_any_virtualenv() -> bool:
    """Проверяет, находится ли интерпретатор в виртуальном окружении."""
    return (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))


def get_project_venv_path(project_root: Path) -> Path:
    return project_root / '.venv'


def get_python_inside_venv(venv_path: Path) -> Path:
    return venv_path / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def is_running_from_project_venv(project_root: Path) -> bool:
    venv = get_project_venv_path(project_root).resolve()
    if not venv.exists():
        return False
    exe = Path(sys.executable).resolve()
    return venv in exe.parents


def create_project_venv(project_root: Path) -> None:
    """Создаёт .venv в корне проекта."""
    venv = get_project_venv_path(project_root)
    log('Создаю виртуальное окружение проекта по пути %s...', venv)
    try:
        subprocess.check_call([sys.executable, '-m', 'venv', str(venv)], cwd=str(project_root))
        log('Виртуальное окружение проекта успешно создано.')
    except subprocess.CalledProcessError as e:
        log('Ошибка при создании виртуального окружения: %s', e)
        raise


def install_missing_requirements(python_executable: Path, requirements_file: Path):
    """
    Устанавливает только недостающие зависимости из requirements.txt.
    Логирует каждое действие.
    """
    import re

    log('Обновляю pip до последней версии...')
    try:
        subprocess.run(
            [str(python_executable), '-m', 'pip', 'install', '--upgrade', 'pip'],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        log('pip обновлён до последней версии.')
    except subprocess.CalledProcessError as e:
        log('Не удалось обновить pip: %s', e)

    if not requirements_file.exists():
        log('%s не найден, установка зависимостей пропущена.', requirements_file)
        return

    log('Проверяю зависимости из %s...', requirements_file)

    # Получаем список уже установленных пакетов
    try:
        result = subprocess.run(
            [str(python_executable), '-m', 'pip', 'freeze'],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        installed_packages = {line.split('==')[0].lower() for line in result.stdout.splitlines() if '==' in line}
    except subprocess.CalledProcessError as e:
        log('Не удалось получить список установленных пакетов: %s', e)
        installed_packages = set()

    # Читаем requirements.txt
    requirements = []
    for line in requirements_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        lib_name = re.split(r'[<>=!]', line)[0].strip().lower()
        requirements.append((lib_name, line))

    all_success = True
    for lib_name, full_spec in requirements:
        if lib_name in installed_packages:
            continue
        log('Устанавливаю %s...', full_spec)
        try:
            subprocess.run(
                [str(python_executable), '-m', 'pip', 'install', full_spec],
                check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
        except subprocess.CalledProcessError as e:
            log('Ошибка при установке %s: %s', full_spec, e)
            all_success = False

    if all_success:
        log('Проверка зависимостей завершена, виртуальное окружение проекта настроено.')
    else:
        log('Некоторые зависимости не смогли установиться.')


def reexec_this_script_with_python(python_executable: Path):
    """Перезапускает текущий скрипт с другим интерпретатором Python."""
    log('Перезапуск скрипта внутри виртуального окружения проекта. Использую интерпретатор %s...', python_executable)
    script = Path(__file__).resolve()
    args = [str(python_executable), str(script)] + sys.argv[1:]
    os.chdir(str(script.parent))
    os.execv(str(python_executable), args)


def ensure_executing_from_project_venv(project_root: Path) -> None:
    if is_running_from_project_venv(project_root):
        log('Текущий процесс уже выполняется из виртуального окружения проекта.')
        return

    venv_path = get_project_venv_path(project_root)
    exists = venv_path.exists()
    if not exists:
        create_project_venv(project_root)

    venv_python = get_python_inside_venv(venv_path)
    install_missing_requirements(venv_python, project_root / 'requirements.txt')
    reexec_this_script_with_python(venv_python)


def run_run_py(project_root: Path):
    run_script = project_root / 'run.py'
    if not run_script.exists():
        log('Ошибка: run.py не найден в %s.', project_root)
        sys.exit(2)

    log('Запуск run.py через %s...', sys.executable)
    cmd = [sys.executable, str(run_script)] + sys.argv[1:]
    try:
        subprocess.check_call(cmd)
        log('run.py завершился успешно.')
    except subprocess.CalledProcessError as e:
        log('run.py завершился с ошибкой: %s', e)
        raise


def main():
    setup_logging()
    log_system_info()
    project_root = Path(__file__).resolve().parent
    ensure_executing_from_project_venv(project_root)
    install_missing_requirements(Path(sys.executable), project_root / 'requirements.txt')
    run_run_py(project_root)


if __name__ == '__main__':
    main()
