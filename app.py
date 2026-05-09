from flask import Flask, render_template, request, redirect, session, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'secretkey'
CORS(app) 

# MYSQL CONFIGURATION
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'medivault_user'
app.config['MYSQL_PASSWORD'] = 'medipass123'
app.config['MYSQL_DB'] = 'medivault'

mysql = MySQL(app)

# =========================
# LOGIN PAGE
# =========================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        cur = mysql.connection.cursor()
        # Only search by email
        cur.execute("SELECT id, full_name, password FROM doctors WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        # check_password_hash compares the input with the scrambled version
        if user and check_password_hash(user[2], password):
            session['doctor_id'] = user[0]
            session['doctor_name'] = user[1]
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid Email or Password")
            
    return render_template('login.html')

# =========================
# REGISTER PAGE (Rendering the page)
# =========================
@app.route('/register')
def register_page():
    return render_template('register.html')

# =========================
# REGISTER API (Handling the JavaScript Fetch)
# =========================
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    
    # 1. Pull all fields from the JSON request
    id_no = data.get('id_no')  
    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')

    # 2. Hash the password for security
    hashed_pw = generate_password_hash(password)

    cur = mysql.connection.cursor()
    try:
        # 3. Include id_no in the columns and the values
        cur.execute("INSERT INTO doctors (id_no, full_name, email, password) VALUES (%s, %s, %s, %s)", 
                    (id_no, full_name, email, hashed_pw))
        mysql.connection.commit()
        return jsonify({"success": True, "message": "Registration successful!"})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "message": "Database error"}), 500
    finally:
        cur.close()

# =========================
# DASHBOARD
# =========================
@app.route('/dashboard')
def dashboard():
    if 'doctor_id' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()
    
    # FIX: Added bp_diastolic and heart_rate. 
    # Note the new positions: name[0], bp_sys[1], bp_dia[2], hr[3], sugar[4], bmi[5], spo2[6], p.id[7], notes[8]
    cur.execute("""
        SELECT p.patient_name, v.bp_systolic, v.bp_diastolic, v.heart_rate, 
               v.blood_sugar, v.bmi, v.spo2, p.id, v.notes 
        FROM vitals v 
        JOIN patients p ON v.patient_id = p.id 
        WHERE p.doctor_id = %s
        ORDER BY v.created_at DESC
    """, (session['doctor_id'],))
    records = cur.fetchall()

    # 2. Total unique patients
    cur.execute("SELECT COUNT(DISTINCT id) FROM patients WHERE doctor_id = %s", (session['doctor_id'],))
    total_patients = cur.fetchone()[0]

    # 3. Critical Patients
    cur.execute("""
        SELECT COUNT(DISTINCT p.id) 
        FROM patients p 
        JOIN vitals v ON p.id = v.patient_id 
        WHERE p.doctor_id = %s AND (v.spo2 < 95 OR v.blood_sugar > 140)
    """, (session['doctor_id'],))
    critical_count = cur.fetchone()[0]

    # 4. Today's Checkups
    cur.execute("""
        SELECT COUNT(*) FROM vitals v 
        JOIN patients p ON v.patient_id = p.id 
        WHERE p.doctor_id = %s AND DATE(v.created_at) = CURDATE()
    """, (session['doctor_id'],))
    today_count = cur.fetchone()[0]

    cur.close()
    
    return render_template('dashboard.html', 
                           records=records, 
                           total=total_patients, 
                           critical=critical_count, 
                           today=today_count,
                           name=session.get('doctor_name'))
# =========================
# ADD PATIENT
# =========================
@app.route('/add_patient', methods=['POST'])
def add_patient():
    if 'doctor_id' not in session:
        return redirect('/')

    # 1. Grab raw data from HTML input 'name' attributes
    name = request.form.get('patient_name')
    bp_sys = request.form.get('blood_pressure') # Systolic (Upper)
    bp_dia = request.form.get('bp_diastolic')   # Diastolic (Lower)
    h_rate = request.form.get('heart_rate')     # Heart Rate
    gender = request.form.get('gender') 
    notes = request.form.get('notes')
    
    # 2. Sanitize and Convert numbers safely (prevents crashes from invalid text)
    try:
        # age should be an int
        age_raw = request.form.get('age')
        age = int(age_raw) if age_raw and age_raw.strip() else 0
        
        # sugar should be an int
        sugar_raw = request.form.get('blood_sugar')
        sugar = int(sugar_raw) if sugar_raw and sugar_raw.strip() else 0
        
        # bmi must be a float (decimal)
        bmi_raw = request.form.get('bmi')
        bmi = float(bmi_raw) if bmi_raw and bmi_raw.strip() else 0.0
        
        # spo2 should be an int
        spo2_raw = request.form.get('spo2')
        spo2 = int(spo2_raw) if spo2_raw and spo2_raw.strip() else 0
        
        # Validation Check (keeps data realistic)
        if age < 0 or age > 150 or sugar > 999 or spo2 > 100:
            return "Error: Health metrics are out of realistic range.", 400
            
    except ValueError:
        # This handles cases where user types letters in a number box
        return "Error: Please enter valid numbers for Age, Sugar, BMI, and SpO2.", 400

    cur = mysql.connection.cursor()
    
    # 3. Patient Check/Creation logic (this part was already working)
    cur.execute("SELECT id FROM patients WHERE patient_name = %s AND doctor_id = %s", 
                (name, session['doctor_id']))
    patient = cur.fetchone()

    if not patient:
        cur.execute("INSERT INTO patients (patient_name, doctor_id) VALUES (%s, %s)", 
                    (name, session['doctor_id']))
        mysql.connection.commit()
        patient_id = cur.lastrowid
    else:
        patient_id = patient[0]

    # 4. THE CRITICAL FIX: The complete INSERT statement
    # The number of %s parameters MUST match the number of columns you listed.
    cur.execute("""
        INSERT INTO vitals (patient_id, bp_systolic, bp_diastolic, heart_rate, blood_sugar, bmi, spo2, age, gender, notes) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (patient_id, bp_sys, bp_dia, h_rate, sugar, bmi, spo2, age, gender, notes)) 
    
    mysql.connection.commit()
    cur.close()
    return redirect('/dashboard')

# =========================
# SEARCH PATIENT
# =========================
@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    cur = mysql.connection.cursor()
    
    # Updated to include bp_diastolic and heart_rate
    cur.execute("""
        SELECT p.patient_name, v.bp_systolic, v.bp_diastolic, v.heart_rate, 
               v.blood_sugar, v.bmi, v.spo2, v.notes, p.id
        FROM patients p
        JOIN vitals v ON p.id = v.patient_id
        WHERE p.patient_name LIKE %s AND p.doctor_id = %s
    """, (f"%{query}%", session['doctor_id']))
    
    results = cur.fetchall()
    
    # Map them to dictionary keys for the JavaScript
    data = []
    for r in results:
        data.append({
            'patient_name': r[0],
            'bp_systolic': r[1],
            'bp_diastolic': r[2],
            'heart_rate': r[3],
            'blood_sugar': r[4],
            'bmi': str(r[5]),
            'spo2': r[6],
            'notes': r[7],
            'id': r[8]
        })
    return jsonify(data)

# =========================
# ONE PATIENT IF CLICKED
# =========================
@app.route('/patient/<int:patient_id>')
def patient_history(patient_id):
    if 'doctor_id' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()
    # 1. Verify patient
    cur.execute("SELECT patient_name FROM patients WHERE id = %s AND doctor_id = %s", 
                (patient_id, session['doctor_id']))
    patient = cur.fetchone()

    if not patient:
        cur.close()
        return "Patient not found", 404

    # 2. Fetch vitals with ALL columns
    # Order: 0:date, 1:sys, 2:sugar, 3:bmi, 4:spo2, 5:notes, 6:age, 7:gender, 8:dia, 9:hr, 10:id
    cur.execute("""
        SELECT created_at, bp_systolic, blood_sugar, bmi, spo2, notes, age, gender, bp_diastolic, heart_rate, id 
        FROM vitals 
        WHERE patient_id = %s 
        ORDER BY created_at DESC
    """, (patient_id,))

    history = cur.fetchall()
    cur.close()
    return render_template('history.html', patient_name=patient[0], history=history)

# =========================
# DELETE RECORD
# =========================
@app.route('/delete_patient/<int:patient_id>')
def delete_patient(patient_id):
    if 'doctor_id' not in session: 
        return redirect('/')

    cur = mysql.connection.cursor()
    # Delete vitals first because of foreign key constraints
    cur.execute("DELETE FROM vitals WHERE patient_id = %s", (patient_id,))
    # Then delete the patient
    cur.execute("DELETE FROM patients WHERE id = %s AND doctor_id = %s", (patient_id, session['doctor_id']))
    
    mysql.connection.commit()
    cur.close()
    return redirect('/dashboard')

# =========================
# UPDATE RECORD (POST)
# =========================
@app.route('/update_history/<int:vitals_id>', methods=['POST'])
def update_history(vitals_id):
    if 'doctor_id' not in session:
        return redirect('/')

    # Get all fields including the new ones
    age = request.form.get('age')
    gender = request.form.get('gender')
    bp_sys = request.form.get('bp_systolic')
    bp_dia = request.form.get('bp_diastolic')
    h_rate = request.form.get('heart_rate')
    sugar = request.form.get('sugar')
    bmi = request.form.get('bmi')
    spo2 = request.form.get('spo2')
    notes = request.form.get('notes')

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE vitals 
        SET age=%s, gender=%s, bp_systolic=%s, bp_diastolic=%s, heart_rate=%s, 
            blood_sugar=%s, bmi=%s, spo2=%s, notes=%s 
        WHERE id = %s
    """, (age, gender, bp_sys, bp_dia, h_rate, sugar, bmi, spo2, notes, vitals_id))
    
    mysql.connection.commit()
    cur.close()
    return redirect(request.referrer)
# =========================
# CREDITS
# =========================
@app.route('/credits')
def credits():
    if 'doctor_id' not in session:
        return redirect('/')
    return render_template('credits.html')

# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():
    session.clear() # Clears the doctor_id and doctor_name
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

