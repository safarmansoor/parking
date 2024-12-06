import os
from flask import Flask, render_template, request, redirect, url_for, flash
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canv
import sqlite3
import csv

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DATABASE = 'parking.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("CREATE TABLE IF NOT EXISTS parking_numbers (id INTEGER PRIMARY KEY, number TEXT, project_id INTEGER, FOREIGN KEY(project_id) REFERENCES projects(id))")
        conn.commit()

@app.route('/')

def index():
    with sqlite3.connect(DATABASE) as conn:
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

# Route to handle bulk project upload
@app.route('/bulk_projects', methods=['POST'])
def bulk_projects():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        with sqlite3.connect(DATABASE) as conn:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    # Avoid duplicate projects
                    conn.execute("""
                        INSERT INTO projects (name) 
                        SELECT ? WHERE NOT EXISTS 
                        (SELECT 1 FROM projects WHERE name = ?)""", (row[0], row[0]))
            conn.commit()
        os.remove(file_path)
        flash('Bulk projects added successfully!')
    return redirect(url_for('index'))

# Route to handle bulk parking number upload
@app.route('/bulk_parking_numbers', methods=['POST'])
def bulk_parking_numbers():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        with sqlite3.connect(DATABASE) as conn:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    # Validate project_id and avoid duplicate parking numbers
                    project_exists = conn.execute("SELECT 1 FROM projects WHERE id = ?", (row[1],)).fetchone()
                    if project_exists:
                        conn.execute("""
                            INSERT INTO parking_numbers (number, project_id)
                            SELECT ?, ? WHERE NOT EXISTS 
                            (SELECT 1 FROM parking_numbers WHERE number = ?)""", (row[0], row[1], row[0]))
            conn.commit()
        os.remove(file_path)
        flash('Bulk parking numbers added successfully!')
    return redirect(url_for('index'))

@app.route('/generate_pdf', methods=['GET'])
def generate_pdf():
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'parking_numbers.pdf')
    
    with sqlite3.connect(DATABASE) as conn:
        # Fetch parking numbers grouped by project
        projects = conn.execute("""
            SELECT projects.name, GROUP_CONCAT(parking_numbers.number, ', ') as parking_numbers
            FROM projects
            LEFT JOIN parking_numbers ON projects.id = parking_numbers.project_id
            GROUP BY projects.id
        """).fetchall()

    # Create PDF
    pdf = canvas.Canvas(file_path, pagesize=landscape(A4))
    pdf.setFont("Helvetica", 12)

    x, y = 50, 550  # Initial coordinates
    for project_name, parking_numbers in projects:
        pdf.drawString(x, y, f"Project: {project_name}")
        y -= 20

        # Split parking numbers into multiple lines if too long
        if parking_numbers:
            numbers = parking_numbers.split(", ")
            lines = [", ".join(numbers[i:i + 10]) for i in range(0, len(numbers), 10)]
            for line in lines:
                pdf.drawString(x + 20, y, line)
                y -= 20
        else:
            pdf.drawString(x + 20, y, "No parking numbers")
            y -= 20

        y -= 10  # Space between projects
        if y < 50:  # Start new page if space runs out
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y = 550

    pdf.save()

    return redirect(f'/static/uploads/parking_numbers.pdf')


if __name__ == '__main__':
    init_db()
import os
app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))