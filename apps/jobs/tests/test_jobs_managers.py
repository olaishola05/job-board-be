from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.companies.models import Company, Industry
from apps.jobs.models import Job, JobApplication, JobCategory, Skill
from decimal import Decimal

User = get_user_model()


class PublishedJobManagerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='testpass123',
            role='employer'
        )
        
        self.industry = Industry.objects.create(
            name='Technology',
            slug='technology'
        )
        
        self.company = Company.objects.create(
            name='Tech Corp',
            description='A tech company',
            location='San Francisco',
            created_by=self.user,
            industry=self.industry
        )
        
        self.category = JobCategory.objects.create(
            name='Software Engineering',
            slug='software-engineering'
        )
        
        # Create published job
        self.published_job = Job.objects.create(
            title='Python Developer',
            slug='python-developer-published',
            description='Job description',
            requirements='Job requirements',
            responsibilities='Job responsibilities',
            company=self.company,
            category=self.category,
            industry=self.industry,
            created_by=self.user,
            job_type='full_time',
            experience_level='mid',
            location='San Francisco',
            status='published',
            published_at=timezone.now(),
            is_featured=True,
            remote_allowed=True,
            salary_min=Decimal('80000'),
            salary_max=Decimal('120000')
        )
        
        # Create draft job
        self.draft_job = Job.objects.create(
            title='Java Developer',
            slug='java-developer-draft',
            description='Job description',
            requirements='Job requirements',
            responsibilities='Job responsibilities',
            company=self.company,
            created_by=self.user,
            job_type='full_time',
            experience_level='senior',
            location='New York',
            status='draft'
        )
        
        # Create expired job
        self.expired_job = Job.objects.create(
            title='JavaScript Developer',
            slug='js-developer-expired',
            description='Job description',
            requirements='Job requirements',
            responsibilities='Job responsibilities',
            company=self.company,
            created_by=self.user,
            job_type='full_time',
            experience_level='mid',
            location='Boston',
            status='published',
            published_at=timezone.now(),
            application_deadline=timezone.now() - timezone.timedelta(days=1)
        )
    
    def test_published_manager_get_queryset(self):
        """Test published manager returns only published jobs"""
        published_jobs = Job.published.all()
        
        self.assertIn(self.published_job, published_jobs)
        self.assertIn(self.expired_job, published_jobs)  # Published but expired
        self.assertNotIn(self.draft_job, published_jobs)
    
    def test_published_manager_active(self):
        """Test active method returns only non-expired jobs"""
        active_jobs = Job.published.active()
        
        self.assertIn(self.published_job, active_jobs)
        self.assertNotIn(self.expired_job, active_jobs)  # Expired
        self.assertNotIn(self.draft_job, active_jobs)  # Not published
    
    def test_published_manager_featured(self):
        """Test featured method returns only featured jobs"""
        featured_jobs = Job.published.featured()
        
        self.assertIn(self.published_job, featured_jobs)
        self.assertNotIn(self.expired_job, featured_jobs)  # Not featured
        self.assertNotIn(self.draft_job, featured_jobs)  # Not published
    
    def test_published_manager_by_location(self):
        """Test by_location method"""
        sf_jobs = Job.published.by_location('San Francisco')
        
        self.assertIn(self.published_job, sf_jobs)
        self.assertNotIn(self.expired_job, sf_jobs)  # Different location
    
    def test_published_manager_by_location_remote(self):
        """Test by_location includes remote jobs"""
        ny_jobs = Job.published.by_location('New York')
        
        # Should include remote job even if not in NY
        self.assertIn(self.published_job, ny_jobs)  # Remote allowed
    
    def test_published_manager_by_salary_range(self):
        """Test by_salary_range method"""
        # Test minimum salary filter
        high_salary_jobs = Job.published.by_salary_range(min_salary=Decimal('70000'))
        self.assertIn(self.published_job, high_salary_jobs)
        
        # Test maximum salary filter
        low_salary_jobs = Job.published.by_salary_range(max_salary=Decimal('100000'))
        self.assertNotIn(self.published_job, low_salary_jobs)  # Max salary too high
        
        # Test range filter
        range_jobs = Job.published.by_salary_range(
            min_salary=Decimal('75000'),
            max_salary=Decimal('150000')
        )
        self.assertIn(self.published_job, range_jobs)
    
    def test_published_manager_with_company_info(self):
        """Test with_company_info method uses select_related"""
        jobs = Job.published.with_company_info()
        
        # This test verifies the method exists and returns a queryset
        # In a real scenario, you'd check that select_related is used
        # by examining the query or using Django's connection queries
        self.assertTrue(jobs.exists())
        
        job = jobs.first()
        # These should not trigger additional queries if select_related works
        company_name = job.company.name
        industry_name = job.industry.name if job.industry else None
        
        self.assertIsNotNone(company_name)


class JobApplicationManagerTest(TestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='testpass123',
            role='employer'
        )
        
        self.job_seeker1 = User.objects.create_user(
            username='jobseeker1',
            email='jobseeker1@example.com',
            password='testpass123'
        )
        
        self.job_seeker2 = User.objects.create_user(
            username='jobseeker2',
            email='jobseeker2@example.com',
            password='testpass123'
        )
        
        self.company = Company.objects.create(
            name='Tech Corp',
            description='A tech company',
            location='San Francisco',
            created_by=self.employer
        )
        
        self.job = Job.objects.create(
            title='Python Developer',
            slug='python-developer-app-test',
            description='Job description',
            requirements='Job requirements',
            responsibilities='Job responsibilities',
            company=self.company,
            created_by=self.employer,
            job_type='full_time',
            experience_level='mid',
            location='San Francisco',
            status='published'
        )
        
        # Create applications with different statuses
        self.pending_app = JobApplication.objects.create(
            job=self.job,
            applicant=self.job_seeker1,
            status='pending'
        )
        
        self.review_app = JobApplication.objects.create(
            job=self.job,
            applicant=self.job_seeker2,
            status='under_review'
        )
    
    def test_application_manager_pending(self):
        """Test pending method"""
        pending_apps = JobApplication.objects.pending()
        
        self.assertIn(self.pending_app, pending_apps)
        self.assertNotIn(self.review_app, pending_apps)
    
    def test_application_manager_under_review(self):
        """Test under_review method"""
        review_apps = JobApplication.objects.under_review()
        
        self.assertIn(self.review_app, review_apps)
        self.assertNotIn(self.pending_app, review_apps)
    
    def test_application_manager_by_user(self):
        """Test by_user method"""
        user1_apps = JobApplication.objects.by_user(self.job_seeker1)
        user2_apps = JobApplication.objects.by_user(self.job_seeker2)
        
        self.assertIn(self.pending_app, user1_apps)
        self.assertNotIn(self.review_app, user1_apps)
        
        self.assertIn(self.review_app, user2_apps)
        self.assertNotIn(self.pending_app, user2_apps)
    
    def test_application_manager_by_company(self):
        """Test by_company method"""
        company_apps = JobApplication.objects.by_company(self.company)
        
        self.assertIn(self.pending_app, company_apps)
        self.assertIn(self.review_app, company_apps)
        
        # Create another company and verify filtering
        other_company = Company.objects.create(
            name='Other Corp',
            description='Another company',
            location='New York',
            created_by=self.employer
        )
        
        other_company_apps = JobApplication.objects.by_company(other_company)
        self.assertEqual(other_company_apps.count(), 0)

