from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import IntegrityError, transaction
from apps.companies.models import Company, Industry
from apps.jobs.models import (
    Job, JobCategory, JobApplication, SavedJob, JobView,
    JobAlert, JobType, Skill, SkillCategory
)
from decimal import Decimal

User = get_user_model()


class SkillCategoryModelTest(TestCase):
    def test_skill_category_creation(self):
        """Test skill category creation"""
        category = SkillCategory.objects.create(
            name='Programming Languages',
            slug='programming-languages',
            description='Various programming languages'
        )
        
        self.assertEqual(category.name, 'Programming Languages')
        self.assertEqual(category.slug, 'programming-languages')
        self.assertTrue(category.is_active)
    
    def test_skill_category_str_method(self):
        """Test skill category string representation"""
        category = SkillCategory.objects.create(
            name='Programming Languages',
            slug='programming-languages'
        )
        self.assertEqual(str(category), 'Programming Languages')
    
    def test_skill_category_slug_auto_generation(self):
        """Test automatic slug generation"""
        category = SkillCategory.objects.create(name='Web Development')
        self.assertEqual(category.slug, 'web-development')


class SkillModelTest(TestCase):
    def setUp(self):
        self.category = SkillCategory.objects.create(
            name='Programming',
            slug='programming'
        )
    
    def test_skill_creation(self):
        """Test skill creation"""
        skill = Skill.objects.create(
            name='Python',
            slug='python',
            category=self.category
        )
        
        self.assertEqual(skill.name, 'Python')
        self.assertEqual(skill.slug, 'python')
        self.assertEqual(skill.category, self.category)
        self.assertTrue(skill.is_active)
        self.assertEqual(skill.popularity_score, 0)
    
    def test_skill_str_method(self):
        """Test skill string representation"""
        skill = Skill.objects.create(name='Python', slug='python')
        self.assertEqual(str(skill), 'Python')
    
    def test_skill_slug_auto_generation(self):
        """Test automatic slug generation"""
        skill = Skill.objects.create(name='Machine Learning')
        self.assertEqual(skill.slug, 'machine-learning')


class JobCategoryModelTest(TestCase):
    def test_job_category_creation(self):
        """Test job category creation"""
        category = JobCategory.objects.create(
            name='Software Engineering',
            slug='software-engineering',
            description='Software development jobs'
        )
        
        self.assertEqual(category.name, 'Software Engineering')
        self.assertEqual(category.slug, 'software-engineering')
        self.assertTrue(category.is_active)
        self.assertIsNone(category.parent)
    
    def test_job_category_hierarchy(self):
        """Test parent-child relationship"""
        parent = JobCategory.objects.create(
            name='Technology',
            slug='technology'
        )
        
        child = JobCategory.objects.create(
            name='Software Development',
            slug='software-development',
            parent=parent
        )
        
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.subcategories.all())
    
    def test_job_category_str_method_with_parent(self):
        """Test string representation with parent"""
        parent = JobCategory.objects.create(name='Technology', slug='technology')
        child = JobCategory.objects.create(
            name='Software Development',
            slug='software-development',
            parent=parent
        )
        
        expected = 'Technology > Software Development'
        self.assertEqual(str(child), expected)


class JobTypeModelTest(TestCase):
    def test_job_type_creation(self):
        """Test job type creation"""
        job_type = JobType.objects.create(
            name='Full Time',
            slug='full-time',
            description='Full-time employment'
        )
        
        self.assertEqual(job_type.name, 'Full Time')
        self.assertEqual(job_type.slug, 'full-time')
        self.assertTrue(job_type.is_active)


class JobModelTest(TestCase):
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
        
        self.skill = Skill.objects.create(
            name='Python',
            slug='python'
        )
        
        self.job_data = {
            'title': 'Senior Python Developer',
            'description': 'Job description',
            'requirements': 'Job requirements',
            'responsibilities': 'Job responsibilities',
            'company': self.company,
            'category': self.category,
            'industry': self.industry,
            'created_by': self.user,
            'job_type': 'full_time',
            'experience_level': 'senior',
            'location': 'San Francisco',
            'salary_min': Decimal('80000.00'),
            'salary_max': Decimal('120000.00'),
            'status': 'published'
        }
    
    def test_job_creation(self):
        """Test job creation"""
        job = Job.objects.create(**self.job_data)
        
        self.assertEqual(job.title, 'Senior Python Developer')
        self.assertEqual(job.company, self.company)
        self.assertEqual(job.status, 'published')
        self.assertFalse(job.is_featured)
        self.assertFalse(job.remote_allowed)
        self.assertEqual(job.views_count, 0)
        self.assertEqual(job.applications_count, 0)
    
    def test_job_str_method(self):
        """Test job string representation"""
        job = Job.objects.create(**self.job_data)
        expected = f"{job.title} at {job.company.name}"
        self.assertEqual(str(job), expected)
    
    def test_job_slug_auto_generation(self):
        """Test automatic slug generation"""
        job = Job.objects.create(**self.job_data)
        expected_slug = 'senior-python-developer-tech-corp'
        self.assertEqual(job.slug, expected_slug)
    
    def test_job_slug_uniqueness(self):
        """Test slug uniqueness handling"""
        job1 = Job.objects.create(**self.job_data)
        job2 = Job.objects.create(**self.job_data)
        
        self.assertNotEqual(job1.slug, job2.slug)
        self.assertTrue(job2.slug.startswith('senior-python-developer-tech-corp'))
    
    def test_job_salary_validation(self):
        """Test salary range validation"""
        job_data = self.job_data.copy()
        job_data['salary_min'] = Decimal('120000.00')
        job_data['salary_max'] = Decimal('80000.00')  # Max < Min
        
        job = Job(**job_data)
        with self.assertRaises(ValidationError):
            job.full_clean()
    
    def test_job_is_active_property(self):
        """Test is_active property"""
        job = Job.objects.create(**self.job_data)
        self.assertTrue(job.is_active)
        
        # Test with expired deadline
        job.application_deadline = timezone.now() - timezone.timedelta(days=1)
        job.save()
        self.assertFalse(job.is_active)
        
        # Test with draft status
        job.status = 'draft'
        job.application_deadline = None
        job.save()
        self.assertFalse(job.is_active)
    
    def test_job_salary_range_display(self):
        """Test salary range display property"""
        job = Job.objects.create(**self.job_data)
        expected = "USD 80,000 - 120,000"
        self.assertEqual(job.salary_range_display, expected)
        
        # Test with only minimum salary
        job.salary_max = None
        job.save()
        expected = "USD 80,000+"
        self.assertEqual(job.salary_range_display, expected)
        
        # Test with only maximum salary
        job.salary_min = None
        job.salary_max = Decimal('120000.00')
        job.save()
        expected = "Up to USD 120,000"
        self.assertEqual(job.salary_range_display, expected)
        
        # Test with no salary info
        job.salary_min = None
        job.salary_max = None
        job.save()
        self.assertEqual(job.salary_range_display, "Competitive")
    
    def test_job_increment_methods(self):
        """Test increment_views and increment_applications methods"""
        job = Job.objects.create(**self.job_data)
        
        initial_views = job.views_count
        initial_applications = job.applications_count
        
        job.increment_views()
        job.refresh_from_db()
        self.assertEqual(job.views_count, initial_views + 1)
        
        job.increment_applications()
        job.refresh_from_db()
        self.assertEqual(job.applications_count, initial_applications + 1)
    
    def test_job_skills_relationship(self):
        """Test many-to-many relationship with skills"""
        job = Job.objects.create(**self.job_data)
        job.skills.add(self.skill)
        
        self.assertIn(self.skill, job.skills.all())
        self.assertIn(job, self.skill.jobs.all())
    
    def test_published_job_manager(self):
        """Test PublishedJobManager"""
        # Create published job
        published_job = Job.objects.create(**self.job_data)
        published_job.published_at = timezone.now()
        published_job.save()
        
        # Create draft job
        draft_data = self.job_data.copy()
        draft_data['title'] = 'Draft Job'
        draft_data['status'] = 'draft'
        draft_job = Job.objects.create(**draft_data)
        
        # Test published manager
        published_jobs = Job.published.all()
        self.assertIn(published_job, published_jobs)
        self.assertNotIn(draft_job, published_jobs)
        
        # Test active jobs
        active_jobs = Job.published.active()
        self.assertIn(published_job, active_jobs)
        
        # Test expired job
        published_job.application_deadline = timezone.now() - timezone.timedelta(days=1)
        published_job.save()
        active_jobs = Job.published.active()
        self.assertNotIn(published_job, active_jobs)

class JobApplicationModelTest(TestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='testpass123',
            role='employer'
        )
        
        self.user = User.objects.create_user(
            username='jobseeker',
            email='jobseeker@example.com',
            password='testpass123',
            role='user'
        )
        
        self.company = Company.objects.create(
            name='Tech Corp',
            description='A tech company',
            location='San Francisco',
            created_by=self.employer
        )
        
        self.job = Job.objects.create(
            title='Python Developer',
            slug='python-developer-tech-corp',
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

    def test_saved_job_creation(self):
        """Test saved job creation"""
        saved_job = SavedJob.objects.create(
            user=self.user,
            job=self.job,
            notes='Interesting position'
        )
        
        self.assertEqual(saved_job.user, self.user)
        self.assertEqual(saved_job.job, self.job)
        self.assertEqual(saved_job.notes, 'Interesting position')
    
    def test_saved_job_str_method(self):
        """Test saved job string representation"""
        saved_job = SavedJob.objects.create(
            user=self.user,
            job=self.job
        )
        
        expected = f"{self.user.get_full_name()} saved {self.job.title}"
        self.assertEqual(str(saved_job), expected)
    
    def test_saved_job_unique_constraint(self):
        """Test unique constraint (one save per job per user)"""
        SavedJob.objects.create(user=self.user, job=self.job)
        
        with self.assertRaises(IntegrityError):
            SavedJob.objects.create(user=self.user, job=self.job)

class JobViewModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='viewer',
            email='viewer@example.com',
            password='testpass123'
        )
        
        self.employer = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='testpass123',
            role='employer'
        )
        
        self.company = Company.objects.create(
            name='Tech Corp',
            description='A tech company',
            location='San Francisco',
            created_by=self.employer
        )
        
        self.job = Job.objects.create(
            title='Python Developer',
            slug='python-developer-tech-corp',
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
    
    def test_job_view_creation(self):
        """Test job view creation"""
        job_view = JobView.objects.create(
            job=self.job,
            user=self.user,
            ip_address='192.168.1.1',
            user_agent='Test User Agent',
            session_key='test_session_key'
        )
        
        self.assertEqual(job_view.job, self.job)
        self.assertEqual(job_view.user, self.user)
        self.assertEqual(job_view.ip_address, '192.168.1.1')
        self.assertEqual(job_view.user_agent, 'Test User Agent')
    
    def test_job_view_str_method(self):
        """Test job view string representation"""
        job_view = JobView.objects.create(
            job=self.job,
            ip_address='192.168.1.1',
            user_agent='Test User Agent'
        )
        
        expected = f"View of {self.job.title} at {job_view.viewed_at}"
        self.assertEqual(str(job_view), expected)
    
    def test_anonymous_job_view(self):
        """Test job view without user (anonymous)"""
        job_view = JobView.objects.create(
            job=self.job,
            ip_address='192.168.1.1',
            user_agent='Test User Agent'
        )
        
        self.assertIsNone(job_view.user)
        self.assertEqual(job_view.ip_address, '192.168.1.1')


class JobAlertModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='jobseeker',
            email='jobseeker@example.com',
            password='testpass123'
        )
        
        self.employer = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='testpass123',
            role='employer'
        )
        
        self.industry = Industry.objects.create(
            name='Technology',
            slug='technology'
        )
        
        self.category = JobCategory.objects.create(
            name='Software Engineering',
            slug='software-engineering'
        )
        
        self.skill = Skill.objects.create(
            name='Python',
            slug='python'
        )
        
        self.job_type = JobType.objects.create(
            name='Full Time',
            slug='full-time'
        )
        
        self.company = Company.objects.create(
            name='Tech Corp',
            description='A tech company',
            location='San Francisco',
            created_by=self.employer,
            industry=self.industry
        )
        
        # Create some test jobs
        self.job1 = Job.objects.create(
            title='Python Developer',
            slug='python-developer-1',
            description='Python development job',
            requirements='Python skills required',
            responsibilities='Develop Python applications',
            company=self.company,
            category=self.category,
            industry=self.industry,
            created_by=self.employer,
            job_type='full_time',
            experience_level='mid',
            location='San Francisco',
            status='published',
            published_at=timezone.now()
        )
        self.job1.skills.add(self.skill)
        
        self.job2 = Job.objects.create(
            title='Java Developer',
            slug='java-developer-1',
            description='Java development job',
            requirements='Java skills required',
            responsibilities='Develop Java applications',
            company=self.company,
            created_by=self.employer,
            job_type='full_time',
            experience_level='senior',
            location='New York',
            status='published',
            published_at=timezone.now()
        )
    
    def test_job_alert_creation(self):
        """Test job alert creation"""
        alert = JobAlert.objects.create(
            user=self.user,
            name='Python Jobs',
            keywords='python, django',
            location='San Francisco',
            frequency='daily',
            salary_min=Decimal('70000.00')
        )
        
        self.assertEqual(alert.user, self.user)
        self.assertEqual(alert.name, 'Python Jobs')
        self.assertEqual(alert.keywords, 'python, django')
        self.assertEqual(alert.frequency, 'daily')
        self.assertTrue(alert.is_active)
    
    def test_job_alert_str_method(self):
        """Test job alert string representation"""
        alert = JobAlert.objects.create(
            user=self.user,
            name='Python Jobs'
        )
        
        expected = f"Python Jobs - {self.user.get_full_name()}"
        self.assertEqual(str(alert), expected)
    
    def test_job_alert_matching_jobs_by_keywords(self):
        """Test get_matching_jobs with keywords"""
        alert = JobAlert.objects.create(
            user=self.user,
            name='Python Jobs',
            keywords='python'
        )
        
        matching_jobs = alert.get_matching_jobs()
        self.assertIn(self.job1, matching_jobs)
        self.assertNotIn(self.job2, matching_jobs)
    
    def test_job_alert_matching_jobs_by_location(self):
        """Test get_matching_jobs with location"""
        alert = JobAlert.objects.create(
            user=self.user,
            name='SF Jobs',
            location='San Francisco'
        )
        
        matching_jobs = alert.get_matching_jobs()
        self.assertIn(self.job1, matching_jobs)
        self.assertNotIn(self.job2, matching_jobs)
    
    def test_job_alert_matching_jobs_remote_only(self):
        """Test get_matching_jobs with remote_only"""
        # Set job1 as remote allowed
        self.job1.remote_allowed = True
        self.job1.save()
        
        alert = JobAlert.objects.create(
            user=self.user,
            name='Remote Jobs',
            remote_only=True
        )
        
        matching_jobs = alert.get_matching_jobs()
        self.assertIn(self.job1, matching_jobs)
        self.assertNotIn(self.job2, matching_jobs)
    
    def test_job_alert_matching_jobs_by_category(self):
        """Test get_matching_jobs with categories"""
        alert = JobAlert.objects.create(
            user=self.user,
            name='Software Jobs'
        )
        alert.categories.add(self.category)
        
        matching_jobs = alert.get_matching_jobs()
        self.assertIn(self.job1, matching_jobs)
        self.assertNotIn(self.job2, matching_jobs)
    
    def test_job_alert_matching_jobs_by_skills(self):
        """Test get_matching_jobs with skills"""
        alert = JobAlert.objects.create(
            user=self.user,
            name='Python Skills Jobs'
        )
        alert.skills.add(self.skill)
        
        matching_jobs = alert.get_matching_jobs()
        self.assertIn(self.job1, matching_jobs)
        self.assertNotIn(self.job2, matching_jobs)
    
    def test_job_alert_should_send_alert(self):
        """Test should_send_alert method"""
        alert = JobAlert.objects.create(
            user=self.user,
            name='Test Alert',
            frequency='daily'
        )
        
        # Should send if never sent before
        self.assertTrue(alert.should_send_alert())
        
        # Should not send if recently sent
        alert.last_sent = timezone.now() - timezone.timedelta(hours=1)
        alert.save()
        self.assertFalse(alert.should_send_alert())
        
        # Should send if enough time has passed
        alert.last_sent = timezone.now() - timezone.timedelta(days=2)
        alert.save()
        self.assertTrue(alert.should_send_alert())
        
        # Should not send if inactive
        alert.is_active = False
        alert.save()
        self.assertFalse(alert.should_send_alert())
    
    def test_job_alert_mark_as_sent(self):
        """Test mark_as_sent method"""
        alert = JobAlert.objects.create(
            user=self.user,
            name='Test Alert'
        )
        
        initial_count = alert.jobs_sent_count
        alert.mark_as_sent(job_count=5)
        
        alert.refresh_from_db()
        self.assertIsNotNone(alert.last_sent)
        self.assertEqual(alert.jobs_sent_count, initial_count + 5)

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

