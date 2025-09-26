from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.core.models import AuditLog
from apps.accounts.models import Profile

User = get_user_model()


class AccountsSignalsTest(TestCase):
    def test_user_creation_logged(self):
        """Test that user creation is logged in audit trail"""
        initial_count = AuditLog.objects.count()
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Should create audit log entry
        self.assertEqual(AuditLog.objects.count(), initial_count + 1)
        
        log = AuditLog.objects.latest('timestamp')
        self.assertEqual(log.action, 'create')
        self.assertEqual(log.object_type, 'User')
        self.assertEqual(log.user, user)
    
    def test_profile_auto_creation(self):
        """Test that profile is automatically created for new users"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Profile should be created automatically
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, Profile)