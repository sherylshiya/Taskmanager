from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os
import urllib.parse

app = Flask(__name__)

# --- DB Config from Service Connector / environment variable ---
# Azure Service Connector injects the full connection string as an environment variable
# Example variable name: POSTGRESQL_CONNECTIONSTRING

DB_CONN_STR = os.environ.get("POSTGRESQL_CONNECTIONSTRING")
if not DB_CONN_STR:
    raise ValueError("POSTGRESQL_CONNECTIONSTRING environment variable not set")

def get_db_connection():
    return psycopg2.connect(DB_CONN_STR)
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

# --- Run App ---
if __name__ == "__main__":
    init_db()  # only runs once when app starts
    app.run(debug=True, host="0.0.0.0", port=5000)
