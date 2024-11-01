from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
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

    search_query = request.args.get('search', '')
    if search_query:
        search_terms = search_query.lower().split()
        filtered_data = excel_data[
            excel_data.apply(lambda row: all(term in row['First Name'].lower() or term in row['Last Name'].lower() for term in search_terms), axis=1)
        ]
    else:
        filtered_data = excel_data

    headers = filtered_data.columns.tolist()
    rows = filtered_data.values.tolist()

    total_received = (excel_data['Received'] == 'Yes').sum() if 'Received' in excel_data.columns else 0

    return render_template('view.html', headers=headers, rows=rows, search_query=search_query, total_received=total_received)

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    global excel_data
    if excel_data is None or excel_data.empty:
        return jsonify([])

    search_query = request.args.get('query', '').lower()
    search_terms = search_query.split()

    # Ensure columns exist to avoid KeyError
    if 'First Name' not in excel_data.columns or 'Last Name' not in excel_data.columns:
        return jsonify([])

    # Convert columns to lowercase for case-insensitive matching
    excel_data['First Name'] = excel_data['First Name'].astype(str).str.lower()
    excel_data['Last Name'] = excel_data['Last Name'].astype(str).str.lower()

    # Find matching names using vectorized operations
    matching_names = excel_data[
        excel_data.apply(lambda row: all(term in row['First Name'] or term in row['Last Name'] for term in search_terms), axis=1)
    ]

    # Create full names with Last Name first and return them as a list
    names = (matching_names['Last Name'] + ' ' + matching_names['First Name']).tolist()

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
