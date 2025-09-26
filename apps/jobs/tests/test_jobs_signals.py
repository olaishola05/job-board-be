from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.companies.models import Company
from apps.jobs.models import Job, JobApplication, SavedJob
from apps.core.models import AuditLog

User = get_user_model()


class JobsSignalsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            description='Test description',
            location='Test Location',
            created_by=self.user
        )
    
    def test_job_creation_logged(self):
        """Test that job creation is logged"""
        initial_count = AuditLog.objects.count()
        
        job = Job.objects.create(
            title='Test Job',
            slug='test-job',
            description='Job description',
            requirements='Job requirements',
            responsibilities='Job responsibilities',
            company=self.company,
            created_by=self.user,
            job_type='full_time',
            experience_level='mid',
            location='Test Location'
        )
        
        self.assertGreater(AuditLog.objects.count(), initial_count)
    
    def test_job_application_logged(self):
        """Test that job applications are logged"""
        job = Job.objects.create(
            title='Test Job',
            slug='test-job',
            description='Job description',
            requirements='Job requirements',
            responsibilities='Job responsibilities',
            company=self.company,
            created_by=self.user,
            job_type='full_time',
            experience_level='mid',
            location='Test Location'
        )
        
        applicant = User.objects.create_user(
            username='applicant',
            email='applicant@example.com',
            password='testpass123'
        )
        
        initial_count = AuditLog.objects.count()
        
        application = JobApplication.objects.create(
            job=job,
            applicant=applicant,
            cover_letter='Test cover letter'
        )
        
        self.assertGreater(AuditLog.objects.count(), initial_count)
    
    def test_saved_job_logged(self):
        """Test that saving jobs is logged"""
        job = Job.objects.create(
            title='Test Job',
            slug='test-job',
            description='Job description',
            requirements='Job requirements',
            responsibilities='Job responsibilities',
            company=self.company,
            created_by=self.user,
            job_type='full_time',
            experience_level='mid',
            location='Test Location'
        )
        
        initial_count = AuditLog.objects.count()
        
        saved_job = SavedJob.objects.create(
            user=self.user,
            job=job
        )
        
        self.assertGreater(AuditLog.objects.count(), initial_count)
        
        # Test unsaving (deletion) is also logged
        saved_job.delete()
        
        # Should have one more log entry for deletion
        self.assertGreater(AuditLog.objects.count(), initial_count + 1)