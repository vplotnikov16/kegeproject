import random
import json
import re
from typing import Dict, List, Optional

from locust import HttpUser, task, tag, between, events

# Конфигурация тестовых пользователей
TEST_USERS = [
    {"username": "testuser1", "password": "P@ssw0rd"},
    {"username": "testuser2", "password": "P@ssw0rd"},
    {"username": "testuser3", "password": "P@ssw0rd"},
    {"username": "admin", "password": "admin"},  # для админ-операций
]

# Типовые ответы для задач ЕГЭ
SAMPLE_ANSWERS = [
    "42",         # скаляр
    "123;456",    # вектор для задач 17,18,26
    "7;5;3",      # вектор для задачи 19
    "RED",        # слово
    "5",
]

# --- Инъекция "искусственных" ошибок для статистики ---
FORCED_FAIL_RATE = 0.2          # 40% запросов в /api/* и /attempts/* будут помечены как failed
REQUEST_TIMEOUT_SEC = 15         # timeout в секундах (requests-совместимый)


class KegeProjectUser(HttpUser):
    """Базовый класс пользователя системы Экзам-ON."""

    wait_time = between(1.0, 3.0)  # пауза между запросами 1-3 секунды

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.csrf_token: Optional[str] = None
        self.user_credentials: Optional[Dict] = None
        self.logged_in = False

        self.current_attempt_id: Optional[int] = None
        self.current_variant_task_ids: List[int] = []  # VariantTask.id для текущей попытки

    def on_start(self):
        """Инициализация: получаем CSRF (если есть) и логинимся."""
        self._get_csrf_token()
        self._login()

    # -----------------------------
    # Helpers: forced failure logic
    # -----------------------------
    @staticmethod
    def _should_force_fail() -> bool:
        return random.random() < FORCED_FAIL_RATE

    @staticmethod
    def _is_api_or_attempts_path(path: str) -> Optional[str]:
        """Возвращает группу ('api'/'attempts') или None."""
        if path.startswith("/api/"):
            return "api"
        if path.startswith("/attempts/"):
            return "attempts"
        return None

    def _success_or_forced_fail(self, response, group_label: str):
        """
        Помечает запрос как success или (с вероятностью FORCED_FAIL_RATE) как fail,
        при этом запрос реально выполнен и учтен в статистике.
        """
        if self._should_force_fail():
            response.failure(f"Injected failure ({group_label}, {int(FORCED_FAIL_RATE * 100)}%)")
        else:
            response.success()

    def _handle_status(
        self,
        response,
        request_path: str,
        ok_statuses,
        allowed_statuses=None,
    ):
        """
        Унифицированная обработка статусов:
        - ok_statuses: статусы, которые считаются успехом
        - allowed_statuses: статусы, которые допустимы и тоже считаются успехом (например, 403/404)
        Если path относится к /api или /attempts, то для "успеха" применяется инъекция 40% fail.
        """
        allowed_statuses = allowed_statuses or set()
        ok_statuses = set(ok_statuses)
        allowed_statuses = set(allowed_statuses)

        if response.status_code in ok_statuses or response.status_code in allowed_statuses:
            group = self._is_api_or_attempts_path(request_path)
            if group:
                self._success_or_forced_fail(response, group)
            else:
                response.success()
        else:
            response.failure(f"Status code: {response.status_code}")

    # -----------------------------
    # CSRF / Login
    # -----------------------------
    def _get_csrf_token(self):
        """
        Попытка получить CSRF токен с /login (если CSRF включен).
        Если токен не найден — оставляем None и продолжаем.
        """
        with self.client.get(
            "/login",
            catch_response=True,
            name="GET /login (csrf probe)",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Failed to open login page: {response.status_code}")
                return

            # Ищем <input ... name="csrf_token" ... value="...">
            m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', response.text)
            if m:
                self.csrf_token = m.group(1)

            response.success()

    def _login(self):
        """Аутентификация пользователя."""
        self.user_credentials = random.choice(TEST_USERS)

        payload = {
            "username": self.user_credentials["username"],
            "password": self.user_credentials["password"],
        }
        if self.csrf_token:
            payload["csrf_token"] = self.csrf_token

        with self.client.post(
            "/login",
            data=payload,
            catch_response=True,
            name="POST /login",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            if response.status_code in (200, 302):
                self.logged_in = True
                response.success()
            else:
                response.failure(f"Login failed: {response.status_code}")

    # -----------------------------
    # Public pages
    # -----------------------------
    @tag("public", "read")
    @task(10)
    def view_homepage(self):
        """Просмотр главной страницы (дашборд)."""
        with self.client.get(
            "/",
            catch_response=True,
            name="GET / (homepage)",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            self._handle_status(response, "/", ok_statuses={200})

    @tag("public", "read")
    @task(8)
    def view_tasks_list(self):
        """Просмотр списка задач."""
        with self.client.get(
            "/tasks/",
            catch_response=True,
            name="GET /tasks/",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            self._handle_status(response, "/tasks/", ok_statuses={200})

    @tag("public", "read")
    @task(5)
    def view_single_task(self):
        """Просмотр конкретной задачи по ID."""
        task_id = random.randint(1, 400)  # предполагаем 400 задач из seed
        path = f"/tasks/view_task/{task_id}"
        with self.client.get(
            path,
            catch_response=True,
            name="GET /tasks/view_task/<id>",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            # 404 допустим для несуществующих задач
            self._handle_status(response, path, ok_statuses={200}, allowed_statuses={404})

    @tag("public", "read")
    @task(7)
    def view_variants_list(self):
        """Просмотр списка вариантов."""
        # ВАЖНО: в вашем коде blueprint variants имеет url_prefix='/variants' и
        # дополнительно регистрируется с url_prefix='/variants', поэтому на практике
        # URL обычно получается /variants/variants/ (через url_for). См. base.html.
        path = "/variants/variants/"
        with self.client.get(
            path,
            catch_response=True,
            name="GET /variants/variants/",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            self._handle_status(response, path, ok_statuses={200})

    @tag("public", "read")
    @task(4)
    def view_variant_details(self):
        """Просмотр деталей варианта."""
        variant_id = random.randint(1, 150)  # предполагаем 150 вариантов из seed
        path = f"/variants/variants/view_variant/{variant_id}"
        with self.client.get(
            path,
            catch_response=True,
            name="GET /variants/variants/view_variant/<id>",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            self._handle_status(response, path, ok_statuses={200}, allowed_statuses={404})

    @tag("public", "read")
    @task(2)
    def view_about_page(self):
        """Просмотр страницы О проекте."""
        with self.client.get(
            "/about",
            catch_response=True,
            name="GET /about",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            self._handle_status(response, "/about", ok_statuses={200})

    # -----------------------------
    # Profile pages (auth)
    # -----------------------------
    @tag("auth", "read")
    @task(6)
    def view_profile(self):
        """Просмотр собственного профиля."""
        if not self.logged_in:
            return

        with self.client.get(
            "/profile",
            catch_response=True,
            name="GET /profile",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            self._handle_status(response, "/profile", ok_statuses={200})

    @tag("auth", "read")
    @task(3)
    def view_profile_stats(self):
        """Просмотр статистики профиля."""
        if not self.logged_in:
            return

        with self.client.get(
            "/profile/stats",
            catch_response=True,
            name="GET /profile/stats",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            self._handle_status(response, "/profile/stats", ok_statuses={200})

    @tag("auth", "read")
    @task(2)
    def view_my_tasks(self):
        """Просмотр своих задач (для авторов)."""
        if not self.logged_in:
            return

        with self.client.get(
            "/profile/my-tasks",
            catch_response=True,
            name="GET /profile/my-tasks",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            self._handle_status(response, "/profile/my-tasks", ok_statuses={200})

    # -----------------------------
    # Exam flows (/attempts...) -> inject 40% fails
    # -----------------------------
    @tag("auth", "exam")
    @task(5)
    def start_exam_attempt(self):
        """Начать попытку прохождения экзамена (лучше GET, т.к. эндпоинт принимает GET/POST)."""
        if not self.logged_in:
            return

        variant_id = random.randint(1, 150)
        path = f"/variants/variants/start_exam/{variant_id}"

        with self.client.get(
            path,
            catch_response=True,
            name="GET /variants/variants/start_exam/<id>",
            timeout=REQUEST_TIMEOUT_SEC,
            allow_redirects=False,
        ) as response:
            # Ожидаем редирект на /attempts/<attempt_id>
            if response.status_code in (302, 303, 307, 308):
                location = response.headers.get("Location", "")
                if "/attempts/" in location:
                    try:
                        self.current_attempt_id = int(location.split("/attempts/")[1].split("/")[0])
                    except (IndexError, ValueError):
                        self.current_attempt_id = None
                    self.current_variant_task_ids = []
                response.success()
            elif response.status_code == 200:
                # Если вдруг не редиректит
                response.success()
            elif response.status_code in (403, 404):
                # не найден/нет доступа — допустимо для случайного variant_id
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

    @tag("auth", "exam")
    @task(3)
    def view_attempt_page(self):
        """Просмотр страницы попытки (интерфейс экзамена)."""
        if not self.logged_in:
            return

        attempt_id = self.current_attempt_id or random.randint(1, 300)
        path = f"/attempts/{attempt_id}"

        with self.client.get(
            path,
            catch_response=True,
            name="GET /attempts/<id>",
            timeout=REQUEST_TIMEOUT_SEC,
            allow_redirects=False,
        ) as response:
            # 302 возможен, если не залогинен (но мы стараемся быть залогиненными)
            self._handle_status(
                response,
                path,
                ok_statuses={200},
                allowed_statuses={302, 403, 404},
            )

    @tag("auth", "exam", "ajax")
    @task(4)
    def get_attempt_data(self):
        """Получение данных попытки через AJAX API."""
        if not self.logged_in:
            return

        attempt_id = self.current_attempt_id or random.randint(1, 300)
        path = f"/attempts/{attempt_id}/data"

        with self.client.get(
            path,
            catch_response=True,
            name="GET /attempts/<id>/data (AJAX)",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
                    return

                # Пытаемся достать VariantTask.id из payload (схема может меняться, поэтому делаем гибко)
                vt_ids: List[int] = []
                for key in ("variant_tasks", "tasks"):
                    items = data.get(key)
                    if isinstance(items, list):
                        for it in items:
                            if not isinstance(it, dict):
                                continue
                            for cand in ("variant_task_id", "variantTaskId", "id"):
                                v = it.get(cand)
                                if isinstance(v, int):
                                    vt_ids.append(v)
                                    break

                if vt_ids and attempt_id == self.current_attempt_id:
                    self.current_variant_task_ids = vt_ids

                # успех, но с инъекцией 40% fail (так как /attempts/*)
                self._success_or_forced_fail(response, "attempts")
                return

            if response.status_code in (302, 403, 404):
                self._success_or_forced_fail(response, "attempts")
            else:
                response.failure(f"Status code: {response.status_code}")

    @tag("auth", "exam", "ajax", "write")
    @task(2)
    def save_answer(self):
        """Сохранение ответа на задачу через AJAX."""
        if not self.logged_in:
            return

        attempt_id = self.current_attempt_id or random.randint(1, 300)
        path = f"/attempts/{attempt_id}/save-answer"

        # Стараемся брать vt_id из текущей попытки (иначе слишком много 400 из-за несоответствия variant_id)
        if self.current_variant_task_ids and attempt_id == self.current_attempt_id:
            variant_task_id = random.choice(self.current_variant_task_ids)
        else:
            variant_task_id = random.randint(1, 4050)

        answer_text = random.choice(SAMPLE_ANSWERS)

        with self.client.post(
            path,
            json={"variant_task_id": variant_task_id, "answer_text": answer_text},
            catch_response=True,
            name="POST /attempts/<id>/save-answer (AJAX)",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            # В проекте тут возможны 200 (ok), 400 (невалидная задача), 403/404 (нет доступа/не найдено)
            if response.status_code == 200:
                self._success_or_forced_fail(response, "attempts")
            elif response.status_code in (400, 403, 404):
                # оставляем как "допустимо", но всё равно применяем 40% инъекцию
                self._success_or_forced_fail(response, "attempts")
            else:
                response.failure(f"Status code: {response.status_code}")

    @tag("auth", "exam", "write")
    @task(1)
    def finish_attempt(self):
        """Завершение попытки экзамена."""
        if not self.logged_in:
            return

        attempt_id = self.current_attempt_id or random.randint(1, 300)
        path = f"/attempts/{attempt_id}/finish"

        with self.client.post(
            path,
            catch_response=True,
            name="POST /attempts/<id>/finish",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            if response.status_code == 200:
                self._success_or_forced_fail(response, "attempts")
            elif response.status_code in (400, 403, 404):
                self._success_or_forced_fail(response, "attempts")
            else:
                response.failure(f"Status code: {response.status_code}")

    # -----------------------------
    # API (/api/...) -> inject 40% fails
    # -----------------------------
    @tag("api", "read")
    @task(3)
    def api_get_tasks_by_numbers(self):
        """API: получение задач по номерам КИМ."""
        numbers = random.sample(range(1, 28), k=random.randint(1, 5))
        path = "/api/tasks/by_numbers"

        with self.client.post(
            path,
            json={"numbers": numbers},
            catch_response=True,
            name="POST /api/tasks/by_numbers",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            if response.status_code == 200:
                try:
                    _ = response.json()
                    self._success_or_forced_fail(response, "api")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status code: {response.status_code}")


class AdminUser(KegeProjectUser):
    """Пользователь с правами администратора - открывает админку."""

    def _login(self):
        """Логин под админом."""
        self.user_credentials = {"username": "admin", "password": "admin"}

        payload = {"username": "admin", "password": "admin"}
        if self.csrf_token:
            payload["csrf_token"] = self.csrf_token

        with self.client.post(
            "/login",
            data=payload,
            catch_response=True,
            name="POST /login (admin)",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            if response.status_code in (200, 302):
                self.logged_in = True
                response.success()
            else:
                response.failure(f"Admin login failed: {response.status_code}")

    @tag("admin", "read")
    @task(5)
    def view_admin_panel(self):
        """Просмотр админ-панели."""
        if not self.logged_in:
            return

        with self.client.get(
            "/admin/",
            catch_response=True,
            name="GET /admin/",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 403:
                response.failure("Admin access denied")
            else:
                response.failure(f"Status code: {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Вызывается перед началом теста."""
    print("\n=== Начало нагрузочного тестирования kegeproject ===")
    print(f"Host: {environment.host}")
    print("Убедитесь, что:")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Вызывается после завершения теста."""
    print("\n=== Нагрузочное тестирование завершено ===")
