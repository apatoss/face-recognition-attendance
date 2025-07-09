# Required imports
from flask import Flask, render_template, request, redirect, session, url_for, send_file
import mysql.connector
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for session

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="_Alfath23",
        database="attendancesystem"
    )

def get_attendance(selected_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, day, timestamp, status FROM attendance WHERE DATE(timestamp) = %s ORDER BY timestamp DESC", (selected_date,))
    data = cursor.fetchall()
    conn.close()
    return data

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = %s AND password = %s", (username, password))
        admin = cursor.fetchone()
        conn.close()

        if admin:
            session['admin'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template("login.html", message="Invalid credentials")

    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))

    date_str = request.args.get("date")
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.now().date()
    except:
        selected_date = datetime.now().date()

    attendance_data = get_attendance(selected_date)

    for i, row in enumerate(attendance_data):
        name = row[0]
        image_path = None
        for ext in ['.jpg', '.jpeg', '.png']:
            possible_path = os.path.join('static/faces', name + ext)
            if os.path.exists(possible_path):
                image_path = url_for('static', filename='faces/' + name + ext)
                break
        attendance_data[i] = list(row) + [image_path or '']

    return render_template("index.html", attendance=attendance_data, today=selected_date)

@app.route('/download')
def download():
    return send_file("attendance.csv", as_attachment=True)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'admin' not in session:
        return redirect(url_for('login'))

    message = ""
    if request.method == 'POST':
        name = request.form.get('name')
        image = request.files.get('image')
        if name and image:
            filename = secure_filename(name) + os.path.splitext(image.filename)[-1]

            # Save to both locations
            face_path = os.path.join("faces", filename)
            static_face_path = os.path.join("static", "faces", filename)
            os.makedirs("faces", exist_ok=True)
            os.makedirs("static/faces", exist_ok=True)
            image.save(face_path)
            image.save(static_face_path)

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, image_path) VALUES (%s, %s)", (name, filename))
            conn.commit()
            conn.close()

            message = f"{name} added successfully!"
        else:
            message = "Please fill in both fields."

    return render_template("admin.html", message=message)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)