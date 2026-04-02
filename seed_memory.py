from vanna_setup import get_agent

def seed_agent_memory():
    """
    Seeds the Vanna Agent's memory with validated Question-to-SQL pairs.
    This provides the LLM with a 'few-shot learning' baseline, improving its 
    accuracy when interpreting domain-specific queries about the clinic schema.
    """
    print("Initializing Vanna Agent for memory seeding...")
    agent = get_agent()
    
    # Validated English-to-SQL pairs spanning all required schema dimensions
    qa_pairs = [
        # --- PATIENT DEMOGRAPHICS ---
        (
            "How many patients do we have?",
            "SELECT COUNT(*) AS total_patients FROM patients;"
        ),
        (
            "Which city has the most patients?",
            """SELECT city, COUNT(*) AS patient_count FROM patients 
               GROUP BY city ORDER BY patient_count DESC LIMIT 1;"""
        ),
        (
            "List all female patients from New York",
            "SELECT first_name, last_name, email FROM patients WHERE gender = 'F' AND city = 'New York';"
        ),
        (
            "List patients who have visited more than 3 times",
            """SELECT p.first_name, p.last_name, COUNT(a.id) as visit_count 
               FROM patients p JOIN appointments a ON p.id = a.patient_id 
               GROUP BY p.id HAVING visit_count > 3;"""
        ),
        
        # --- DOCTOR WORKLOAD ---
        (
            "List all doctors and their specializations",
            "SELECT name, specialization FROM doctors;"
        ),
        (
            "Which doctor has the most appointments?",
            """SELECT d.name, COUNT(a.id) AS appointment_count 
               FROM doctors d JOIN appointments a ON d.id = a.doctor_id 
               GROUP BY d.name ORDER BY appointment_count DESC LIMIT 1;"""
        ),
        
        # --- APPOINTMENT METRICS ---
        (
            "How many cancelled appointments did we have last month?",
            """SELECT COUNT(*) AS cancelled_count FROM appointments 
               WHERE status = 'Cancelled' AND appointment_date >= date('now', '-1 month');"""
        ),
        (
            "What percentage of appointments are no-shows?",
            """SELECT (CAST(SUM(CASE WHEN status = 'No-Show' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*)) * 100 AS no_show_percentage 
               FROM appointments;"""
        ),
        (
            "Show the busiest day of the week for appointments",
            """SELECT strftime('%w', appointment_date) AS day_of_week, COUNT(*) AS appointment_count 
               FROM appointments GROUP BY day_of_week ORDER BY appointment_count DESC LIMIT 1;"""
        ),

        # --- FINANCIAL METRICS ---
        (
            "Show revenue by doctor",
            """SELECT d.name, SUM(i.total_amount) AS total_revenue 
               FROM invoices i 
               JOIN appointments a ON a.patient_id = i.patient_id 
               JOIN doctors d ON d.id = a.doctor_id 
               GROUP BY d.name ORDER BY total_revenue DESC;"""
        ),
        (
            "Show unpaid invoices",
            "SELECT id, patient_id, total_amount, invoice_date FROM invoices WHERE status IN ('Pending', 'Overdue');"
        ),
        (
            "Average treatment cost by specialization",
            """SELECT d.specialization, AVG(t.cost) AS average_cost 
               FROM doctors d 
               JOIN appointments a ON d.id = a.doctor_id 
               JOIN treatments t ON a.id = t.appointment_id 
               GROUP BY d.specialization;"""
        ),
        (
            "Top 5 patients by total spending",
            """SELECT p.first_name, p.last_name, SUM(i.total_amount) AS total_spending 
               FROM patients p JOIN invoices i ON p.id = i.patient_id 
               GROUP BY p.id ORDER BY total_spending DESC LIMIT 5;"""
        ),

        # --- TIME-SERIES TRENDS ---
        (
            "Show monthly appointment count for the past 6 months",
            """SELECT strftime('%Y-%m', appointment_date) AS month, COUNT(*) AS appointment_count 
               FROM appointments 
               WHERE appointment_date >= date('now', '-6 months') 
               GROUP BY month ORDER BY month DESC;"""
        ),
        (
            "Revenue trend by month",
            """SELECT strftime('%Y-%m', invoice_date) AS month, SUM(total_amount) AS monthly_revenue 
               FROM invoices GROUP BY month ORDER BY month DESC;"""
        )
    ]

    print(f"Injecting {len(qa_pairs)} training pairs into Agent Memory...")
    
    for question, sql in qa_pairs:
        # Utilize the agent's tool registry to safely write to local memory
        agent.tool_registry.execute_tool(
            tool_name="save_question_tool_args", 
            question=question, 
            sql=sql
        )
        
    print("Memory seeding successfully completed.")

if __name__ == "__main__":
    seed_agent_memory()