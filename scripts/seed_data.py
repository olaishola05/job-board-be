import os
import sys
import django
from django.core.management.base import BaseCommand
from decimal import Decimal
import random

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
        username='admin_sd',
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
    for i in range(20):
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
    for i in range(50):
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
        ('Transportation', 'Logistics, Shipping, Delivery'),
        ('Hospitality', 'Hotels, Restaurants, Travel'),
        ('Energy', 'Oil & Gas, Renewable Energy, Utilities'),
        ('Telecommunications', 'Mobile, Internet, Networking'),
        ('Entertainment', 'Media, Film, Music, Gaming'),
        ('Non-Profit', 'Charities, NGOs, Social Services'),
        ('Government', 'Public Sector, Administration, Policy'),
        ('Agriculture', 'Farming, Agribusiness, Food Production'),
        ('Legal', 'Law Firms, Corporate Law, Legal Services'),
        ('Consulting', 'Business Consulting, Strategy, Advisory'),
        ('Automotive', 'Car Manufacturing, Dealerships, Services'),
        ('Aerospace', 'Aviation, Space Exploration, Defense'),
        ('Real Estate', 'Property Management, Brokerage, Development'),
        ('Media', 'Publishing, Journalism, Broadcasting'),
        ('Pharmaceuticals', 'Drug Development, Research, Sales'),
        ('Biotechnology', 'Bio Research, Genetics, Life Sciences'),
        ('Fashion', 'Apparel, Design, Retail'),
        ('Food & Beverage', 'Restaurants, Food Production, Catering'),
        ('Sports', 'Athletics, Sports Management, Fitness'),
        ('Travel & Tourism', 'Tour Operators, Travel Agencies, Tourism Boards'),
        ('Human Resources', 'Recruitment, Staffing, HR Services'),
        ('Arts & Culture', 'Museums, Galleries, Cultural Institutions')
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
        ],
        'Project Management': [
            'Agile', 'Scrum', 'Kanban', 'JIRA', 'Trello', 'Asana'
        ],
        'Business': [
            'Sales', 'Negotiation', 'Customer Service', 'Business Development', 'CRM'
        ],
        'Soft Skills': [
            'Communication', 'Leadership', 'Time Management', 'Problem Solving', 'Teamwork'
        ],
        'Cloud & DevOps': [
            'AWS', 'Azure', 'Docker', 'Kubernetes', 'CI/CD', 'Terraform'
        ],
        'Mobile Development': [
            'iOS Development', 'Android Development', 'React Native', 'Flutter'
        ],
        'Cybersecurity': [
            'Network Security', 'Ethical Hacking', 'Penetration Testing', 'Information Security'
        ],
        'Languages': [
            'English', 'Spanish', 'French', 'German', 'Chinese', 'Arabic'
        ],
        'Finance & Accounting': [
            'Financial Analysis', 'Accounting', 'Bookkeeping', 'Taxation', 'Auditing'
        ],
        'Writing & Content': [
            'Copywriting', 'Technical Writing', 'Blogging', 'Editing', 'Proofreading'
        ],
        'Education & Training': [
            'Curriculum Development', 'E-learning', 'Instructional Design', 'Teaching'
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
        'Project Management',
        'Education',
        'Healthcare',
        'Engineering',
        'Legal',
        'Writing & Content',
        'Product Management',
        'Quality Assurance',
        'DevOps',
        'IT Support',
        'Business Development',
        'Consulting',
        'Manufacturing',
        'Logistics',
        'Real Estate',
        'Hospitality',
        'Arts & Culture',
        'Science & Research',
        'Telecommunications',
        'Non-Profit',
        'Government',
        'Agriculture'
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
        },
        {
            'name': 'RetailWorld',
            'description': 'Leading retail chain offering a wide range of consumer products.',
            'location': 'Lagos, Nigeria',
            'website': 'https://retailworld.ng',
            'company_size': 'large',
            'founded_year': 2000,
        },
        {
            'name': 'MarketGurus',
            'description': 'Digital marketing agency helping businesses grow their online presence.',
            'location': 'Lagos, Nigeria',
            'website': 'https://marketgurus.ng',
            'company_size': 'small',
            'founded_year': 2016,
        },
        {
            'name': 'BuildIt Construction',
            'description': 'Construction company specializing in residential and commercial projects.',
            'location': 'Abuja, Nigeria',
            'website': 'https://buildit.ng',
            'company_size': 'medium',
            'founded_year': 2011,
        },
        {
            'name': 'FastTrack Logistics',
            'description': 'Logistics and transportation company providing efficient delivery solutions.',
            'location': 'Lagos, Nigeria',
            'website': 'https://fasttracklogistics.ng',
            'company_size': 'medium',
            'founded_year': 2013,
        },
        {
            'name': 'HospitalityPlus',
            'description': 'Hospitality group managing hotels and restaurants across Nigeria.',
            'location': 'Lagos, Nigeria',
            'website': 'https://hospitalityplus.ng',
            'company_size': 'large',
            'founded_year': 2008,
        },
        {
            'name': 'GreenEnergy Solutions',
            'description': 'Renewable energy company focused on solar and wind power projects.',
            'location': 'Abuja, Nigeria',
            'website': 'https://greenenergy.ng',
            'company_size': 'small',
            'founded_year': 2017,
        },
        {
            'name': 'TelecomConnect',
            'description': 'Telecommunications provider offering mobile and internet services.',
            'location': 'Lagos, Nigeria',
            'website': 'https://telecomconnect.ng',
            'company_size': 'large',
            'founded_year': 2003,
        },
        {
            'name': 'MediaWorks',
            'description': 'Media production company creating content for TV, film, and digital platforms.',
            'location': 'Lagos, Nigeria',
            'website': 'https://mediaworks.ng',
            'company_size': 'medium',
            'founded_year': 2014,
        },
        {
            'name': 'NonProfit Aid',
            'description': 'Non-profit organization dedicated to community development and social services.',
            'location': 'Abuja, Nigeria',
            'website': 'https://nonprofitaid.ng',
            'company_size': 'small',
            'founded_year': 2010,
        },
        {
            'name': 'GovTech Solutions',
            'description': 'Government contractor providing IT and consulting services to public sector clients.',
            'location': 'Lagos, Nigeria',
            'website': 'https://govtech.ng',
            'company_size': 'medium',
            'founded_year': 2009,
        },
        {
            'name': 'AgriFarm Ltd.',
            'description': 'Agriculture company focused on sustainable farming and food production.',
            'location': 'Kaduna, Nigeria',
            'website': 'https://agrifarm.ng',
            'company_size': 'medium',
            'founded_year': 2012,
        },
        {
            'name': 'LegalEase',
            'description': 'Law firm providing corporate and individual legal services.',
            'location': 'Lagos, Nigeria',
            'website': None,
            'company_size': 'small',
            'founded_year': 2011,
        },
        {
            'name': 'ConsultCorp',
            'description': "Business consulting firm helping companies improve performance and strategy.",
            'location': 'Lagos, Nigeria',
            'website': 'https://consultcorp.ng',
            'company_size': 'medium',
            'founded_year': 2013,
        },
        {
            'name': 'AutoDrive',
            'description': 'Automotive company specializing in car sales and services.',
            'location': 'Lagos, Nigeria',
            'website': 'https://autodrive.ng',
            'company_size': 'large',
            'founded_year': 2015,
        },
        {
            'name': 'AeroSpace Innovations',
            'description': 'Aerospace company involved in aviation and defense projects.',
            'location': 'Abuja, Nigeria',
            'website': 'https://aerospace.ng',
            'company_size': 'small',
            'founded_year': 2016,
        },
        {
            'name': 'RealEstate Pros',
            'description': 'Real estate agency offering property sales and management services.',
            'location': 'Lagos, Nigeria',
            'website': 'https://realestatepros.ng',
            'company_size': 'large',
            'founded_year': 2018,
        },
        {
            'name': 'PharmaLife',
            'description': 'Pharmaceutical company engaged in drug development and healthcare products.',
            'location': 'Lagos, Nigeria',
            'website': 'https://pharmalife.ng',
            'company_size': 'large',
            'founded_year': 2019,
        },
        {
            'name': 'BioGen Labs',
            'description': 'Biotechnology research company focused on genetic and life sciences.',
            'location': 'Lagos, Nigeria',
            'website': 'https://biogenlabs.ng',
            'company_size': 'large',
            'founded_year': 2020,
        },
        {
            'name': 'Fashionista',
            'description': 'Fashion brand designing and retailing trendy apparel and accessories.',
            'location': 'Lagos, Nigeria',
            'website': 'https://fashionista.ng',
            'company_size': 'medium',
            'founded_year': 2014,
        },
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
        },
        {
            'title': 'Sales Executive',
            'description': 'Drive sales and build relationships with clients.',
            'requirements': 'Sales experience, excellent communication skills, target-driven',
            'responsibilities': 'Identify leads, close deals, maintain client relationships',
            'job_type': 'full_time',
            'experience_level': 'mid',
            'location': 'Lagos, Nigeria',
            'salary_min': 500000,
            'salary_max': 800000,
            'status': 'published'
        },
        {
            'title': 'HR Specialist',
            'description': 'Manage recruitment and employee relations.',
            'requirements': 'HR degree, 3+ years experience, knowledge of labor laws',
            'responsibilities': 'Recruitment, employee onboarding, conflict resolution',
            'job_type': 'full_time',
            'experience_level': 'mid',
            'location': 'Abuja, Nigeria',
            'salary_min': 450000,
            'salary_max': 700000,
            'status': 'published'
        },
        {
            'title': 'Financial Analyst',
            'description': 'Provide financial insights to support business decisions.',
            'requirements': 'Finance degree, Excel skills, analytical mindset',
            'responsibilities': 'Financial modeling, budgeting, reporting',
            'job_type': 'full_time',
            'experience_level': 'mid',
            'location': 'Lagos, Nigeria',
            'salary_min': 600000,
            'salary_max': 850000,
            'status': 'published'
        },
        {
            'title': 'Operations Manager',
            'description': 'Oversee daily operations and improve efficiency.',
            'requirements': 'Operations experience, leadership skills, problem-solving ability',
            'responsibilities': 'Manage teams, optimize processes, ensure quality control',
            'job_type': 'full_time',
            'experience_level': 'senior',
            'location': 'Lagos, Nigeria',
            'salary_min': 750000,
            'salary_max': 1100000,
            'status': 'published'
        },
        {
            'title': 'Customer Service Representative',
            'description': "Provide excellent service to our customers and resolve their issues.",
            'requirements': "Communication skills, patience, problem-solving skills",
            'responsibilities': "Handle customer inquiries, resolve complaints, maintain customer satisfaction",
            'job_type': 'full_time',
            'experience_level': 'junior',
            'location': 'Lagos, Nigeria',
            'salary_min': 300000,
            'salary_max': 450000,
            'status': 'published'
        },
        
        {
            'title': 'Project Manager',
            'description': 'Lead projects from initiation to closure, ensuring timely delivery.',
            'requirements': 'PMP certification, Agile/Scrum knowledge, leadership skills',
            'responsibilities': 'Define project scope, manage resources, communicate with stakeholders',
            'job_type': 'full_time',
            'experience_level': 'senior',
            'location': 'Lagos, Nigeria',
            'salary_min': 800000,
            'salary_max': 1200000,
            'status': 'published'
        },
        {
            'title': 'Content Writer',
            'description': 'Create engaging content for our blog and marketing materials.',
            'requirements': 'Excellent writing skills, SEO knowledge, creativity',
            'responsibilities': 'Write articles, create marketing copy, collaborate with marketing team',
            'job_type': 'full_time',
            'experience_level': 'junior',
            'location': 'Remote',
            'salary_min': 350000,
            'salary_max': 500000,
            'status': 'published'
        },
        {
            'title': 'Quality Assurance Engineer',
            'description': 'Ensure the quality of our software products through rigorous testing.',
            'requirements': 'Attention to detail, analytical skills, experience with testing tools',
            'responsibilities': 'Design test plans, execute tests, report bugs',
            'job_type': 'full_time',
            'experience_level': 'mid',
            'location': 'Lagos, Nigeria',
            'salary_min': 600000,
            'salary_max': 900000,
            'status': 'published'
        },
        {
            'title': 'DevOps Engineer',
            'description': 'Manage our infrastructure and deployment pipelines.',
            'requirements': 'Experience with AWS, Docker, Kubernetes, CI/CD tools',
            'responsibilities': 'Automate deployments, monitor systems, ensure reliability',
            'job_type': 'full_time',
            'experience_level': 'mid',
            'location': 'Lagos, Nigeria',
            'salary_min': 700000,
            'salary_max': 1000000,
            'status': 'published'
        },
        {
            'title': 'IT Support Specialist',
            'description': 'Provide technical support to our employees and resolve IT issues.',
            'requirements': 'Technical knowledge, problem-solving skills, customer service experience',
            'responsibilities': 'Troubleshoot issues, maintain hardware/software, assist users',
            'job_type': 'full_time',
            'experience_level': 'junior',
            'location': 'Lagos, Nigeria',
            'salary_min': 400000,
            'salary_max': 600000,
            'status': 'published'
        },
        {
            'title': 'Business Development Manager',
            'description': 'Identify growth opportunities and build strategic partnerships.',
            'requirements': 'Sales experience, networking skills, strategic thinking',
            'responsibilities': 'Generate leads, negotiate deals, develop business strategies',
            'job_type': 'full_time',
            'experience_level': 'senior',
            'location': 'Lagos, Nigeria',
            'salary_min': 800000,
            'salary_max': 1300000,
            'status': 'published'
        },
        {
            'title': 'Consultant',
            'description': "Provide expert advice to help clients improve their business performance.",
            'requirements': "Industry knowledge, analytical skills, communication skills",
            'responsibilities': "Analyze client needs, develop solutions, present recommendations",
            'job_type': "contract",
            'experience_level': "senior",
            'location': "Lagos, Nigeria",
            'salary_min': 1000000,
            'salary_max': 1500000,
            'status': "published"
        },
        {
            'title': "Mechanical Engineer",
            'description': "Design and oversee the manufacturing of mechanical devices.",
            'requirements': "Mechanical engineering degree, CAD skills, problem-solving ability",
            'responsibilities': "Create designs, test prototypes , collaborate with production teams",
            'job_type': "full_time",
            'experience_level': "mid",
            'location': "Lagos, Nigeria",
            'salary_min': 600000,
            'salary_max': 900000,
            'status': "published"
        },
        {
            'title': "Logistics Coordinator",
            'description': "Manage the supply chain and ensure timely delivery of goods.",
            'requirements': "Logistics experience, organizational skills, attention to detail",
            'responsibilities': "Coordinate shipments, manage inventory, liaise with suppliers",
            'job_type': "full_time",
            'experience_level': "junior",
            'location': "Lagos, Nigeria",
            'salary_min': 400000,
            'salary_max': 600000,
            'status': "published"
        },
        {
            'title': "Real Estate Agent",
            'description': "Assist clients in buying, selling, and renting properties.",
            'requirements': "Real estate license, sales skills, local market knowledge",
            'responsibilities': "Show properties, negotiate deals, manage client relationships",
            'job_type': "full_time",
            'experience_level': "mid",
            'location': "Lagos, Nigeria",
            'salary_min': 500000,
            'salary_max': 800000,
            'status': "published"
        },
    ]
    
    jobs = []
    for i, data in enumerate(jobs_data):
        all_skills = Skill.objects.all()
        job = Job.objects.create(
            **data,
            company=companies[i % len(companies)],
            category=categories[i % len(categories)],
            industry=companies[i % len(companies)].industry,
            created_by=employers[i % len(employers)]
        )
        
        if all_skills:
            job.skills.set(random.sample(list(all_skills), min(3, all_skills.count())))
            job.save()
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