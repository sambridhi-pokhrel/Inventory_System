# Django Inventory Management System

A comprehensive web-based inventory management system built with Django, featuring role-based access control, user approval workflows, and modern responsive design.

## 📋 Project Overview

This inventory management system provides a complete solution for managing inventory items with different user roles and permissions. The system includes user registration with admin approval, secure authentication, role-based dashboards, and comprehensive inventory operations.

### 🎯 Key Features

- **Role-Based Access Control**: Three distinct user roles (Admin, Manager, Staff) with specific permissions
- **User Management**: Admin-controlled user approval system with role assignment
- **Secure Authentication**: Login, logout, password reset with email functionality
- **Inventory Operations**: Full CRUD operations with role-based restrictions
- **Advanced Search & Filtering**: Search by name, filter by stock status
- **Stock Management**: Automated low stock alerts and status tracking
- **Professional UI**: Modern Bootstrap-based responsive design
- **Security**: Custom decorators, mixins, and proper 403 error handling

## 👥 User Roles & Permissions

### 🔴 Administrator (Superuser)
- **User Management**: Approve/reject new users, assign roles
- **Full Inventory Access**: Add, edit, delete all inventory items
- **System Administration**: Complete system control
- **Dashboard**: User management statistics and system overview

### 🔵 Manager
- **Inventory Management**: Add and edit inventory items
- **Stock Monitoring**: Access to all inventory data and low stock alerts
- **Dashboard**: Inventory statistics and management tools

### 🟡 Staff
- **View Access**: Read-only access to inventory data
- **Search & Filter**: Full search and filtering capabilities
- **Dashboard**: Inventory overview and personal statistics

## 🚀 Setup Instructions

### Prerequisites
- Python 3.8+
- MySQL Server
- Git

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd inventory_system
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install django mysqlclient
   ```

4. **Database Configuration**
   - Create MySQL database named `inventory_system`
   - Update database credentials in `inventory_system/settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'inventory_system',
           'USER': 'your_username',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   ```

5. **Run Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create Superuser (Admin)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Create User Groups**
   ```bash
   python manage.py shell
   ```
   ```python
   from django.contrib.auth.models import Group
   Group.objects.create(name='Manager')
   Group.objects.create(name='Staff')
   exit()
   ```

8. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

9. **Access the Application**
   - Open browser to `http://127.0.0.1:8000/`
   - Login with superuser credentials

## 🔑 Login Credentials & User Flow

### Initial Access
1. **Admin Access**: Use the superuser account created during setup
2. **New User Registration**: 
   - Users can register at `/users/register/`
   - Account requires admin approval before access
   - Admin approves users and assigns roles via User Management dashboard

### User Registration Flow
1. User fills registration form with personal details
2. Account created with "Pending Approval" status
3. Admin receives notification of pending user
4. Admin reviews user in User Management dashboard
5. Admin approves user and assigns appropriate role (Manager/Staff)
6. User can now login and access system based on assigned role

### Password Reset
- Available via "Forgot Password" link on login page
- Email-based secure token system
- 24-hour token expiration for security

## 🏗️ System Architecture

### Applications
- **users/**: User authentication, roles, and management
- **inventory/**: Inventory items and operations
- **templates/**: Shared templates and error pages

### Key Components
- **Security Decorators**: `users/decorators.py` - Role-based access control
- **Role Management**: `users/utils.py` - Centralized role utilities
- **Custom Forms**: Enhanced registration and password reset forms
- **Error Handling**: Custom 403 forbidden page

### Database Models
- **User**: Django's built-in user model
- **UserProfile**: Extended user information with approval status
- **Item**: Inventory items with name, quantity, and price

## 🎨 User Interface

### Design Features
- **Responsive Design**: Mobile-friendly Bootstrap 5 interface
- **Modern Styling**: Gradient backgrounds and glassmorphism effects
- **Role-Based UI**: Different interfaces based on user permissions
- **Interactive Elements**: Hover effects, animations, and transitions
- **Professional Icons**: Bootstrap Icons throughout the system

### Key Pages
- **Login/Register**: Secure authentication with password visibility toggle
- **Dashboard**: Role-specific overview with statistics and quick actions
- **Inventory List**: Searchable, filterable inventory with stock status badges
- **User Management**: Admin interface for user approval and role assignment

## 🔒 Security Features

- **Role-Based Access Control**: Comprehensive permission system
- **User Approval Workflow**: Admin-controlled user access
- **Secure Authentication**: Password hashing and session management
- **Input Validation**: Form validation and XSS prevention
- **CSRF Protection**: Django's built-in CSRF middleware
- **Custom Error Handling**: Professional 403 forbidden pages

## 📁 Project Structure

```
inventory_system/
├── docs/                          # Documentation files
├── inventory/                     # Inventory app
│   ├── migrations/
│   ├── templates/inventory/
│   ├── models.py                  # Item model
│   ├── views.py                   # Inventory operations
│   └── urls.py
├── inventory_system/              # Main project
│   ├── settings.py                # Configuration
│   ├── urls.py                    # URL routing
│   └── wsgi.py
├── templates/                     # Shared templates
│   └── 403.html                   # Custom error page
├── users/                         # User management app
│   ├── migrations/
│   ├── templates/users/
│   ├── decorators.py              # Security decorators
│   ├── utils.py                   # Role utilities
│   ├── models.py                  # UserProfile model
│   ├── views.py                   # User operations
│   └── forms.py                   # Custom forms
├── manage.py
└── README.md
```

## 🧪 Testing

The system includes comprehensive role-based testing scenarios:
- User registration and approval workflow
- Role-based access control validation
- Inventory operations with permission checking
- Search and filtering functionality
- Password reset flow

## 📝 Development Notes

- **Django Version**: 5.2.7
- **Database**: MySQL
- **Frontend**: Bootstrap 5 with custom CSS
- **Security**: Custom decorators and mixins
- **Email**: Console backend for development (configurable for production)

## 🎓 Academic Project

This project demonstrates:
- **Full-Stack Development**: Complete Django web application
- **Security Best Practices**: Role-based access control and secure authentication
- **Database Design**: Proper model relationships and data integrity
- **User Experience**: Professional UI/UX design
- **Code Organization**: Clean architecture and separation of concerns

---

**Author**: [Your Name]  
**Course**: [Course Name]  
**Institution**: [University Name]  
**Date**: [Submission Date]