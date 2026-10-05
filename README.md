
# Clinic Management System (Dhada)

A comprehensive, responsive web application designed for outpatient clinics, medical centers, and private practices to streamline doctor management, patient records, appointment scheduling, and billing workflows.

---

## 🌟 Key Features

### 👨‍⚕️ Doctor Management

- **Doctor Profiles**: Manage doctor details including name, specialization, arrival time, consultation fees, and weekly off-days.
- **Dynamic Specializations**: Built-in support for medical specializations (General Physician, Cardiologist, Dermatologist, ENT, Gynecologist, etc.) with custom "Other" specification support.
- **Commission Tracking**:
  - Supports both **Percentage-based (%)** and **Fixed-amount (Rs.)** commission structures.
  - Automatic calculation of doctor earnings on visited appointments.
  - Comprehensive commission payout history and pending balance tracking.

### 👥 Patient Management

- **Fast Registration**: Quick patient intake with seamless redirection to appointment scheduling.
- **Patient Detail Dashboard**:
  - Complete history of past visits, waiting consultations, and cancellations.
  - Financial overview of total paid vs. outstanding dues.
  - Direct quick actions to book new appointments, edit profiles, or clear pending balances.

### 📅 Appointment & Queue Management

- **Automated Token Generation**: Auto-incrementing daily queue token numbers per doctor and date.
- **Doctor Availability Check**: Intelligent validation that checks and warns against booking on doctor's scheduled off-days.
- **Appointment Types**: Supports **Regular**, **Follow-Up (Paid)**, and **Follow-Up (Free)** visits.
- **Status Workflow**: Manage appointment status through **Waiting**, **Visited**, and **Cancelled**.

### 💳 Billing & Payment Tracking

- **Flexible Payment Statuses**: Fully tracks **Paid**, **Partial**, and **Unpaid** appointments.
- **Partial Payment Workflow**: Dedicated workflow allowing partial upfront payments and tracking remaining balances.
- **Due Clearance**: Easily settle outstanding balances directly from the patient’s profile.

### 📊 Dashboard & Analytics

- Overview of key metrics: Total Doctors, Patients, Appointments, Paid/Unpaid counts, and queue status.
- Quick navigation shortcuts for front-desk and clinical staff.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Django 5.x / 6.x
- **Database**: SQLite (default for development; easily configurable for PostgreSQL or MySQL)
- **Frontend**: Django Templates, Vanilla HTML5 / CSS3, JavaScript
- **Libraries**: [Flatpickr](https://flatpickr.js.org/) for interactive date selection

---

## 📁 Project Structure

```text
Dhada/
├── Dhada/                 # Project configuration
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py        # Django settings and configurations
│   ├── urls.py            # Root URL routing
│   └── wsgi.py
├── doctors/               # Core clinical management app
│   ├── migrations/        # Database migrations
│   ├── admin.py           # Django admin registration
│   ├── apps.py
│   ├── forms.py           # Forms for doctors, patients, appointments, payments
│   ├── models.py          # Data models (DoctorProfile, Patient, Appointment, etc.)
│   ├── urls.py            # App-level URL routes
│   └── views.py           # Business logic and view handlers
├── static/                # Static assets (CSS, JS, Images)
│   ├── css/
│   ├── js/
│   └── images/
├── templates/             # HTML Templates
│   ├── base.html          # Base layout template
│   ├── dashboard.html     # Main analytics dashboard
│   ├── homepage.html      # Landing page
│   ├── appointments/      # Appointment booking and payment templates
│   ├── doctors/           # Doctor profile and commission templates
│   └── patients/          # Patient registration, list, and detail templates
├── manage.py              # Django management script
├── requirements.txt       # Project dependencies
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed:

- **Python 3.10+**
- **pip** (Python package manager)
- **Git**

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/kaushal-karna/clinical-management-system.git
   cd Dhada
   ```
2. **Create and activate a virtual environment**:

   - On Windows:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```
4. **Apply database migrations**:

   ```bash
   python manage.py migrate
   ```
5. **(Optional) Load initial fixture data**:

   ```bash
   python manage.py loaddata data.json
   ```
6. **Create an administrator account**:

   ```bash
   python manage.py createsuperuser
   ```
7. **Start the development server**:

   ```bash
   python manage.py runserver
   ```
8. **Access the application**:

   - Web App: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - Admin Panel: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## ⚙️ Configuration Notes

- **Timezone**: Set to `Asia/Kathmandu` in `Dhada/settings.py` (update `TIME_ZONE` as per your local region).
- **Secret Key & Debug**: Make sure to set `DEBUG = False` and use environment variables for `SECRET_KEY` and `ALLOWED_HOSTS` before deploying to production.

---

## 📄 License

This project is licensed under the MIT License.
