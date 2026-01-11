import random
import json
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
    "42",  # скаляр
    "123;456",  # вектор для задач 17,18,26
    "7;5;3",  # вектор для задачи 19
    "RED",  # слово
    "5",
]

# --- Инъекция "искусственных" ошибок для статистики ---
FORCED_FAIL_RATE = 0.40  # 40% запросов в указанных группах будут помечены как failed
REQUEST_TIMEOUT_SEC = 15  # таймаут на каждый запрос (connect/read)


class KegeProjectUser(HttpUser):
    """Базовый класс пользователя системы Экзам-ON."""

    wait_time = between(1.0, 3.0)  # пауза между запросами 1-3 секунды

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.csrf_token: Optional[str] = None
        self.user_credentials: Optional[Dict] = None
        self.logged_in = False
        self.current_attempt_id: Optional[int] = None
        self.available_tasks: List[int] = []
        self.available_variants: List[int] = []

    def on_start(self):
        """Инициализация: получаем CSRF токен и логинимся."""
        self._get_csrf_token()
        self._login()

    # -----------------------------
    # Helpers for forced failures
    # -----------------------------
    @staticmethod
    def _should_force_fail() -> bool:
        return random.random() < FORCED_FAIL_RATE

    def _success_or_forced_fail(self, response, group_label: str):
        """
        Помечает запрос как success или (с вероятностью FORCED_FAIL_RATE) как fail,
        при этом запрос фактически уже выполнен и учтен в статистике.
        """
        if self._should_force_fail():
            response.failure(f"Injected failure ({group_label}, {int(FORCED_FAIL_RATE * 100)}%)")
        else:
            response.success()

    def _handle_status_with_optional_forced_fail(
        self,
        response,
        ok_statuses,
        allowed_statuses=None,
        force_fail_group: Optional[str] = None,
    ):
        """
        Унифицированная обработка статуса:
        - ok_statuses: статусы, которые считаются успехом
        - allowed_statuses: статусы, которые допустимы и тоже считаются успехом (например, 403/404)
        - force_fail_group: если задано ("api" или "attempts"), то к успешным/допустимым ответам
          применяется инъекция fail в 40% случаев
        """
        allowed_statuses = allowed_statuses or set()
        ok_statuses = set(ok_statuses)
        allowed_statuses = set(allowed_statuses)

        if response.status_code in ok_statuses or response.status_code in allowed_statuses:
            if force_fail_group:
                self._success_or_forced_fail(response, force_fail_group)
            else:
                response.success()
        else:
            response.failure(f"Status code: {response.status_code}")

    # -----------------------------
    # Auth / CSRF
    # -----------------------------
    def _get_csrf_token(self):
        """Получение CSRF токена с главной страницы."""
        with self.client.get(
            "/",
            catch_response=True,
            name="GET /",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            if response.status_code == 200:
                # Попытка извлечь CSRF токен из куки или мета-тега
                if "csrf_token" in response.cookies:
                    self.csrf_token = response.cookies["csrf_token"]
                response.success()
            else:
                response.failure(f"Failed to get CSRF token: {response.status_code}")

    def _login(self):
        """Аутентификация пользователя."""
        self.user_credentials = random.choice(TEST_USERS)

        with self.client.post(
            "/login",
            data={
                "username": self.user_credentials["username"],
                "password": self.user_credentials["password"],
            },
            catch_response=True,
            name="POST /login",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            if response.status_code in (200, 302):  # 302 = redirect после успешного логина
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
            self._handle_status_with_optional_forced_fail(
                response,
                ok_statuses={200},
            )

    @tag("public", "read")
    @task(8)
    def view_tasks_list(self):
        """Просмотр списка всех задач."""
        with self.client.get(
            "/tasks",
            catch_response=True,
            name="GET /tasks",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            self._handle_status_with_optional_forced_fail(
                response,
                ok_statuses={200},
            )

    @tag("public", "read")
    @task(5)
    def view_single_task(self):
        """Просмотр конкретной задачи по ID."""
        task_id = random.randint(1, 400)  # предполагаем 400 задач из seed
        with self.client.get(
            f"/tasks/view/{task_id}",
            catch_response=True,
            name="GET /tasks/view/<id>",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            # 404 допускается, как и было
            self._handle_status_with_optional_forced_fail(
                response,
                ok_statuses={200},
                allowed_statuses={404},
            )

    @tag("public", "read")
    @task(7)
    def view_variants_list(self):
        """Просмотр списка вариантов."""
        with self.client.get(
            "/variants",
            catch_response=True,
            name="GET /variants",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            self._handle_status_with_optional_forced_fail(
                response,
                ok_statuses={200},
            )

    @tag("public", "read")
    @task(4)
    def view_variant_details(self):
        """Просмотр деталей варианта."""
        variant_id = random.randint(1, 150)  # предполагаем 150 вариантов из seed
        with self.client.get(
            f"/variants/view/{variant_id}",
            catch_response=True,
            name="GET /variants/view/<id>",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            # 404 допускается, как и было
            self._handle_status_with_optional_forced_fail(
                response,
                ok_statuses={200},
                allowed_statuses={404},
            )

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
            self._handle_status_with_optional_forced_fail(
                response,
                ok_statuses={200},
            )

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
            self._handle_status_with_optional_forced_fail(
                response,
                ok_statuses={200},
            )

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
            self._handle_status_with_optional_forced_fail(
                response,
                ok_statuses={200},
            )

    # -----------------------------
    # Exam flows (/attempts...) -> inject 40% fails
    # -----------------------------
    @tag("auth", "exam")
    @task(5)
    def start_exam_attempt(self):
        """Начать попытку прохождения экзамена."""
        if not self.logged_in:
            return

        variant_id = random.randint(1, 150)
        with self.client.post(
            f"/variants/start-exam/{variant_id}",
            catch_response=True,
            name="POST /variants/start-exam/<id>",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            if response.status_code in (200, 302):
                # Попытка извлечь attempt_id из редиректа
                if "Location" in response.headers:
                    location = response.headers["Location"]
                    if "/attempts/" in location:
                        try:
                            self.current_attempt_id = int(location.split("/attempts/")[1].split("/")[0])
                        except (IndexError, ValueError):
                            pass
                response.success()
            elif response.status_code == 404:
                response.success()  # вариант не найден - это OK
            else:
                response.failure(f"Status code: {response.status_code}")

    @tag("auth", "exam")
    @task(3)
    def view_attempt_page(self):
        """Просмотр страницы попытки (интерфейс экзамена)."""
        if not self.logged_in or not self.current_attempt_id:
            # Используем случайный attempt_id для теста
            attempt_id = random.randint(1, 300)
        else:
            attempt_id = self.current_attempt_id

        with self.client.get(
            f"/attempts/{attempt_id}",
            catch_response=True,
            name="GET /attempts/<id>",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            # 200 OK, 403/404 допустимы -> но 40% таких ответов хотим считать "failed"
            self._handle_status_with_optional_forced_fail(
                response,
                ok_statuses={200},
                allowed_statuses={403, 404},
                force_fail_group="attempts",
            )

    @tag("auth", "exam", "ajax")
    @task(4)
    def get_attempt_data(self):
        """Получение данных попытки через AJAX API."""
        if not self.logged_in:
            return

        attempt_id = random.randint(1, 300)
        with self.client.get(
            f"/attempts/{attempt_id}/data",
            catch_response=True,
            name="GET /attempts/<id>/data (AJAX)",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            if response.status_code == 200:
                try:
                    _ = response.json()
                    # Успех, но хотим инъекцию fail 40%
                    self._success_or_forced_fail(response, "attempts")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code in (403, 404):
                # Допустимо, но хотим инъекцию fail 40%
                self._success_or_forced_fail(response, "attempts")
            else:
                response.failure(f"Status code: {response.status_code}")

    @tag("auth", "exam", "ajax", "write")
    @task(2)
    def save_answer(self):
        """Сохранение ответа на задачу через AJAX."""
        if not self.logged_in:
            return

        attempt_id = random.randint(1, 300)
        variant_task_id = random.randint(1, 4050)  # 150 вариантов * 27 задач
        answer_text = random.choice(SAMPLE_ANSWERS)

        with self.client.post(
            f"/attempts/{attempt_id}/save-answer",
            json={"varianttaskid": variant_task_id, "answertext": answer_text},
            catch_response=True,
            name="POST /attempts/<id>/save-answer (AJAX)",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            if response.status_code == 200:
                self._success_or_forced_fail(response, "attempts")
            elif response.status_code in (403, 404):
                self._success_or_forced_fail(response, "attempts")  # не наша попытка - допускаем, но инъектим
            else:
                response.failure(f"Status code: {response.status_code}")

    @tag("auth", "exam", "write")
    @task(1)
    def finish_attempt(self):
        """Завершение попытки экзамена."""
        if not self.logged_in:
            return

        attempt_id = random.randint(1, 300)
        with self.client.post(
            f"/attempts/{attempt_id}/finish",
            catch_response=True,
            name="POST /attempts/<id>/finish",
            timeout=REQUEST_TIMEOUT_SEC,
        ) as response:
            if response.status_code in (200, 302):
                self._success_or_forced_fail(response, "attempts")
            elif response.status_code in (403, 404):
                self._success_or_forced_fail(response, "attempts")
            else:
                response.failure(f"Status code: {response.status_code}")

    # -----------------------------
    # API (/api/...) -> inject 40% fails
    # -----------------------------
    @tag("api", "read")
    @task(3)
    def api_get_tasks_by_numbers(self):
        """API: получение задач по номерам."""
        numbers = random.sample(range(1, 28), k=random.randint(1, 5))
        with self.client.post(
            "/api/tasks/by-numbers",
            json={"numbers": numbers},
            catch_response=True,
            name="POST /api/tasks/by-numbers",
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
            self._handle_status_with_optional_forced_fail(
                response,
                ok_statuses={200},
            )


class AdminUser(KegeProjectUser):
    """Пользователь с правами администратора - создает и редактирует задачи."""

    def _login(self):
        """Логин под админом."""
        self.user_credentials = {"username": "admin", "password": "admin"}

        with self.client.post(
            "/login",
            data={
                "username": self.user_credentials["username"],
                "password": self.user_credentials["password"],
            },
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
            # Это НЕ /api и НЕ /attempts, поэтому здесь инъекцию не делаем
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
