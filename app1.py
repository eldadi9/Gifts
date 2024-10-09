from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
import pandas as pd
import os
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'xlsx'}

# פונקציה לבדיקת סוג הקובץ
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # שמירת הנתונים ב-Session
        session['filepath'] = filepath
        return redirect(url_for('view_data'))
    flash('Invalid file format. Please upload an Excel file.')
    return redirect(url_for('index'))

@app.route('/view')
def view_data():
    filepath = session.get('filepath')
    if not filepath or not os.path.exists(filepath):
        flash('No file uploaded.')
        return redirect(url_for('index'))

    excel_data = pd.read_excel(filepath)
    
    search_query = request.args.get('search', '').lower()
    filtered_data = excel_data[
        excel_data.apply(lambda row: search_query in row.astype(str).str.lower().values, axis=1)
    ] if search_query else excel_data

    headers = filtered_data.columns.tolist()
    rows = filtered_data.values.tolist()
    
    return render_template('view.html', headers=headers, rows=rows, search_query=search_query)

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    filepath = session.get('filepath')
    if not filepath or not os.path.exists(filepath):
        return jsonify([])

    excel_data = pd.read_excel(filepath)
    search_query = request.args.get('query', '').lower()

    matching_names = excel_data[
        excel_data.apply(lambda row: search_query in row['First Name'].lower() or search_query in row['Last Name'].lower(), axis=1)
    ]

    names = matching_names.apply(lambda row: f"{row['First Name']} {row['Last Name']}", axis=1).tolist()
    return jsonify(names)

@app.route('/mark_received', methods=['POST'])
def mark_received():
    filepath = session.get('filepath')
    if not filepath or not os.path.exists(filepath):
        flash('No file uploaded.')
        return redirect(url_for('index'))
    
    # קריאת הנתונים
    excel_data = pd.read_excel(filepath)
    row_index = int(request.form['row_index'])
    if 'Received' not in excel_data.columns:
        excel_data['Received'] = ''
        
    if excel_data.at[row_index, 'Received'] == 'Yes':
        flash(f"Error: {excel_data.iloc[row_index]['First Name']} {excel_data.iloc[row_index]['Last Name']} already received a gift.")
    else:
        excel_data.at[row_index, 'Received'] = 'Yes'

        # שמירת גיבוי של הקובץ הקיים
        backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        backup_filepath = os.path.join(app.config['UPLOAD_FOLDER'], backup_filename)
        shutil.copy(filepath, backup_filepath)

        # שמירת הקובץ עם השינויים
        excel_data.to_excel(filepath, index=False)
        flash(f"{excel_data.iloc[row_index]['First Name']} {excel_data.iloc[row_index]['Last Name']} marked as received. Backup saved as {backup_filename}.")
    
    return redirect(url_for('view_data'))

@app.route('/save', methods=['POST'])
def save_file():
    filepath = session.get('filepath')
    if not filepath or not os.path.exists(filepath):
        flash('No file to save.')
        return redirect(url_for('index'))

    save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'updated_gift_list.xlsx')
    pd.read_excel(filepath).to_excel(save_path, index=False)
    flash('File saved successfully.')
    return send_file(save_path, as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)