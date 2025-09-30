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
- Redoc at `/api/redoc`.  
- Auto-generated and updated with drf-yasg.  

---

## Installation

1. Clone the repository:

```bash
   git clone https://github.com/olaishola05/job-board-be.git
   cd job-board-be
   ```

2. Environment Variables

Create a .env file in the root directory:
  ```bash
    cp .env.example .env
  ```
 Update the variables in the .env file as needed.

3. Create a virtual environment:

```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
  ```

4. Install the dependencies:

```bash
   pip install -r requirements.txt
   ```

5. Create a PostgreSQL database:

```bash
login to your DB and create a database named `job_board_db`
   CREATE DATABASE job_board_db;
  ```

6. Set up the environment variables:
   ```bash
   cp .env.example .env
   ```

7. Run the migrations:
```bash
   python manage.py migrate
   ```

8. Create a superuser:
```bash
   python manage.py createsuperuser
   ```

9. (Optional) Load initial data:
```bash
   python manage.py seed_db
   ```

10. Start the development server:
```bash
   python manage.py runserver
   ```

11. Start the Celery worker and beat scheduler in separate terminal windows:

```bash
   celery -A job_platform worker -l INFO
   celery -A job_platform beat -l INFO
   ```

## Docker Setup (Optional)

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

Run migrations

``` bash
docker-compose exec web python manage.py migrate
```

Create superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

Load initial data (optional)

```bash
docker-compose exec web python manage.py seed_db
```

Start Celery worker and beat

```bash
docker-compose exec web celery -A job_platform worker -l INFO
docker-compose exec web celery -A job_platform beat -l INFO
```

## Access Points

- API: `<http://localhost:8000/api/v1/>`
- Swagger Docs: `<http://localhost:8000/api/docs/>`

## API Endpoints

Authentication

- POST /api/v1/auth/register/ - User registration
- POST /api/v1/auth/login/ - User login
- POST /api/v1/auth/refresh/ - Refresh JWT token
- POST /api/v1/auth/logout/ - User logout

Jobs

- GET /api/v1/jobs/ - List jobs with filtering
- POST /api/v1/jobs/ - Create job posting
- GET /api/v1/jobs/{id}/ - Job details
- POST /api/v1/jobs/{id}/apply/ - Apply to job

Companies

- GET /api/v1/companies/ - List companies
- POST /api/v1/companies/ - Create company
- GET /api/v1/companies/{id}/jobs/ - Company jobs

## Contributing
Contributions are welcome! Please fork the repository and create a pull request with your changes.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Author
- Oladipupo Ishola (olaishola05) - [GitHub](https://github.com/olaishola05)
- LinkedIn: [Oladipupo Ishola](https://www.linkedin.com/in/olaishola05/)


## Acknowledgements
- Inspired by best practices in backend development and job board platforms.
- Thanks to the open-source community for the tools and libraries used in this project.
- ALX Africa for the learning resources and support.