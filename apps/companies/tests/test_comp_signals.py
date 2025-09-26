from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.companies.models import Company, Industry
# from apps.companies.signals import company_verified, company_featured
from apps.core.models import AuditLog

User = get_user_model()


class CompanySignalsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='employer'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role='admin',
            is_staff=True
        )
        
        self.industry = Industry.objects.create(
            name='Technology',
            slug='technology'
        )
    
    def test_company_creation_logged(self):
        """Test that company creation is logged in audit trail"""
        initial_count = AuditLog.objects.count()
        
        company = Company.objects.create(
            name='Tech Corp',
            description='A technology company',
            location='San Francisco',
            created_by=self.user,
            industry=self.industry
        )
        
        # Should create audit log entry
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)
        
        log = AuditLog.objects.latest('timestamp')
        self.assertEqual(log.action, 'create')
        self.assertEqual(log.object_type, 'Company')
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.details['name'], 'Tech Corp')
        self.assertEqual(log.details['location'], 'San Francisco')
        self.assertEqual(log.details['industry'], 'Technology')
    
    def test_company_update_logged(self):
        """Test that company updates are logged"""
        company = Company.objects.create(
            name='Tech Corp',
            description='A technology company',
            location='San Francisco',
            created_by=self.user,
            industry=self.industry
        )
        
        initial_count = AuditLog.objects.count()
        
        # Update company
        company.name = 'Updated Tech Corp'
        company.location = 'New York'
        company._updated_by = self.user  # Simulate user context
        company.save()
        
        # Should create another audit log entry
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)
        
        log = AuditLog.objects.latest('timestamp')
        self.assertEqual(log.action, 'update')
        self.assertEqual(log.object_type, 'Company')
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.details['name'], 'Updated Tech Corp')
    
    def test_company_verification_logged(self):
        """Test that company verification creates special audit log"""
        company = Company.objects.create(
            name='Tech Corp',
            description='A technology company',
            location='San Francisco',
            created_by=self.user,
            industry=self.industry,
            is_verified=False
        )
        
        initial_count = AuditLog.objects.count()
        
        # Verify company
        company.is_verified = True
        company._updated_by = self.admin_user
        company.save()
        
        # Should create audit log entries (update + verify)
        self.assertGreater(AuditLog.objects.count(), initial_count + 1)
        
        # Check for verification log
        verify_logs = AuditLog.objects.filter(action='verify')
        self.assertTrue(verify_logs.exists())
        
        verify_log = verify_logs.latest('timestamp')
        self.assertEqual(verify_log.user, self.admin_user)
        self.assertEqual(verify_log.details['new_status'], True)
        self.assertEqual(verify_log.details['previous_status'], False)
    
    def test_company_featured_logged(self):
        """Test that featuring company creates special audit log"""
        company = Company.objects.create(
            name='Tech Corp',
            description='A technology company',
            location='San Francisco',
            created_by=self.user,
            industry=self.industry,
            is_featured=False
        )
        
        initial_count = AuditLog.objects.count()
        
        # Feature company
        company.is_featured = True
        company._updated_by = self.admin_user
        company.save()
        
        # Should create audit log entries
        self.assertGreater(AuditLog.objects.count(), initial_count + 1)
        
        # Check for feature log
        feature_logs = AuditLog.objects.filter(action='feature')
        self.assertTrue(feature_logs.exists())
        
        feature_log = feature_logs.latest('timestamp')
        self.assertEqual(feature_log.user, self.admin_user)
        self.assertEqual(feature_log.details['new_status'], True)
    
    def test_company_deletion_logged(self):
        """Test that company deletion is logged"""
        company = Company.objects.create(
            name='Tech Corp',
            description='A technology company',
            location='San Francisco',
            created_by=self.user,
            industry=self.industry
        )
        
        # Create some jobs for the company to test job_count logging
        from apps.jobs.models import Job
        Job.objects.create(
            title='Test Job',
            slug='test-job-company-delete',
            description='Job description',
            requirements='Job requirements',
            responsibilities='Job responsibilities',
            company=company,
            created_by=self.user,
            job_type='full_time',
            experience_level='mid',
            location='San Francisco'
        )
        
        initial_count = AuditLog.objects.count()
        
        # Set deletion context
        company._deleted_by = self.admin_user
        company_name = company.name
        company.delete()
        
        # Should create audit log entry
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)
        
        log = AuditLog.objects.latest('timestamp')
        self.assertEqual(log.action, 'delete')
        self.assertEqual(log.object_type, 'Company')
        self.assertEqual(log.user, self.admin_user)
        self.assertEqual(log.details['name'], company_name)
        self.assertEqual(log.details['job_count'], 1)

class IndustrySignalsTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role='admin'
        )
    
    def test_industry_creation_logged(self):
        """Test that industry creation is logged"""
        initial_count = AuditLog.objects.count()
        
        industry = Industry.objects.create(
            name='Healthcare',
            slug='healthcare',
            description='Healthcare industry'
        )
        
        # Should create audit log entry
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)
        
        log = AuditLog.objects.latest('timestamp')
        self.assertEqual(log.action, 'create')
        self.assertEqual(log.object_type, 'Industry')
        self.assertEqual(log.details['name'], 'Healthcare')
        self.assertEqual(log.details['slug'], 'healthcare')
    
    def test_industry_update_logged(self):
        """Test that industry updates are logged"""
        industry = Industry.objects.create(
            name='Healthcare',
            slug='healthcare'
        )
        
        initial_count = AuditLog.objects.count()
        
        # Update industry
        industry.name = 'Health & Medicine'
        industry._updated_by = self.admin_user
        industry.save()
        
        # Should create audit log entry
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)
        
        log = AuditLog.objects.latest('timestamp')
        self.assertEqual(log.action, 'update')
        self.assertEqual(log.object_type, 'Industry')
        self.assertEqual(log.details['name'], 'Health & Medicine')
    
    def test_industry_deletion_logged(self):
        """Test that industry deletion is logged"""
        industry = Industry.objects.create(
            name='Healthcare',
            slug='healthcare'
        )
        
        # Create a company in this industry
        user = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='testpass123'
        )
        
        Company.objects.create(
            name='Health Corp',
            description='Healthcare company',
            location='Boston',
            created_by=user,
            industry=industry
        )
        
        initial_count = AuditLog.objects.count()
        
        industry._deleted_by = self.admin_user
        industry_name = industry.name
        industry.delete()
        
        # Should create audit log entry
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)
        
        log = AuditLog.objects.latest('timestamp')
        self.assertEqual(log.action, 'delete')
        self.assertEqual(log.object_type, 'Industry')
        self.assertEqual(log.user, self.admin_user)
        self.assertEqual(log.details['name'], industry_name)