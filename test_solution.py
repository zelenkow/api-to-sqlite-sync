import sqlite3

import httpx
import pytest

from solution import (
    fetch,
    get_three_top_users,
    init_db,
    save_to_db,
)


def test_init_db_creates_tables():
    """
    Проверяет, что init_db создаёт таблицы users и posts.
    """
    with sqlite3.connect(":memory:") as conn:
        init_db(conn)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "users" in tables
        assert "posts" in tables


def test_save_to_db_inserts_data():
    """
    Проверяет, что save_to_db сохраняет всех пользователей и посты.
    """
    users = [
        {"id": 1, "name": "Иван"},
        {"id": 2, "name": "Мария"},
    ]
    posts = [
        {"id": 1, "userId": 1, "title": "Пост 1", "body": "Текст"},
        {"id": 2, "userId": 1, "title": "Пост 2", "body": "Текст"},
        {"id": 3, "userId": 2, "title": "Пост 3", "body": "Текст"},
    ]

    with sqlite3.connect(":memory:") as conn:
        init_db(conn)
        save_to_db(conn, users, posts)

        users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        posts_count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]

        assert users_count == 2
        assert posts_count == 3


def test_save_to_db_is_idempotent():
    """
    Проверяет, что повторный вызов save_to_db не создаёт дубликаты.
    """
    users = [{"id": 1, "name": "Иван"}]
    posts = [{"id": 1, "userId": 1, "title": "Пост", "body": "Текст"}]

    with sqlite3.connect(":memory:") as conn:
        init_db(conn)
        save_to_db(conn, users, posts)
        save_to_db(conn, users, posts)

        users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        posts_count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]

        assert users_count == 1
        assert posts_count == 1


def test_get_three_top_users(capsys):
    """
    Проверяет, что get_three_top_users выводит топ-3 по количеству постов.
    """
    users = [
        {"id": 1, "name": "Иван"},
        {"id": 2, "name": "Мария"},
        {"id": 3, "name": "Петр"},
        {"id": 4, "name": "Анна"},
    ]
    posts = [
        {"id": 1, "userId": 1, "title": "", "body": ""},
        {"id": 2, "userId": 1, "title": "", "body": ""},
        {"id": 3, "userId": 1, "title": "", "body": ""},
        {"id": 4, "userId": 2, "title": "", "body": ""},
        {"id": 5, "userId": 2, "title": "", "body": ""},
        {"id": 6, "userId": 3, "title": "", "body": ""},
        {"id": 7, "userId": 4, "title": "", "body": ""},
    ]

    with sqlite3.connect(":memory:") as conn:
        init_db(conn)
        save_to_db(conn, users, posts)
        get_three_top_users(conn)

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")

    assert len(lines) == 3
    assert lines[0] == "Иван: 3 posts"
    assert lines[1] == "Мария: 2 posts"


def test_fetch_success(mocker):
    """
    Проверяет, что fetch возвращает данные при успешном запросе.
    """
    mock_response = mocker.Mock()
    mock_response.json.return_value = [{"id": 1, "name": "Test"}]
    mock_response.raise_for_status.return_value = None
    mocker.patch("httpx.get", return_value=mock_response)

    result = fetch("https://example.com/users")

    assert result == [{"id": 1, "name": "Test"}]


def test_fetch_http_error(mocker):
    """
    Проверяет, что fetch завершает программу при ошибке HTTP.
    """
    mocker.patch("httpx.get", side_effect=httpx.HTTPError("connection failed"))

    with pytest.raises(SystemExit) as exc_info:
        fetch("https://example.com/users")

    assert exc_info.value.code == 1
