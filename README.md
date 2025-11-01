# 🧩 Internal Service Request Tracking System

A simple web-based application that allows staff to submit IT service requests and enables administrators to manage and track these requests efficiently.  
This project was built as part of the **IT Officer Assessment** focusing on software development, systems integration, and automation.

---

## 📌 Features

- Staff can submit IT service requests (Name, Department, Category, Description)
- Requests are stored in a database with timestamps and default “Pending” status
- Admins can view, update, and resolve requests
- Integrated with an **Email API (SendGrid)** to send notifications
- Basic automation for request status updates
- Basic authentication for admin users
- Clean and responsive UI using **Bootstrap 5**

---

## 🧱 Tech Stack

- **Backend:** PHP (Laravel Framework)
- **Frontend:** Blade Templates + Bootstrap 5
- **Database:** MySQL
- **API Integration:** SendGrid Email API
- **Version Control:** Git & GitHub

---

## ⚙️ Installation and Setup

Follow these steps to run the project locally:

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/it-service-tracker.git
cd it-service-tracker
