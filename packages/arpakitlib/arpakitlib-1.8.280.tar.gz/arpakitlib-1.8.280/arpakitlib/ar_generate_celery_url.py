from urllib.parse import quote_plus

_ARPAKIT_LIB_MODULE_VERSION = "3.0"


def generate_celery_url(
        *,
        scheme: str = "redis",  # или amqp, sqs, etc.
        user: str | None = None,
        password: str | None = None,
        host: str = "127.0.0.1",
        port: int | None = 6379,
        database: str | int | None = 0,  # для Redis — номер БД; для AMQP — vhost
        **query_params
) -> str:
    """
    Генерирует Celery broker/backend URL.

    Примеры:
      redis://:mypassword@redis:6379/0
      amqp://user:pass@rabbit:5672/myvhost
      redis://localhost:6379/1?ssl_cert_reqs=none
    """
    # Формируем часть авторизации
    auth_part = ""
    if user and password:
        auth_part = f"{quote_plus(user)}:{quote_plus(password)}@"
    elif password and not user:
        # Redis-style — пароль без юзера
        auth_part = f":{quote_plus(password)}@"
    elif user:
        auth_part = f"{quote_plus(user)}@"

    # Формируем хост и порт
    host_part = host
    if port:
        host_part += f":{port}"

    # Формируем "базу" (для Redis — номер, для AMQP — vhost)
    db_part = ""
    if database is not None:
        db_part = f"/{quote_plus(str(database))}"

    # Формируем query параметры
    query_part = ""
    if query_params:
        query_items = [f"{key}={quote_plus(str(value))}" for key, value in query_params.items()]
        query_part = f"?{'&'.join(query_items)}"

    return f"{scheme}://{auth_part}{host_part}{db_part}{query_part}"


def __example():
    print(generate_celery_url())
    # → redis://127.0.0.1:6379/0

    # Redis с паролем
    print(generate_celery_url(password="supersecret", host="redis"))
    # → redis://:supersecret@redis:6379/0

    # RabbitMQ (AMQP)
    print(generate_celery_url(scheme="amqp", user="guest", password="guest", host="rabbitmq"))
    # → amqp://guest:guest@rabbitmq:6379/0

    # Redis с параметрами
    print(generate_celery_url(password="pass", ssl_cert_reqs="none", socket_timeout=10))
    # → redis://:pass@127.0.0.1:6379/0?ssl_cert_reqs=none&socket_timeout=10


if __name__ == '__main__':
    __example()
