import os
import sys
import django
from django.core.management.base import BaseCommand
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_platform.settings')
django.setup()

from apps.accounts.models import User
from apps.companies.models import Company, CompanyReview, CompanyFollow
from apps.jobs.models import Job, JobCategory, JobType, Skill, SkillCategory, JobApplication, Industry

def create_users():
    """Create test users"""
    # Admin user
    admin = User.objects.create_user(
        email='admin@jobboard.com',
        username='admin',
        password='admin123@',
        first_name='Admin',
        last_name='User',
        role='admin',
        is_verified=True,
        is_staff=True,
        is_superuser=True
    )
    
    # Employers
    employers = []
    for i in range(5):
        employer = User.objects.create_user(
            email=f'employer{i+1}@company.com',
            username=f'employer{i+1}',
            password='employer123@',
            first_name=f'Employer{i+1}',
            last_name='Manager',
            role='employer',
            is_verified=True
        )
        employers.append(employer)
    
    # Job users
    users = []
    for i in range(10):
        user = User.objects.create_user(
            email=f'user{i+1}@email.com',
            username=f'user{i+1}',
            password='seeker123@',
            first_name=f'Job{i+1}',
            last_name='Seeker',
            role='user',
            is_verified=True
        )
        users.append(user)
    
    return admin, employers, users

def create_industries():
    """Create industries"""
    industries_data = [
        ('Technology', 'Software, Hardware, IT Services'),
        ('Finance', 'Banking, Insurance, Fintech'),
        ('Healthcare', 'Medical, Pharmaceutical, Wellness'),
        ('Education', 'Schools, Universities, Training'),
        ('Manufacturing', 'Production, Assembly, Industrial'),
        ('Retail', 'Sales, E-commerce, Consumer Goods'),
        ('Marketing', 'Advertising, Digital Marketing, PR'),
        ('Construction', 'Building, Infrastructure, Real Estate'),
    ]
    
    industries = []
    for name, description in industries_data:
        industry = Industry.objects.create(
            name=name,
            description=description,
            is_active=True
        )
        industries.append(industry)
    
    return industries

def create_skill_categories_and_skills():
    """Create skill categories and skills"""
    categories_data = {
        'Programming': [
            'Python', 'JavaScript', 'Java', 'C++', 'PHP', 'Ruby', 'Go', 'Swift'
        ],
        'Web Development': [
            'HTML', 'CSS', 'React', 'Vue.js', 'Angular', 'Node.js', 'Django', 'Laravel'
        ],
        'Design': [
            'Photoshop', 'Figma', 'Sketch', 'Illustrator', 'UI/UX Design', 'Graphic Design'
        ],
        'Data Science': [
            'Machine Learning', 'Data Analysis', 'SQL', 'Tableau', 'Power BI', 'R'
        ],
        'Marketing': [
            'SEO', 'SEM', 'Social Media Marketing', 'Content Marketing', 'Email Marketing'
        ]
    }
    
    for category_name, skills in categories_data.items():
        category = SkillCategory.objects.create(name=category_name)
        for skill_name in skills:
            Skill.objects.create(name=skill_name, category=category)

def create_job_categories():
    """Create job categories"""
    categories_data = [
        'Software Development',
        'Data Science',
        'Design',
        'Marketing',
        'Sales',
        'Human Resources',
        'Finance',
        'Operations',
        'Customer Service',
        'Project Management'
    ]
    
    categories = []
    for name in categories_data:
        category = JobCategory.objects.create(name=name)
        categories.append(category)
    
    return categories

def create_companies(employers, industries):
    """Create companies"""
    companies_data = [
        {
            'name': 'TechCorp Nigeria',
            'description': 'Leading technology company in Nigeria specializing in software development and digital solutions.',
            'location': 'Lagos, Nigeria',
            'website': 'https://techcorp.ng',
            'company_size': 'large',
            'founded_year': 2010,
        },
        {
            'name': 'FinanceHub',
            'description': 'Premier financial services company providing banking and fintech solutions.',
            'location': 'Abuja, Nigeria',
            'website': 'https://financehub.com',
            'company_size': 'medium',
            'founded_year': 2015,
        },
        {
            'name': 'HealthPlus Medical',
            'description': 'Healthcare organization committed to providing quality medical services.',
            'location': 'Port Harcourt, Nigeria',
            'website': 'https://healthplus.ng',
            'company_size': 'medium',
            'founded_year': 2012,
        },
        {
            'name': 'EduTech Solutions',
            'description': 'Educational technology company revolutionizing learning in Africa.',
            'location': 'Ibadan, Nigeria',
            'website': 'https://edutech.ng',
            'company_size': 'small',
            'founded_year': 2018,
        },
        {
            'name': 'ManufacturePro',
            'description': 'Manufacturing company producing quality goods for local and international markets.',
            'location': 'Kano, Nigeria',
            'website': 'https://manufacturepro.ng',
            'company_size': 'large',
            'founded_year': 2005,
        }
    ]
    
    companies = []
    for i, data in enumerate(companies_data):
        company = Company.objects.create(
            **data,
            industry=industries[i % len(industries)],
            created_by=employers[i % len(employers)],
            approval_status='approved',
            is_verified=True,
            is_featured=i < 2,
            rating=Decimal(str(4.0 + (i * 0.2)))
        )
        companies.append(company)
    
    return companies

def create_jobs(companies, categories, employers):
    """Create job postings"""
    jobs_data = [
        {
            'title': 'Senior Python Developer',
            'description': 'We are looking for an experienced Python developer to join our team.',
            'requirements': 'Bachelor\'s degree, 5+ years Python experience, Django knowledge',
            'responsibilities': 'Develop web applications, mentor junior developers, code reviews',
            'job_type': 'full_time',
            'experience_level': 'senior',
            'location': 'Lagos, Nigeria',
            'salary_min': 800000,
            'salary_max': 1200000,
            'status': 'published'
        },
        {
            'title': 'Frontend Developer',
            'description': 'Join our frontend team to build amazing user interfaces.',
            'requirements': 'React, JavaScript, HTML/CSS, 3+ years experience',
            'responsibilities': 'Build responsive UIs, collaborate with designers, optimize performance',
            'job_type': 'full_time',
            'experience_level': 'mid',
            'location': 'Lagos, Nigeria',
            'salary_min': 600000,
            'salary_max': 900000,
            'status': 'published'
        },
        {
            'title': 'Data Analyst',
            'description': 'Analyze data to drive business insights and decisions.',
            'requirements': 'SQL, Excel, Python/R, statistics background',
            'responsibilities': 'Create reports, analyze trends, present findings to stakeholders',
            'job_type': 'full_time',
            'experience_level': 'mid',
            'location': 'Abuja, Nigeria',
            'salary_min': 500000,
            'salary_max': 750000,
            'status': 'published'
        },
        {
            'title': 'UI/UX Designer',
            'description': 'Design intuitive and beautiful user experiences.',
            'requirements': 'Figma, Sketch, design portfolio, 2+ years experience',
            'responsibilities': 'Create wireframes, design mockups, conduct user research',
            'job_type': 'full_time',
            'experience_level': 'junior',
            'location': 'Lagos, Nigeria',
            'salary_min': 400000,
            'salary_max': 650000,
            'status': 'published'
        },
        {
            'title': 'Marketing Manager',
            'description': 'Lead our marketing efforts and grow our brand presence.',
            'requirements': 'Marketing degree, 4+ years experience, digital marketing skills',
            'responsibilities': 'Develop marketing strategy, manage campaigns, analyze ROI',
            'job_type': 'full_time',
            'experience_level': 'senior',
            'location': 'Lagos, Nigeria',
            'salary_min': 700000,
            'salary_max': 1000000,
            'status': 'published'
        }
    ]
    
    jobs = []
    for i, data in enumerate(jobs_data):
        job = Job.objects.create(
            **data,
            company=companies[i % len(companies)],
            category=categories[i % len(categories)],
            industry=companies[i % len(companies)].industry,
            created_by=employers[i % len(employers)]
        )
        jobs.append(job)
    
    return jobs

def create_reviews(companies, users):
    """Create company reviews"""
    reviews_data = [
        {
            'rating': 5,
            'title': 'Great place to work',
            'content': 'Excellent work environment and growth opportunities.',
            'pros': 'Good salary, flexible hours, nice colleagues',
            'cons': 'Sometimes high pressure deadlines',
            'employment_status': 'current'
        },
        {
            'rating': 4,
            'title': 'Good company culture',
            'content': 'Really enjoy the team and the projects we work on.',
            'pros': 'Learning opportunities, modern tech stack',
            'cons': 'Limited remote work options',
            'employment_status': 'former'
        },
        {
            'rating': 4,
            'title': 'Solid workplace',
            'content': 'Professional environment with good benefits.',
            'pros': 'Health insurance, career development',
            'cons': 'Could improve work-life balance',
            'employment_status': 'current'
        }
    ]
    
    for i, data in enumerate(reviews_data):
        CompanyReview.objects.create(
            **data,
            company=companies[i % len(companies)],
            user=users[i % len(users)]
        )

def create_follows(companies, users):
    """Create company follows"""
    for i, user in enumerate(users[:6]):
        CompanyFollow.objects.create(
            company=companies[i % len(companies)],
            user=user,
            notifications_enabled=True
        )

def create_applications(jobs, users):
    """Create job applications"""
    statuses = ['pending', 'under_review', 'accepted', 'rejected']
    
    for i, job in enumerate(jobs):
        # Create 2-3 applications per job
        for j in range(2 + (i % 2)):
            seeker_idx = (i * 2 + j) % len(users)
            JobApplication.objects.create(
                job=job,
                applicant=users[seeker_idx],
                cover_letter=f'I am very interested in the {job.title} position at {job.company.name}.',
                status=statuses[j % len(statuses)]
            )

def run_seed():
    """Main function to run all seed operations"""
    print("Creating users...")
    admin, employers, users = create_users()
    
    print("Creating industries...")
    industries = create_industries()
    
    print("Creating skills...")
    create_skill_categories_and_skills()
    
    print("Creating job categories...")
    categories = create_job_categories()
    
    print("Creating companies...")
    companies = create_companies(employers, industries)
    
    print("Creating jobs...")
    jobs = create_jobs(companies, categories, employers)
    
    print("Creating reviews...")
    create_reviews(companies, users)
    
    print("Creating follows...")
    create_follows(companies, users)
    
    print("Creating applications...")
    create_applications(jobs, users)
    
    print("\nSeed data created successfully!")
    print(f"Users: {User.objects.count()}")
    print(f"Companies: {Company.objects.count()}")
    print(f"Jobs: {Job.objects.count()}")
    print(f"Applications: {JobApplication.objects.count()}")
    print(f"Reviews: {CompanyReview.objects.count()}")

if __name__ == '__main__':
    run_seed()