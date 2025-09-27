# Job Board Platform Backend

A robust backend system requiring complex role management and efficient data retrieval for a job platform endpoints for job postings, categories, and applications.

## 📌 Overview

The backend enables:

- **Job Postings Management**: CRUD APIs for jobs, categories, and applications.  
- **Role-Based Access Control (RBAC)**: Secure authentication using JWT, with different permissions for admins and users.  
- **Optimized Job Search**: Efficient query performance, including indexing and advanced filtering.  
- **Background Jobs**: Asynchronous processing for tasks like sending emails and job alerts.  
- **Caching**: Redis-based caching strategies for API performance optimization.  
- **API Documentation**: Interactive Swagger docs for seamless integration with frontend clients.  
- **CI/CD Pipelines**: Automated linting, testing, and Dockerized deployment.  

---

![ERD Diagram](docs/ERD/erd.png)
full documentation of the ERD can be found [here](docs/ERD/erd.md).

## 🎯 Project Goals

- Build APIs for managing **job postings, categories, and applications**.  
- Implement **secure role-based authentication** for admins and users.  
- Optimize job search with **query indexing** and **filters**.  
- Set up **background jobs** (Celery + RabbitMQ + celery-beat).  
- Add **email service** for onboarding, job notifications, and alerts.  
- Integrate **caching strategies** for job search endpoints.  
- Provide **Swagger API docs** at `/api/docs`.  
- Use **Docker Compose** to orchestrate Django, PostgreSQL, Redis, and RabbitMQ.  

---

## 🛠️ Technologies Used

| Technology     | Purpose                                      |
|----------------|----------------------------------------------|
| Django         | High-level Python framework for rapid backend development |
| PostgreSQL     | Relational database for job board data       |
| JWT            | Secure authentication for role-based access  |
| Redis          | Caching layer for fast queries               |
| Celery + RabbitMQ | Background jobs, async processing, scheduled tasks |
| celery-beat    | Scheduling recurring background jobs         |
| Swagger (drf-yasg) | API documentation                        |
| Docker Compose | Container orchestration for services         |
| GitHub Actions | CI/CD pipelines for linting, testing, and deployment |

---

## 🔑 Key Features

### Job Posting Management

- CRUD APIs for jobs, categories, and applications.  
- Categorize jobs by **industry, location, and type**.  

### Role-Based Authentication

- **Admins**: Manage jobs and categories.  
- **Users**: Apply for jobs and manage applications.  

### Optimized Job Search

- Use **indexes** for faster filtering.  
- Provide **location-based** and **category-based** filtering.  

### Background Jobs

- **Email notifications** for user onboarding and job alerts.  
- **Scheduled tasks** with celery-beat.  

### Caching & Strategies

- Redis caching for job search endpoints.  
- Invalidation strategies to ensure fresh data.  

### API Documentation

- Hosted at `/api/docs`.  
- Auto-generated and updated with drf-yasg.  

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/job-board-be.git
   cd job-board-be
   ```
2. Environment Variables

Create a .env file in the root directory:
  ```bash
    cp .env.example .env
  ```
 Update the variables in the .env file as needed.

2. Create a virtual environment:
```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
  ```

3. Install the dependencies:

```bash
   pip install -r requirements.txt
   ```

4. Create a PostgreSQL database:

```bash
sudo -u postgres psql
CREATE DATABASE job_board;
  ```

5. Set up the environment variables:
   ```bash
   cp .env.example .env
   ```

5. Run the migrations:
```bash
   python manage.py migrate
   ```

6. Start the development server:
```bash
   python manage.py runserver
   ```
7. Access the application at `http://localhost:8000` and the API documentation at `http://localhost:8000/api/docs/`.

## Contributing
Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For any inquiries or support, please contact [support@jobboard.com](mailto:support@jobboard.com).