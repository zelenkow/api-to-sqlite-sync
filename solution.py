import sqlite3
import sys

import httpx

USERS_URL = "https://jsonplaceholder.typicode.com/users"
POSTS_URL = "https://jsonplaceholder.typicode.com/posts"

USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
"""

POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title TEXT,
    body TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


def init_db(conn):
    cursor = conn.cursor()
    cursor.executescript(USERS_TABLE)
    cursor.executescript(POSTS_TABLE)


def fetch(url, timeout=10):
    try:
        r = httpx.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        print(f"Ошибка при запросе {url}: {e}")
        sys.exit(1)


def save_to_db(conn, users, posts):
    with conn:
        cursor = conn.cursor()
        for user in users:
            cursor.execute(
                "INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (user["id"], user["name"])
            )
        for post in posts:
            cursor.execute(
                "INSERT OR IGNORE INTO posts (id, user_id, title, body) VALUES (?, ?, ?, ?)",
                (post["id"], post["userId"], post["title"], post["body"]),
            )


def get_three_top_users(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT users.name, COUNT(posts.id) AS post_count
        FROM users
        JOIN posts ON posts.user_id = users.id
        GROUP BY users.id, users.name
        ORDER BY post_count DESC
        LIMIT 3
""")
    rows = cursor.fetchall()
    for name, count in rows:
        print(f"{name}: {count} posts")


def main():
    with sqlite3.connect("app.db") as conn:
        init_db(conn)
        users = fetch(USERS_URL)
        posts = fetch(POSTS_URL)
        save_to_db(conn, users, posts)
        get_three_top_users(conn)


if __name__ == "__main__":
    main()
