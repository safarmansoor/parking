from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Database setup
DATABASE = 'parking.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        # Create tables
        conn.execute("CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS parking_numbers (id INTEGER PRIMARY KEY, number TEXT, project_id INTEGER, FOREIGN KEY(project_id) REFERENCES projects(id))")
        conn.commit()

# Routes
@app.route('/')
def index():
    with sqlite3.connect(DATABASE) as conn:
        # Fetch projects and their associated parking numbers
        projects = conn.execute("SELECT * FROM projects").fetchall()
        parking_numbers = conn.execute("SELECT parking_numbers.id, parking_numbers.number, projects.name FROM parking_numbers LEFT JOIN projects ON parking_numbers.project_id = projects.id").fetchall()
    return render_template('index.html', projects=projects, parking_numbers=parking_numbers)

@app.route('/add_project', methods=['POST'])
def add_project():
    project_name = request.form.get('project_name')
    if project_name:
        with sqlite3.connect(DATABASE) as conn:
            conn.execute("INSERT INTO projects (name) VALUES (?)", (project_name,))
            conn.commit()
    return redirect(url_for('index'))

@app.route('/add_parking_number', methods=['POST'])
def add_parking_number():
    number = request.form.get('number')
    project_id = request.form.get('project_id')
    if number and project_id:
        with sqlite3.connect(DATABASE) as conn:
            conn.execute("INSERT INTO parking_numbers (number, project_id) VALUES (?, ?)", (number, project_id))
            conn.commit()
    return redirect(url_for('index'))

@app.route('/delete_parking_number/<int:number_id>', methods=['GET'])
def delete_parking_number(number_id):
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("DELETE FROM parking_numbers WHERE id = ?", (number_id,))
        conn.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
