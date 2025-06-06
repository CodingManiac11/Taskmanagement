# Task Management Application

## Project Description

This is a full-stack Task Management Application built with React for the frontend and Flask for the backend. It allows users to register, log in, and manage their tasks with features like creating, reading, updating, and deleting tasks, assigning tasks to other users, and filtering/sorting tasks.

## Features

- User Registration and Login
- JWT-based Authentication
- User Profile Management
- Create, Read, Update, and Delete Tasks
- Task Attributes (Title, Description, Due Date, Priority, Status)
- Task Assignment to Users
- Filtering and Sorting of Tasks
- Role-based task viewing (Admin can see all tasks, users see their own or assigned tasks)
- Responsive UI using Material-UI

## Technologies Used

**Frontend:**
- React
- Material-UI (MUI)
- Axios
- React Router DOM
- date-fns

**Backend:**
- Flask
- Flask-Cors
- Flask-SQLAlchemy
- PyJWT
- bcrypt
- SQLite (Database)

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.6+
- Node.js and npm
- Git

## Setup Instructions

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/CodingManiac11/Taskmanagement.git
    cd Taskmanagement
    ```

2.  **Backend Setup:**

    Navigate to the `backend` directory:

    ```bash
    cd backend
    ```

    Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

    The Flask application uses a SQLite database. On the first run, it will create the necessary database file (`instance/tasks.db`) and tables. It will also create a default admin user if one does not exist.

3.  **Frontend Setup:**

    Navigate to the `frontend` directory:

    ```bash
    cd ../frontend
    ```

    Install the required npm packages:

    ```bash
    npm install
    ```

## Running the Application

1.  **Start the Backend Server:**

    Open a terminal, navigate to the `backend` directory, and run:

    ```bash
    cd backend
    python app.py
    ```

    The backend server will run on `http://localhost:5000`.

2.  **Start the Frontend Server:**

    Open a **separate** terminal, navigate to the `frontend` directory, and run:

    ```bash
    cd frontend
    npm start
    ```

    The frontend application will open in your browser at `http://localhost:3000`.

## Admin User

On the first successful run of the backend (`python app.py`) with an empty database, a default admin user is created with the following temporary credentials:

-   **Username:** `admin`
-   **Email:** `admin@taskapp.com`
-   **Password:** `admin123`

**It is highly recommended to log in as this user immediately and change the password and potentially the username/email via the profile page for security reasons.**

Admin users have access to view all tasks in the system.

## Further Development

- Implement more comprehensive error handling and user feedback.
- Enhance UI/UX design and add more animations.
- Add filtering and sorting options for admin viewing all tasks.
- Implement task editing and deletion functionalities on the frontend.
- Add more robust testing.
- Consider using a more production-ready database. 
