from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.companies.models import Company, Industry
from apps.companies.utils import set_user_context, verify_company, feature_company
from apps.core.models import AuditLog

User = get_user_model()


class CompanyUtilsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='testpass123'
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role='admin'
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
    
    def test_set_user_context(self):
        """Test setting user context on model instances"""
        # Test update context
        updated_company = set_user_context(self.company, self.admin, 'update')
        self.assertEqual(updated_company._updated_by, self.admin)
        
        # Test delete context
        deleted_company = set_user_context(self.company, self.admin, 'delete')
        self.assertEqual(deleted_company._deleted_by, self.admin)
    
    def test_verify_company_utility(self):
        """Test company verification utility function"""
        self.assertFalse(self.company.is_verified)
        initial_count = AuditLog.objects.count()
        
        # Verify company using utility
        verified_company = verify_company(self.company, self.admin)
        
        # Check company is verified
        self.assertTrue(verified_company.is_verified)
        
        # Check audit logs were created
        self.assertGreater(AuditLog.objects.count(), initial_count)
        
        # Check for verification-specific log
        verify_logs = AuditLog.objects.filter(action='verify_company')
        self.assertTrue(verify_logs.exists())
    
    def test_feature_company_utility(self):
        """Test company featuring utility function"""
        self.assertFalse(self.company.is_featured)
        initial_count = AuditLog.objects.count()
        
        # Feature company using utility
        featured_company = feature_company(self.company, self.admin)
        
        # Check company is featured
        self.assertTrue(featured_company.is_featured)
        
        # Check audit logs were created
        self.assertGreater(AuditLog.objects.count(), initial_count)
        
        # Check for feature-specific log
        feature_logs = AuditLog.objects.filter(action='feature_company')
        self.assertTrue(feature_logs.exists())

