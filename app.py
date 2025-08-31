from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os

app = Flask(__name__)

# --- DB Config from environment variables (set in Azure) ---
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "taskdb")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "password")
DB_PORT = os.environ.get("DB_PORT", "5432")  # default PostgreSQL port

# --- Helper: Get DB connection ---
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        sslmode="require"  # Azure requires SSL
    )
    return conn

# --- Initialize DB (create table if not exists) ---
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT NOT NULL
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

# --- Run DB initialization immediately ---
init_db()

# --- Routes ---
@app.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, status FROM tasks ORDER BY id;")
    tasks = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", tasks=tasks)

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        title = request.form["title"]
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO tasks (title, status) VALUES (%s, %s);", (title, "Pending"))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("index"))
    return render_template("add_task.html")

@app.route("/update/<int:task_id>", methods=["GET", "POST"])
def update_task(task_id):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == "POST":
        new_title = request.form["title"]
        cur.execute("UPDATE tasks SET title = %s WHERE id = %s", (new_title, task_id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for("index"))
    else:
        cur.execute("SELECT id, title FROM tasks WHERE id = %s", (task_id,))
        task = cur.fetchone()
        cur.close()
        conn.close()
        return render_template("update_task.html", task=task)

@app.route("/complete/<int:task_id>")
def complete(task_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET status = %s WHERE id = %s;", ("Completed", task_id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>")
def delete(task_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("index"))

# --- Run App locally ---
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
