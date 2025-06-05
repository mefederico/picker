import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

PSQL_URL = os.getenv('DATABASE_URL')

class DatabaseManager:
    def __init__(self):
        self.conn = psycopg2.connect(PSQL_URL, cursor_factory=RealDictCursor)

    def close(self):
        self.conn.close()

    # --- Pull Requests ---
    def create_pull_request(self, channel, link, reviewers, asked, thread):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pull_requests (channel, link, reviewers, asked, thread)
                VALUES (%s, %s, %s, %s, %s) RETURNING id;
                """,
                (channel, link, reviewers, asked, thread)
            )
            self.conn.commit()
            return cur.fetchone()['id']

    def get_pull_request(self, pr_id):
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM pull_requests WHERE id = %s;", (pr_id,))
            return cur.fetchone()

    def list_pull_requests(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM pull_requests;")
            return cur.fetchall()

    # --- Reviewers ---
    def add_reviewer(self, pull_request, user_id):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO reviewers (pull_request, user_id) VALUES (%s, %s) RETURNING id;",
                (pull_request, user_id)
            )
            self.conn.commit()
            return cur.fetchone()['id']

    def get_reviewers_for_pr(self, pull_request):
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM reviewers WHERE pull_request = %s;", (pull_request,))
            return cur.fetchall()

    # --- Users ---
    def create_user(self, slack_id, until, available, channel):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (slack_id, until, available, channel) VALUES (%s, %s, %s, %s) RETURNING id;",
                (slack_id, until, available, channel)
            )
            self.conn.commit()
            return cur.fetchone()['id']

    def get_user_by_slack_id(self, slack_id):
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE slack_id = %s;", (slack_id,))
            return cur.fetchone()

    def update_user_availability(self, slack_id, until, available):
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET until = %s, available = %s WHERE slack_id = %s;",
                (until, available, slack_id)
            )
            self.conn.commit()

    def list_users(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM users;")
            return cur.fetchall() 