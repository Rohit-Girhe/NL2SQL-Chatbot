import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = "clinic.db"

def create_tables():
    # Connect to the SQLite database (this creates the file if it doesn't exist)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Patients Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        date_of_birth DATE,
        gender TEXT,
        city TEXT,
        registered_date DATE
    )
    ''')

    # 2. Doctors Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialization TEXT,
        department TEXT,
        phone TEXT
    )
    ''')

    # 3. Appointments Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        appointment_date DATETIME,
        status TEXT,
        notes TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    )
    ''')
    
    # 4. Treatments Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS treatments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER,
        treatment_name TEXT,
        cost REAL,
        duration_minutes INTEGER,
        FOREIGN KEY (appointment_id) REFERENCES appointments(id)
    )
    ''')
    
    # 5. Invoices Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        invoice_date DATE,
        total_amount REAL,
        paid_amount REAL,
        status TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )
    ''')

    # Save changes and close the connection
    conn.commit()
    conn.close()
    print("Database schema created successfully.")

def insert_dummy_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM doctors")
    if cursor.fetchone()[0] > 0:
        print("Database already seeded!")
        return

    print("Seeding database with dummy data...")

    first_names = ["John", "Emma", "Liam", "Olivia", "Noah", "Ava", "William", "Sophia", "James", "Isabella", "Rohit", "Manisha"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Girhe", "Patil"]
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "Pune"]
    specializations = ["Dermatology", "Cardiology", "Orthopedics", "General", "Pediatrics"]
    
    # 1. Insert 15 Doctors
    doctor_ids = []
    for _ in range(15):
        name = f"Dr. {random.choice(first_names)} {random.choice(last_names)}"
        spec = random.choice(specializations)
        dept = f"{spec} Dept"
        phone = f"555-{random.randint(1000, 9999)}"
        cursor.execute('INSERT INTO doctors (name, specialization, department, phone) VALUES (?, ?, ?, ?)', (name, spec, dept, phone))
        doctor_ids.append(cursor.lastrowid)

    # 2. Insert 200 Patients
    patient_ids = []
    for _ in range(200):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        email = f"{fname.lower()}.{lname.lower()}{random.randint(1,99)}@example.com" if random.random() > 0.1 else None # 10% chance of NULL email
        phone = f"555-{random.randint(1000, 9999)}" if random.random() > 0.1 else None # 10% chance of NULL phone
        dob = (datetime.now() - timedelta(days=random.randint(18*365, 80*365))).strftime('%Y-%m-%d')
        gender = random.choice(['M', 'F'])
        city = random.choice(cities)
        reg_date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT INTO patients (first_name, last_name, email, phone, date_of_birth, gender, city, registered_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (fname, lname, email, phone, dob, gender, city, reg_date))
        patient_ids.append(cursor.lastrowid)

    # 3. Insert 500 Appointments
    appointment_ids = []
    statuses = ["Scheduled", "Completed", "Completed", "Completed", "Cancelled", "No-Show"]
    for _ in range(500):
        p_id = random.choice(patient_ids)
        d_id = random.choice(doctor_ids)
        appt_date = (datetime.now() - timedelta(days=random.randint(0, 365), hours=random.randint(9, 16))).strftime('%Y-%m-%d %H:%M:%S')
        status = random.choice(statuses)
        notes = "Follow-up required" if random.random() > 0.8 else None
        
        cursor.execute('''
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (p_id, d_id, appt_date, status, notes))
        if status == "Completed":
            appointment_ids.append(cursor.lastrowid)

    # 4. Insert 350 Treatments (Linked to completed appointments only)
    treatment_names = ["Blood Test", "X-Ray", "Physical Therapy", "Consultation", "Vaccination", "MRI"]
    for i in range(min(350, len(appointment_ids))):
        appt_id = random.choice(appointment_ids)
        t_name = random.choice(treatment_names)
        cost = round(random.uniform(50.0, 5000.0), 2)
        duration = random.choice([15, 30, 45, 60])
        
        cursor.execute('INSERT INTO treatments (appointment_id, treatment_name, cost, duration_minutes) VALUES (?, ?, ?, ?)', (appt_id, t_name, cost, duration))

    # 5. Insert 300 Invoices
    invoice_statuses = ["Paid", "Paid", "Pending", "Overdue"]
    for _ in range(300):
        p_id = random.choice(patient_ids)
        inv_date = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')
        total = round(random.uniform(100.0, 2000.0), 2)
        status = random.choice(invoice_statuses)
        paid = total if status == "Paid" else (0.0 if status == "Overdue" else round(total * 0.5, 2))
        
        cursor.execute('INSERT INTO invoices (patient_id, invoice_date, total_amount, paid_amount, status) VALUES (?, ?, ?, ?, ?)', (p_id, inv_date, total, paid, status))

    # ONLY ONE COMMIT AND CLOSE
    conn.commit()
    conn.close()
    print(f"Database seeded successfully with {len(patient_ids)} patients and {len(doctor_ids)} doctors!")

if __name__ == "__main__":
    create_tables()
    insert_dummy_data()