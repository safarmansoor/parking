from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Database setup
DATABASE = 'numbers.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS numbers (id INTEGER PRIMARY KEY, number TEXT)")
        conn.commit()

# Routes
@app.route('/')
def index():
    with sqlite3.connect(DATABASE) as conn:
        numbers = conn.execute("SELECT * FROM numbers").fetchall()
    return render_template('index.html', numbers=numbers)

@app.route('/add', methods=['POST'])
def add():
    number = request.form.get('number')
    if number:
        with sqlite3.connect(DATABASE) as conn:
            conn.execute("INSERT INTO numbers (number) VALUES (?)", (number,))
            conn.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
import os
app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))