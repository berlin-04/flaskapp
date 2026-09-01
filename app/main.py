from flask import Flask, jsonify
from datetime import datetime
import os
import psycopg2
import redis

app = Flask(__name__)

redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

def get_db_connection():
    return psycopg2.connect(
        host="postgres-db",
        database="flaskdb",
        user="flaskuser",
        password="flaskpass"
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id SERIAL PRIMARY KEY,
            visited_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def get_visit_count():
    cached = redis_client.get("visit_count")
    if cached is not None:
        return int(cached), True

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM visits")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()

    redis_client.setex("visit_count", 10, count)
    return count, False

@app.route("/")
def home():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO visits DEFAULT VALUES")
    conn.commit()
    cur.close()
    conn.close()

    redis_client.delete("visit_count")
    count, from_cache = get_visit_count()

    return jsonify({
        "message": "Hello depuis Docker sur Kali !",
        "visits": count,
        "from_cache": from_cache,
        "time": datetime.now().isoformat(),
        "hostname": os.uname().nodename
    })

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

