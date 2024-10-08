from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# משתנה גלובלי לשמירת האקסל
excel_data = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global excel_data
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and file.filename.endswith('.xlsx'):
        # בדיקת קיומה של התיקייה 'uploads' ויצירתה במידת הצורך
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        excel_data = pd.read_excel(filepath)
        return redirect(url_for('view_data'))
    flash('Invalid file format. Please upload an Excel file.')
    return redirect(url_for('index'))


@app.route('/view')
def view_data():
    global excel_data
    if excel_data is None:
        flash('No file uploaded.')
        return redirect(url_for('index'))
    
    # קבלת מחרוזת החיפוש מה-URL
    search_query = request.args.get('search', '')

    # סינון הנתונים לפי החיפוש
    filtered_data = excel_data[
        excel_data.apply(lambda row: search_query.lower() in row.astype(str).str.lower().values, axis=1)
    ] if search_query else excel_data

    headers = filtered_data.columns.tolist()
    rows = filtered_data.values.tolist()
    
    return render_template('view.html', headers=headers, rows=rows, search_query=search_query)

# נתיב AJAX לחיפוש שמות תוך כדי הקלדה
@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    global excel_data
    if excel_data is None:
        return jsonify([])

    search_query = request.args.get('query', '').lower()

    # מציאת שמות תואמים לפי שם פרטי או משפחה
    matching_names = excel_data[
        excel_data.apply(lambda row: search_query in row['First Name'].lower() or search_query in row['Last Name'].lower(), axis=1)
    ]

    # מחזירים את השמות התואמים ברשימה
    names = matching_names.apply(lambda row: f"{row['First Name']} {row['Last Name']}", axis=1).tolist()

    return jsonify(names)

@app.route('/mark_received', methods=['POST'])
def mark_received():
    global excel_data
    if excel_data is None:
        flash('No file uploaded.')
        return redirect(url_for('index'))
    
    row_index = int(request.form['row_index'])
    if 'Received' not in excel_data.columns:
        excel_data['Received'] = ''
        
    if excel_data.at[row_index, 'Received'] == 'Yes':
        flash(f"Error: {excel_data.iloc[row_index]['First Name']} {excel_data.iloc[row_index]['Last Name']} already received a gift.")
    else:
        excel_data.at[row_index, 'Received'] = 'Yes'
        flash(f"{excel_data.iloc[row_index]['First Name']} {excel_data.iloc[row_index]['Last Name']} marked as received.")
    
    return redirect(url_for('view_data'))

@app.route('/save', methods=['POST'])
def save_file():
    global excel_data
    if excel_data is None:
        flash('No file to save.')
        return redirect(url_for('index'))
    
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'updated_gift_list.xlsx')
    excel_data.to_excel(save_path, index=False)
    flash('File saved successfully.')
    return send_file(save_path, as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
