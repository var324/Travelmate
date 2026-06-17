# ✈️ TravelMate – Business Travel Management System

TravelMate is a full-stack web application designed to manage employee business travel requests, approvals, notifications, and corporate travel compliance within an organization. It provides a role-based system for employees and managers to streamline travel planning and approval workflows.

---

## 📌 Project Overview

TravelMate helps organizations handle:
- Business trip requests
- Manager approvals and rejections
- Travel policy enforcement
- Expense estimation (flight, hotel, total cost)
- Notifications for status updates
- Corporate compliance tracking

---

## 🚀 Features

### 👤 Employee Features
- Secure login system
- Account activation process
- Create business trip requests using a multi-module form
- View upcoming trips
- View flight and hotel details
- Receive notifications for approvals/rejections
- Access corporate travel policy

---

### 👨‍💼 Manager Features
- Dedicated manager dashboard
- View all trip requests:
  - Pending trips
  - Approved trips
  - Rejected trips
- Approve or reject travel requests
- Automatic notification generation for employees
- Role-based access control

---

### 🔔 Notifications System
- Alerts for:
  - Trip approval
  - Trip rejection
  - Account activation updates
- Stored per user

---

### 📄 Corporate Travel Policy
- Built-in policy page explaining company travel rules:
  - Advance booking requirements
  - Trip approval rules
  - Hotel cost limits
  - Expense reimbursement policies
  - Required documentation
  - Cybersecurity and VPN compliance

---

## 🧭 Application Pages / Routes

### 🔐 Authentication
- `/login` → User login page
- `/activate` → Account activation page

---

### 👤 Employee Routes
- `/dashboard` → Employee dashboard
- `/create-trip` → Business trip request form
- `/notifications` → View notifications
- `/policy` → Corporate travel policy page

---

### 👨‍💼 Manager Routes
- `/manager` → Manager dashboard
- `/approve/<trip_id>` → Approve trip request
- `/reject/<trip_id>` → Reject trip request

---

## 🏗️ Tech Stack

- **Backend:** Flask (Python)
- **Frontend:** HTML, CSS, Jinja2 templates
- **Database:** SQLAlchemy (SQLite / PostgreSQL)
- **Authentication:** Flask sessions + Werkzeug password hashing

---

## 🔐 Role-Based Access Control

TravelMate uses role-based authentication:

| Role     | Permissions |
|----------|------------|
| Employee | Create trips, view status, notifications |
| Manager  | Approve/reject trips, view all requests |

---

## 🔄 System Workflow

1. User logs in through `/login`
2. System validates credentials
3. Role is stored in session:
   - Employee → redirected to `/dashboard`
   - Manager → redirected to `/manager`
4. Employee submits a trip request
5. Manager reviews requests
6. Manager approves or rejects trips
7. Notification is sent to employee
8. Employee sees updated status in dashboard

---

## 📊 Business Logic

- Trips must be approved before confirmation
- Expenses are calculated automatically
- Hotel and flight costs are tracked
- Notifications are generated on status change
- Users must activate account before login access

---

## ⚙️ Installation & Setup

```bash
# Clone repository
git clone <your-repo-url>

# Move into project folder
cd travelmate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
