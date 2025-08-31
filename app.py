from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os

app = Flask(__name__)

# Database connection helper
def get_db_connection():
    conn_str = os.environ.get("AZURE_POSTGRESQL_CONNECTIONSTRING")
    try:
        if conn_str:
            conn = psycopg2.connect(conn_str)
        else:
            conn = psycopg2.connect(
                user=os.environ.get("DB_USER"),
                password=os.environ.get("DB_PASS"),
                host=os.environ.get("DB_HOST"),
                port=os.environ.get("DB_PORT"),
                database=os.environ.get("DB_NAME"),
                sslmode='require'
            )
        return conn
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        raise

# Initialize DB (create table if not exists)
def init_db():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        status TEXT NOT NULL
                    );
                ''')
                conn.commit()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")

# Run DB initialization on startup
with app.app_context():
    init_db()

# Routes
@app.route("/")
def index():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, title, status FROM tasks ORDER BY id;")
                tasks = cur.fetchall()
        return render_template("index.html", tasks=tasks)
    except Exception as e:
        return f"Database query failed: {e}", 500

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        title = request.form["title"]
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO tasks (title, status) VALUES (%s, %s);",
                        (title, "Pending")
                    )
                    conn.commit()
            return redirect(url_for("index"))
        except Exception as e:
            return f"Failed to add task: {e}", 500
    return render_template("add_task.html")

@app.route("/update/<int:task_id>", methods=["GET", "POST"])
def update_task(task_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if request.method == "POST":
                    new_title = request.form["title"]
                    cur.execute("UPDATE tasks SET title = %s WHERE id = %s", (new_title, task_id))
                    conn.commit()
                    return redirect(url_for("index"))
                else:
                    cur.execute("SELECT id, title FROM tasks WHERE id = %s", (task_id,))
                    task = cur.fetchone()
        return render_template("update_task.html", task=task)
    except Exception as e:
        return f"Failed to update task: {e}", 500

@app.route("/complete/<int:task_id>")
def complete(task_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE tasks SET status = %s WHERE id = %s;", ("Completed", task_id))
                conn.commit()
        return redirect(url_for("index"))
    except Exception as e:
        return f"Failed to mark task complete: {e}", 500

@app.route("/delete/<int:task_id>")
def delete(task_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
                conn.commit()
        return redirect(url_for("index"))
    except Exception as e:
        return f"Failed to delete task: {e}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
