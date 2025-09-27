from django.core.management.base import BaseCommand
from apps.companies.models import Company, CompanyFollow, CompanyReview
from apps.jobs.models import Job, JobApplication, User
from scripts.seed_data import (
    create_users,
    create_industries,
    create_skill_categories_and_skills,
    create_job_categories,
    create_companies,
    create_jobs,
    create_reviews,
    create_follows,
    create_applications
)

class Command(BaseCommand):
    help = 'Seed the database with initial data'

    def handle(self, *args, **options):
        admin, employers, users = create_users()
        industries = create_industries()
        create_skill_categories_and_skills()
        categories = create_job_categories()
        companies = create_companies(employers, industries)
        jobs = create_jobs(companies, categories, employers)
        create_reviews(companies, users)
        create_follows(companies, users)
        create_applications(jobs, users)
        
        
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.stdout.write(self.style.SUCCESS(f"Users: {User.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"Companies: {Company.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"Jobs: {Job.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"Applications: {JobApplication.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"Reviews: {CompanyReview.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"Follows: {CompanyFollow.objects.count()}"))  