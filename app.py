from flask import Flask, render_template, request, redirect, url_for, session
from tinydb import TinyDB
import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request
from tinydb import TinyDB, Query


app = Flask(__name__)
app.secret_key = "supersecret"

# --- DB setup ---
db = TinyDB("database.json")
notes_db = db.table("notes")
tests_db = db.table("tests")

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ADMIN_USER = "admin_srinivasan"
ADMIN_PASS = "srini@vasan"


# ---------- HOME ----------
@app.route('/')
def home():
    return render_template('home.html')


# ---------- USER ----------
@app.route('/user_dashboard')
def user_dashboard():
    notes = notes_db.all()
    tests = tests_db.all()
    return render_template('user_dashboard.html', notes=notes, tests=tests)


@app.route('/view_note/<int:note_id>')
def view_note(note_id):
    note = notes_db.get(doc_id=note_id)
    if note:
        notes_db.update({'viewed': True}, doc_ids=[note_id])
        return redirect(f"/static/uploads/{note['file']}")
    return redirect(url_for('user_dashboard'))


@app.route('/attend_test/<int:test_id>')
def attend_test(test_id):
    test = tests_db.get(doc_id=test_id)
    if test:
        tests_db.update({'viewed': True}, doc_ids=[test_id])
        return redirect(test['link'])
    return redirect(url_for('user_dashboard'))


# ---------- ADMIN ----------
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html')


@app.route('/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    notes = notes_db.all()
    tests = tests_db.all()
    total_notes = len(notes)
    total_tests = len(tests)
    viewed_notes = sum(1 for n in notes if n.get('viewed'))
    viewed_tests = sum(1 for t in tests if t.get('viewed'))
    return render_template('admin_dashboard.html',
                           notes=notes, tests=tests,
                           total_notes=total_notes,
                           total_tests=total_tests,
                           viewed_notes=viewed_notes,
                           viewed_tests=viewed_tests)


@app.route('/upload_note', methods=['POST'])
def upload_note():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    file = request.files['file']
    title = request.form['title']
    if file:
        path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(path)
        notes_db.insert({
            'title': title,
            'file': file.filename,
            'viewed': False,
            'date': str(datetime.now())
        })
    return redirect(url_for('admin_dashboard'))


@app.route('/add_test', methods=['POST'])
def add_test():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    title = request.form['title']
    link = request.form['link']
    tests_db.insert({
        'title': title,
        'link': link,
        'viewed': False,
        'date': str(datetime.now())
    })
    return redirect(url_for('admin_dashboard'))


@app.route('/delete_note/<int:note_id>')
def delete_note(note_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    notes_db.remove(doc_ids=[note_id])
    return redirect(url_for('admin_dashboard'))


@app.route('/delete_test/<int:test_id>')
def delete_test(test_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    tests_db.remove(doc_ids=[test_id])
    return redirect(url_for('admin_dashboard'))


@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
