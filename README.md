# ✨ ApiB Documentation ✨

Welcome to **ApiB** – an innovative project that automates the creation of working shift schedules for two supermarket hubs. Designed with efficiency in mind, ApiB integrates modern web interfaces and a robust backend to streamline scheduling and meet legal work constraints.

---

## 🚀 Project Overview

**ApiB** leverages MongoDB as its primary database and offers three distinct interfaces:

- **Student/Worker Interface:**  
  Allows users to log in and upload their available dates and times for work.

- **Manager Interface:**  
  Enables managers to specify staffing needs by hub, setting the required number of personnel per day along with time ranges.

- **Workflow Interface:**  
  Automatically generates the working shift schedule based on the collected data and defined constraints.

The backend (code omitted for security reasons) utilizes the **ortools** library to enforce constraints such as:
- Maximum working days and hours per week
- Mandatory 11-hour breaks between shifts  
- And other legal work regulations

---

## 🔧 Installation & Running

To get ApiB up and running quickly, ensure you have **Docker** and **docker-compose** installed. Then, follow these steps:

1. **Clone or Download the Repository:**  
   Download the contents of the repository to your local machine.

2. **Start the Application:**  
   Open a terminal in the repository directory and run:
   ```bash
   docker-compose up -d

3. **Access the Interfaces:**
    Once the containers are running, open your web browser and navigate to:
    - Student/Worker Interface: http://localhost:5673/student
    - Manager Interface: http://localhost:5673/manager
    - Workflow Interface: http://localhost:5673/workflow

---

## 📚 Bibliography

-**Year:** 2021
-**Conference:** 25th International Conference on Knowledge-Based and Intelligent Information & Engineering Systems
-**Author:** Fred N. Kiwanuka
-**Title:** Modeling Employee Flexible Work Scheduling As A Classification Problem
-**Journal:** ScienceDirect

---

**Enjoy exploring ApiB and its capabilities in automating shift scheduling!**