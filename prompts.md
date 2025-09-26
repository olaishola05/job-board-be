# Job Board Platform Development Prompts

## 🚀 Project Setup and Initial Configuration

### Prompt 1: Django Project Setup with Docker

```
Create a Django project setup for a Job Board Platform with the following requirements:
- Django 4.2+ with PostgreSQL database
- Docker Compose configuration for Django app, PostgreSQL, Redis, and RabbitMQ
- Environment configuration with python-dotenv
- Basic project structure with apps: accounts, jobs, companies, core
- Requirements.txt with all necessary packages including Celery, DRF, JWT, Swagger
- Settings configuration for development and production environments
- Database settings optimized for PostgreSQL with connection pooling
- Static and media files configuration
- CORS configuration for frontend integration
- Logging configuration with different levels for development and production
```

### Prompt 2: Authentication System Setup

```
Create a comprehensive authentication system for the Job Board Platform with:
- Custom User model extending AbstractUser with role-based access (admin, employer, job_seeker)
- JWT authentication with access and refresh tokens
- Email verification system with token-based verification
- Password reset functionality with secure token generation
- User registration with email confirmation
- Login/logout endpoints with proper token management
- Role-based permissions and decorators
- User profile management endpoints
- Account activation and deactivation functionality
- Rate limiting for authentication endpoints to prevent brute force attacks
```

### Prompt 3: Database Models Implementation

```
Implement the complete database models for the Job Board Platform based on the provided schema:
- User, Profile, Company, Industry, JobCategory models
- Job, JobApplication, SavedJob, JobView models
- Skill, SkillCategory, JobAlert, JobType models
- AuditLog model for tracking user actions
- Proper model relationships with foreign keys and many-to-many fields
- Database indexes for query optimization
- Model methods for common operations
- String representations and metadata
- Custom managers for frequently used queries
- Model validators for data integrity
```

## 🔧 Core API Development

### Prompt 4: Job Management APIs

```
Create comprehensive REST APIs for job management with the following features:
- CRUD operations for job postings (create, read, update, delete)
- Job listing with advanced filtering (location, category, salary range, job type, experience level)
- Search functionality with full-text search and relevance scoring
- Job application submission and management
- Job saving/bookmarking for users
- Job view tracking for analytics
- Bulk operations for admin users
- Job status management (draft, published, closed)
- Featured jobs management
- File upload handling for job-related documents
- Pagination with cursor-based pagination for better performance
- API versioning and proper HTTP status codes
```

### Prompt 5: Company Management System

```
Develop a complete company management system with:
- Company profile creation and management
- Company verification system for trusted employers
- Company-specific job postings management
- Company analytics dashboard data
- Company search and filtering
- Company logo and media upload handling
- Industry association and categorization
- Company size and founding year tracking
- Company location management with geocoding
- Company following/subscription system for job seekers
- Admin approval workflow for new companies
- Company performance metrics and reporting
```

### Prompt 6: Advanced Search and Filtering

```
Implement advanced search and filtering capabilities:
- Full-text search using PostgreSQL's full-text search capabilities
- Location-based search with radius filtering
- Salary range filtering with currency conversion
- Experience level and job type filtering
- Skills-based matching with relevance scoring
- Date range filtering (posted date, application deadline)
- Company size and industry filtering
- Remote work filtering options
- Advanced query builder with AND/OR operators
- Search result ranking algorithm
- Search analytics and popular search terms tracking
- Auto-complete suggestions for search terms
- Saved searches and search alerts
```

## 🔐 Security and Performance

### Prompt 7: Rate Limiting and Security Implementation

```
Implement comprehensive security measures:
- Rate limiting using Django-ratelimit for different endpoints
- API throttling with user-based and IP-based limits
- Input validation and sanitization
- SQL injection prevention with parameterized queries
- XSS protection with proper escaping
- CSRF protection for state-changing operations
- File upload security with type validation and size limits
- Secure headers configuration (HSTS, CSP, etc.)
- API key authentication for third-party integrations
- Audit logging for security events
- Brute force protection for login attempts
- Data encryption for sensitive information
```

### Prompt 8: Caching Strategy Implementation

```
Develop a comprehensive caching strategy:
- Redis caching configuration with Django
- Query result caching for expensive database operations
- Page-level caching for static content
- Fragment caching for partially dynamic content
- Session caching with Redis backend
- Cache invalidation strategies for data updates
- Cache warming for frequently accessed data
- Database query optimization with select_related and prefetch_related
- Memcached integration for distributed caching
- Cache monitoring and performance metrics
- Cache key management and namespacing
- TTL (Time To Live) configuration for different data types
```

## 🔄 Background Jobs and Async Processing

### Prompt 9: Celery and Background Tasks

```
Set up Celery with RabbitMQ for background job processing:
- Celery configuration with RabbitMQ as message broker
- Task definitions for email sending, report generation, data processing
- Periodic tasks with Celery Beat for scheduled operations
- Job application processing and notifications
- Email notification system for job alerts
- Data export tasks for large datasets
- Image processing and optimization tasks
- Database cleanup and maintenance tasks
- Task monitoring and failure handling
- Task retry mechanisms with exponential backoff
- Task priority queues for different operation types
- Worker scaling and load balancing
- Task result storage and retrieval
- Dead letter queue handling for failed tasks
```

### Prompt 10: Email Service Integration

```
Implement a comprehensive email service system:
- Email backend configuration with SMTP/SendGrid/AWS SES
- HTML email templates for different notification types
- Email queue management with Celery
- Job alert notifications with customizable frequency
- Application status update notifications
- Welcome and verification emails
- Password reset email functionality
- Bulk email sending for marketing campaigns
- Email tracking and analytics (open rates, click rates)
- Email template management system
- Unsubscribe functionality with one-click unsubscribe
- Email bounces and complaints handling
- Email scheduling for optimal delivery times
- Personalized email content based on user preferences
```

## 📊 Analytics and Reporting

### Prompt 11: Analytics Dashboard Backend

```
Create analytics and reporting backend services:
- Job posting analytics (views, applications, conversion rates)
- User engagement metrics and tracking
- Company performance analytics
- Search analytics and popular keywords
- Application funnel analysis
- Geographic analytics for job distribution
- Time-series data collection and aggregation
- Custom dashboard widgets and KPIs
- Report generation with filtering and grouping
- Data export functionality (CSV, PDF, Excel)
- Real-time analytics with WebSocket updates
- A/B testing framework for feature testing
- User behavior tracking and heatmaps
- Performance monitoring and alerting
```

### Prompt 12: Notification System

```
Develop a comprehensive notification system:
- In-app notifications for user actions
- Push notifications for mobile applications
- Email notifications with template management
- SMS notifications for urgent updates
- Notification preferences and settings
- Notification history and read/unread status
- Real-time notifications with WebSocket
- Notification batching and scheduling
- Template-based notification system
- Multi-language notification support
- Notification analytics and delivery tracking
- Webhook notifications for third-party integrations
- Notification queue management with priorities
- Notification retry mechanisms for failed deliveries
```

## 🧪 Testing and Quality Assurance

### Prompt 13: Comprehensive Testing Suite

```
Create a complete testing framework:
- Unit tests for models, views, and utility functions
- Integration tests for API endpoints
- Authentication and authorization testing
- Database transaction testing
- File upload and media handling tests
- Email functionality testing with mock services
- Celery task testing with test workers
- Performance testing for high-load scenarios
- Security testing for common vulnerabilities
- API documentation testing with Swagger validation
- Mock external services for isolated testing
- Test data factories using Factory Boy
- Coverage reporting and quality metrics
- Continuous testing with GitHub Actions
```

### Prompt 14: API Documentation and Swagger Integration

```
Implement comprehensive API documentation:
- Swagger/OpenAPI 3.0 specification generation
- Interactive API documentation with Swagger UI
- API endpoint documentation with request/response examples
- Authentication documentation with JWT examples
- Error response documentation with status codes
- Rate limiting documentation
- Pagination documentation with cursor-based examples
- File upload documentation with multipart examples
- API versioning documentation
- SDK generation for popular programming languages
- Postman collection generation
- API changelog and versioning strategy
- Developer portal with getting started guides
- Code examples in multiple programming languages
```

## 🚀 Deployment and DevOps

### Prompt 15: CI/CD Pipeline Setup

```
Create comprehensive CI/CD pipelines:
- GitHub Actions workflow for automated testing
- Docker image building and optimization
- Multi-stage Docker builds for production
- Database migration automation
- Environment-specific deployment configurations
- Health checks and readiness probes
- Rolling deployment strategy with zero downtime
- Automated backup and restore procedures
- Environment variable management and secrets
- Performance monitoring and alerting setup
- Log aggregation and monitoring
- Blue-green deployment strategy
- Database seeding and fixture management
- Static asset deployment to CDN
```

### Prompt 16: Production Deployment Configuration

```
Set up production-ready deployment infrastructure:
- Docker Compose production configuration
- Load balancer configuration with Nginx
- SSL/TLS certificate management with Let's Encrypt
- Database connection pooling with PgBouncer
- Redis cluster configuration for high availability
- RabbitMQ clustering for message queue reliability
- Monitoring setup with Prometheus and Grafana
- Log management with ELK stack (Elasticsearch, Logstash, Kibana)
- Backup strategies for database and media files
- Disaster recovery procedures
- Performance optimization and tuning
- Security hardening and firewall configuration
- CDN configuration for static assets
- Domain and DNS management
```

## 🔍 Advanced Features

### Prompt 17: Machine Learning Integration

```
Implement AI/ML features for job matching:
- Job recommendation system based on user profiles
- Skills matching algorithm with similarity scoring
- Resume parsing and skill extraction
- Job description analysis and categorization
- Salary prediction models based on job attributes
- User behavior analysis for personalization
- Content-based and collaborative filtering
- Natural language processing for job descriptions
- Automated job categorization and tagging
- Duplicate job detection and merging
- Sentiment analysis for company reviews
- Predictive analytics for hiring success
- A/B testing framework for ML model comparison
- Model versioning and deployment strategies
```

### Prompt 18: Advanced User Features

```
Develop advanced user experience features:
- User onboarding flow with progressive profiling
- Skills assessment and certification system
- Portfolio and project showcase functionality
- Interview scheduling and management system
- Video interview integration with third-party services
- Career path recommendations and planning
- Salary negotiation tools and market data
- Professional networking features
- Mentorship matching system
- Learning resources and course recommendations
- Achievement and badge system
- Social login integration (Google, LinkedIn, GitHub)
- Multi-language support with internationalization
- Accessibility features and compliance
```

## 📱 API Integration and Third-party Services

### Prompt 19: External API Integrations

```
Implement third-party service integrations:
- LinkedIn API for profile import and job posting
- Indeed API for job aggregation and posting
- Google Maps API for location services and geocoding
- Payment gateway integration for premium features
- Social media APIs for job sharing
- Video conferencing API integration (Zoom, Google Meet)
- File storage integration with AWS S3/Google Cloud
- Analytics integration with Google Analytics
- Email service provider APIs (SendGrid, Mailgun)
- SMS service integration for notifications
- Background check API integration
- Credit scoring API for financial roles
- Calendar integration for interview scheduling
- Webhook management for real-time updates
```

### Prompt 20: Performance Optimization

```
Implement comprehensive performance optimizations:
- Database query optimization with indexes and analysis
- API response time optimization with caching layers
- Image optimization and lazy loading implementation
- Database connection pooling and optimization
- Async view implementation for I/O bound operations
- Memory usage optimization and garbage collection tuning
- CDN implementation for static asset delivery
- Database sharding strategy for horizontal scaling
- Read replica configuration for database scaling
- Application profiling and bottleneck identification
- Resource monitoring and auto-scaling configuration
- Code splitting and lazy loading for frontend assets
- HTTP/2 and compression optimization
- Database vacuum and maintenance automation
```

## 🛠 Maintenance and Monitoring

### Prompt 21: System Monitoring and Alerting

```
Set up comprehensive system monitoring:
- Application performance monitoring (APM) with New Relic/Datadog
- Database performance monitoring and slow query analysis
- Redis monitoring and memory usage tracking
- Celery task monitoring and queue length alerts
- Error tracking and exception monitoring with Sentry
- Uptime monitoring with health check endpoints
- Custom business metrics and KPI tracking
- Log analysis and anomaly detection
- Security monitoring and intrusion detection
- Resource utilization monitoring (CPU, memory, disk)
- API response time and error rate monitoring
- User activity and engagement monitoring
- Automated alerting with escalation procedures
- Dashboard creation for different stakeholder groups
```

### Prompt 22: Data Management and Analytics

```
Implement data management and analytics infrastructure:
- Data warehouse setup for analytics and reporting
- ETL pipelines for data processing and transformation
- Data backup and archival strategies
- GDPR compliance and data privacy implementation
- Data retention policies and automated cleanup
- Data export functionality for users and compliance
- Anonymous data collection for analytics
- Data quality monitoring and validation
- Master data management for consistent data
- Data migration tools and procedures
- Search indexing with Elasticsearch for complex queries
- Data versioning and change tracking
- Audit trail implementation for compliance
- Data anonymization for testing environments
```

---

## 🎯 Implementation Order Recommendation

1. **Foundation** (Prompts 1-3): Project setup, authentication, database models
2. **Core Features** (Prompts 4-6): Job management, company system, search functionality  
3. **Security & Performance** (Prompts 7-8): Rate limiting, caching strategies
4. **Background Processing** (Prompts 9-10): Celery setup, email services
5. **Analytics & Notifications** (Prompts 11-12): Reporting system, notifications
6. **Quality Assurance** (Prompts 13-14): Testing framework, API documentation
7. **Deployment** (Prompts 15-16): CI/CD pipelines, production setup
8. **Advanced Features** (Prompts 17-18): ML integration, advanced user features
9. **Integrations** (Prompts 19-20): Third-party APIs, performance optimization
10. **Operations** (Prompts 21-22): Monitoring, data management

Each prompt is designed to be self-contained while building upon previous implementations. Use them sequentially or adapt specific prompts based on your immediate needs.
