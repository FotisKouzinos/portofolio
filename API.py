from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import json
import datetime
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "a9f3e0c8d4b7a621e2e6e10d8fa3b3c2a5d7e9c9b1f6d3a4e7b2c6d5f8a1b0e4"

# --- CONNECT TO MONGODB ---
try:
    with open('/apib/ApiB/backend/conf.json', 'r') as json_file:
        data = json.load(json_file)

    uri = ("mongodb://%s:%s@%s:27017/%s?authSource=admin" % (data['username'],
                                                            data['password'],
                                                            data['host'],
                                                            data['name']))
    client = MongoClient(uri)
    db = client['ApiB']  # Ensure database is correctly named
    hubs_collection = db['hub']
    students_collection = db['students']
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    db = None

# --- GENERATE AND SHOW THE SCHEDULE ---
@app.route('/workflow')
def generate_and_show_schedule():
    try:
        with open("/apib/ApiB/backend/workflow.json", 'r') as workflow:
            output_schedule = json.load(workflow)
        schedule_data = output_schedule.get("hubs", {}).get("schedule", {})
        return render_template('index.html', schedule=schedule_data, year=datetime.datetime.now().year)
    except json.JSONDecodeError:
        return render_template('index.html', error="Error decoding JSON. Ensure workflow.json is correctly formatted.", year=datetime.datetime.now().year)
    except Exception as e:
        return render_template('index.html', error=f"An unexpected error occurred: {str(e)}", year=datetime.datetime.now().year)

# --- MANAGER INTERFACE ---
@app.route('/manager')
def manager():
    try:
        if db is not None:  # ✅ Explicitly check if db is not None
            hub_document = hubs_collection.find_one({}, {"_id": 0, "hubs": 1})  # Fetch only hubs array
            hubs = hub_document.get("hubs", []) if hub_document else []  # Extract hubs safely
        else:
            hubs = []
        return render_template('manager.html', data={"hubs": hubs})  
    except Exception as e:
        return f"Error fetching hubs: {str(e)}"

@app.route('/manager/update_hub', methods=['POST'])
def update_hub():
    try:
        hub_id = request.form.get('edit_hub_id')
        # Prepare dictionaries for storing multiple time slots
        hours_need = {}
        students_need = {}
        for day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
            from_times = request.form.getlist(f'edit_hours_{day}_from[]')
            to_times = request.form.getlist(f'edit_hours_{day}_to[]')
            student_counts = request.form.getlist(f'edit_students_{day}[]')
            # Ensure correct formatting
            time_slots = []
            student_slots = []
            for from_time, to_time, student_count in zip(from_times, to_times, student_counts):
                time_slots.append(f"{int(from_time):02d}:00-{int(to_time):02d}:00")
                student_slots.append(int(student_count))  # Convert student count to integer
            hours_need[day] = time_slots if time_slots else []
            students_need[day] = student_slots if student_slots else []
        # Fetch the entire hubs list from MongoDB
        hub_document = hubs_collection.find_one({}, {"_id": 0, "hubs": 1})
        if not hub_document or "hubs" not in hub_document:
            return jsonify({"error": "No hubs found in database."}), 500
        hubs_list = hub_document["hubs"]
        # Find the hub and update it
        for hub in hubs_list:
            if hub["hub_id"] == hub_id:
                hub["hours_need"] = hours_need
                hub["students_need"] = students_need
                break  # Stop looping once updated
        # Update MongoDB with the modified hubs list
        hubs_collection.update_one(
            {"hubs.hub_id": hub_id},  # Match the hub inside the array
            {"$set": {
                "hubs.$.hours_need": hours_need,
                "hubs.$.students_need": students_need
            }}
        )
        return jsonify({"hubs": hubs_list})  # Return updated hubs list
    except Exception as e:
        return jsonify({"error": f"Failed to update hub: {e}"}), 500

@app.route('/manager/save_output', methods=['POST'])
def save_output():
    try:
        # Fetch the latest hubs data from MongoDB
        hub_document = hubs_collection.find_one({}, {"_id": 0, "hubs": 1})
        if not hub_document or "hubs" not in hub_document:
            return jsonify({"error": "No hubs found in database."}), 500
        hubs_data = hub_document["hubs"]
        # Save the updated dictionary to a JSON file
        with open('final.json', 'w') as json_file:
            json.dump({"hubs": hubs_data}, json_file, indent=4)
        hubs_collection.update_one(
            {},  # Match the first document
            {"$set": {"hubs": hubs_data}}
        )
        return jsonify({"message": "Data saved successfully!", "hubs": hubs_data}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to save data: {e}"}), 500

# --- STUDENT INTERFACE ---

# Route for student login page
@app.route('/student', methods=['GET', 'POST'])
def student_home():
    if request.method == 'POST':  # Check if the request is a POST (form submission)
        student_id = request.form['student_id'].strip()  # Get the student ID from the form and remove whitespace
        student_name = request.form['student_name'].strip()  # Get the student name from the form and remove whitespace
        # Fetch the document that contains the students array from MongoDB
        student_document = students_collection.find_one({}, {'_id': 0, 'students': 1})# this is the dictionary for the students
        if not student_document:  # If no document is found, return an error message
            return render_template('student_login.html', error="Database error. Please contact admin.")
        # Extract the students list from the document
        students_list = student_document.get("students", [])
        # Search for a matching student by ID and name
        student = next((s for s in students_list if s["id"] == student_id and s["name"] == student_name), None)
        if student:  # If the student is found
            session['student_id'] = student_id  # Store the student ID in the session
            session['student_name'] = student_name  # Store the student name in the session
            session['student_data'] = student  # ✅ Store the entire student data in the session
            session.modified = True  # Ensure the session is saved
            return redirect(url_for('student_dashboard'))  # Redirect to the student dashboard
        else:  # If no match is found, return an error message
            return render_template('student_login.html', error="Invalid Student ID or Name. Please try again.")    
    return render_template('student_login.html')  # Render the login page for GET requests

# Route for adding availability for a specific day
@app.route('/student/add', methods=['POST'])
def add_entry():
    try:
        if 'student_id' not in session:  # Check if the user is logged in
            return redirect(url_for('student_home'))  # Redirect to login if not logged in
        student_id = session['student_id']  # Get the logged-in student's ID from the session
        day = request.form['day']  # Get the selected day from the form
        from_time = request.form['from']  # Get the start time from the form
        to_time = request.form['to']  # Get the end time from the form
        # Fetch student data from session
        student = session.get('student_data')
        if not student:  # If student data is not found in session
            return jsonify({"error": "Student data not found in session"}), 404
        # Update only the selected day's availability with the chosen time range
        student["availability"][day] = f"{from_time}:00-{to_time}:00"
        # Save updated availability in session
        session['student_data'] = student
        session.modified = True  # Ensure session is saved
        # Update the student's availability in MongoDB for the selected day only
        students_collection.update_one(
            {"students.id": student_id},  # Find the student by ID
            {"$set": {f"students.$.availability.{day}": student["availability"][day]}}  # Update only the chosen day
        )
        return redirect(url_for('student_dashboard'))  # Redirect to dashboard
    except Exception as e:
        return jsonify({"error": f"Failed to update availability: {e}"}), 500  # Return error message if an issue occurs

# Route for completing availability by filling in missing days with "None"
@app.route('/student/complete_availability', methods=['POST'])
def complete_availability():
    try:
        if 'student_id' not in session:
            return redirect(url_for('student_home'))
        student_id = session['student_id']
        student = session.get('student_data')
        if not student or "availability" not in student:
            return jsonify({"error": "Student data not found in session"}), 404
        # Ensure all days exist in availability; if missing, set to ["None"]
        for day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
            if day not in student["availability"] or not student["availability"][day]:
                student["availability"][day] = ["None"]
        # Update session data to reflect changes
        session['student_data'] = student
        session.modified = True
        # Update database to reflect "None" for empty days
        students_collection.update_one(
            {"students.id": student_id},
            {"$set": {f"students.$.availability": student["availability"]}}
        )
        return redirect(url_for('student_dashboard'))  # Redirect to dashboard
    except Exception as e:
        return jsonify({"error": f"Failed to complete availability: {e}"}), 500

# Route for displaying the student dashboard
@app.route('/student/dashboard')
def student_dashboard():
    if 'student_id' not in session:  # Ensure user is logged in
        return redirect(url_for('student_home'))  # Redirect to login if not
    student_id = session['student_id']  # Retrieve student ID from session
    # Fetch student data from the database
    student_document = students_collection.find_one({}, {'_id': 0, 'students': 1})
    if not student_document:  # Ensure database contains student data
        return redirect(url_for('student_home'))  # Redirect to login if no students found
    # Find the logged-in student in the database
    students_list = student_document.get("students", [])
    student = next((s for s in students_list if s["id"] == student_id), None)
    if student:
        # Ensure the student has an "availability" field but leave it empty initially
        student.setdefault("availability", {day: [] for day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]})
        # Store updated student data in session
        session['student_data'] = student
        session.modified = True
        return render_template('student_dashboard.html', json_data=student)  # Render the dashboard
    return redirect(url_for('student_home'))  # Redirect to login if student not found

@app.route('/student/update_availability', methods=['POST'])
def update_availability():
    try:
        if 'student_id' not in session:
            return redirect(url_for('student_home'))
        student_id = session['student_id']
        student = session.get('student_data')
        if not student:
            return jsonify({"error": "Student data not found in session"}), 404
        # Retrieve availability data from form
        updated_availability = {}
        for day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
            from_times = request.form.getlist(f"availability[{day}][from][]")
            to_times = request.form.getlist(f"availability[{day}][to][]")
            # Ensure correct formatting
            availability_slots = []
            for from_time, to_time in zip(from_times, to_times):
                if from_time == "None" or to_time == "None":
                    availability_slots = ["None"]
                    break  # If any slot is "None", the entire day is marked unavailable
                availability_slots.append(f"{from_time}:00-{to_time}:00")
            updated_availability[day] = availability_slots
        # Update student data in session
        student["availability"] = updated_availability
        session['student_data'] = student
        session.modified = True
        # Replace the entire availability field in MongoDB
        students_collection.update_one(
            {"students.id": student_id},
            {"$set": {f"students.$.availability": updated_availability}}
        )
        return redirect(url_for('student_dashboard'))  # Redirect back to dashboard
    except Exception as e:
        return jsonify({"error": f"Failed to update availability: {e}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5673)