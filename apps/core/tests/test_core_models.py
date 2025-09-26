from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.core.models import AuditLog
from apps.companies.models import Company
import json

User = get_user_model()


class AuditLogModelTest(TestCase):
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
    
    def test_audit_log_creation(self):
        """Test audit log creation"""
        log = AuditLog.objects.create(
            user=self.user,
            action='create',
            object_type='Company',
            object_id=str(self.company.id),
            object_repr=str(self.company),
            details={'name': self.company.name},
            ip_address='192.168.1.1',
            user_agent='Test User Agent'
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'create')
        self.assertEqual(log.object_type, 'Company')
        self.assertEqual(log.object_id, str(self.company.id))
        self.assertEqual(log.details, {'name': self.company.name})
    
    def test_audit_log_str_method(self):
        """Test audit log string representation"""
        log = AuditLog.objects.create(
            user=self.user,
            action='create',
            object_type='Company',
            object_id=str(self.company.id),
            object_repr=str(self.company)
        )
        
        expected = f"create Company by {self.user}"
        self.assertEqual(str(log), expected)
    
    def test_audit_log_anonymous_user(self):
        """Test audit log with anonymous user"""
        log = AuditLog.objects.create(
            action='view',
            object_type='Job',
            object_id='123',
            object_repr='Test Job',
            ip_address='192.168.1.1'
        )
        
        expected = "view Job by Anonymous"
        self.assertEqual(str(log), expected)
    
    def test_audit_log_log_action_class_method(self):
        """Test log_action class method"""
        log = AuditLog.log_action(
            user=self.user,
            action='update',
            obj=self.company,
            details={'field': 'name', 'old_value': 'Old Name', 'new_value': 'New Name'}
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'update')
        self.assertEqual(log.object_type, 'Company')
        self.assertEqual(log.object_id, str(self.company.id))
        self.assertEqual(log.object_repr, str(self.company))
        self.assertEqual(log.details['field'], 'name')
        self.assertEqual(log.details['old_value'], 'Old Name')
        self.assertEqual(log.details['new_value'], 'New Name')
