from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class UserManagerTest(TestCase):
    """Test cases for custom UserManager"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_email = 'test@example.com'
        self.valid_password = 'testpass123'
        self.invalid_emails = [
            'invalid-email',
            'test@',
            '@example.com',
            'test..test@example.com',
            '',
        ]
    
    def test_create_user_with_valid_email(self):
        """Test creating user with valid email"""
        user = User.objects.create_user(
            email=self.valid_email,
            password=self.valid_password,
            first_name='Test',
            last_name='User',
            username='testuser'  # Let it auto-generate from email
        )
        
        self.assertEqual(user.email, self.valid_email)
        self.assertTrue(user.check_password(self.valid_password))
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.role, 'user')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_active)  # Default for new users
        self.assertFalse(user.is_verified)
        self.assertIsNotNone(user.verification_token)
        self.assertEqual(len(user.verification_token), 67)  # token_urlsafe(50) length
    
    def test_create_user_without_email_raises_error(self):
        """Test that creating user without email raises ValueError"""
        with self.assertRaises(ValueError) as context:
            User.objects.create_user(
                email=None,
                password=self.valid_password,
                username='testuser'
            )
        
        self.assertIn('The Email field must be set', str(context.exception))
        
        # Test with empty string
        with self.assertRaises(ValueError) as context:
            User.objects.create_user(
                email='',
                password=self.valid_password,
                username='testuser'
            )
        
        self.assertIn('The Email field must be set', str(context.exception))
    
    def test_create_user_with_invalid_email_raises_error(self):
        """Test that creating user with invalid email raises ValueError"""
        for invalid_email in self.invalid_emails:
            with self.assertRaises(ValueError) as context:
                User.objects.create_user(
                    email=invalid_email,
                    password=self.valid_password,
                    username='testuser'
                )
            assertErr = str(context.exception)
            if assertErr == 'Invalid email format':
              self.assertIn('Invalid email format', assertErr)
            else:
              self.assertIn('The Email field must be set', assertErr)
    
    def test_email_normalization(self):
        """Test that email is properly normalized"""
        test_cases = [
            ('Test@Example.COM', 'Test@example.com'),
            ('TEST@EXAMPLE.COM', 'TEST@example.com'),
            ('test@Example.Com', 'test@example.com'),
        ]
        
        for input_email, expected_email in test_cases:
            user = User.objects.create_user(
                email=input_email,
                password=self.valid_password,
                # username='testuser'
            )
            self.assertEqual(user.email, expected_email)
    
    def test_username_generation_from_email(self):
        """Test automatic username generation from email"""
        user = User.objects.create_user(
            email='johndoe@example.com',
            password=self.valid_password,
        ) # type: ignore
        
        self.assertEqual(user.username, 'johndoe')
    
    def test_username_uniqueness_handling(self):
        """Test that duplicate usernames are handled properly"""
        # Create first user
        user1 = User.objects.create_user(
            email='test@example.com',
            password=self.valid_password
        )
        self.assertEqual(user1.username, 'test')
        
        # Create second user with same email prefix
        user2 = User.objects.create_user(
            email='test@another.com',
            password=self.valid_password
        )
        self.assertEqual(user2.username, 'test1')
        
        # Create third user with same email prefix
        user3 = User.objects.create_user(
            email='test@third.com',
            password=self.valid_password
        )
        self.assertEqual(user3.username, 'test2')
    
    def test_custom_username_provided(self):
        """Test that custom username is used when provided"""
        user = User.objects.create_user(
            email=self.valid_email,
            password=self.valid_password,
            username='customuser'
        )
        
        self.assertEqual(user.username, 'customuser')
    
    def test_create_employer(self):
        """Test creating employer user"""
        employer = User.objects.create_employer(
            email='employer@example.com',
            password=self.valid_password,
            first_name='Employer',
            last_name='User'
        )
        
        self.assertEqual(employer.email, 'employer@example.com')
        self.assertEqual(employer.role, 'employer')
        self.assertFalse(employer.is_staff)
        self.assertFalse(employer.is_superuser)
        self.assertFalse(employer.is_active)  # Default for new users
        self.assertFalse(employer.is_verified)
        self.assertIsNotNone(employer.verification_token)
    
    def test_create_superuser(self):
        """Test creating superuser"""
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password=self.valid_password,
            first_name='Admin',
            last_name='User'
        ) # type: ignore
        
        self.assertEqual(superuser.email, 'admin@example.com')
        self.assertEqual(superuser.role, 'admin')
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_verified)
        self.assertIsNotNone(superuser.verification_token)
    
    def test_create_superuser_validation(self):
        """Test superuser validation"""
        # Test is_staff=False
        with self.assertRaises(ValueError) as context:
            User.objects.create_superuser(
                email='admin@example.com',
                password=self.valid_password,
                is_staff=False
            ) # type: ignore
        self.assertIn('Superuser must have is_staff=True', str(context.exception))
        
        # Test is_superuser=False
        with self.assertRaises(ValueError) as context:
            User.objects.create_superuser(
                email='admin@example.com',
                password=self.valid_password,
                is_superuser=False
            ) # type: ignore
        self.assertIn('Superuser must have is_superuser=True', str(context.exception))
    
    def test_get_by_natural_key(self):
        """Test authentication using email (case insensitive)"""
        user = User.objects.create_user(
            email='Test@Example.Com',
            password=self.valid_password
        ) # type: ignore
        
        # Test case insensitive lookup
        retrieved_user = User.objects.get_by_natural_key('test@example.com')
        self.assertEqual(retrieved_user, user)
        
        retrieved_user = User.objects.get_by_natural_key('TEST@EXAMPLE.COM')
        self.assertEqual(retrieved_user, user)
        
        retrieved_user = User.objects.get_by_natural_key('Test@Example.Com')
        self.assertEqual(retrieved_user, user)
    
    def test_get_active_users(self):
        """Test getting active and verified users"""
        # Create active and verified user
        active_user = User.objects.create_user(
            email='active@example.com',
            password=self.valid_password
        ) # type: ignore
        active_user.is_active = True
        active_user.is_verified = True
        active_user.save()
        
        # Create inactive user
        inactive_user = User.objects.create_user(
            email='inactive@example.com',
            password=self.valid_password
        ) # type: ignore
        # inactive_user remains inactive by default
        
        # Create unverified but active user
        unverified_user = User.objects.create_user(
            email='unverified@example.com',
            password=self.valid_password
        ) # type: ignore
        unverified_user.is_active = True
        unverified_user.save()
        # unverified_user remains unverified
        
        active_users = User.objects.get_active_users()
        
        self.assertIn(active_user, active_users)
        self.assertNotIn(inactive_user, active_users)
        self.assertNotIn(unverified_user, active_users)
    
    def test_get_users_by_role(self):
        """Test getting users by specific role"""
        # Create users with different roles
        job_seeker = User.objects.create_user(
            email='jobseeker@example.com',
            password=self.valid_password
        ) # type: ignore
        job_seeker.is_active = True
        job_seeker.save()
        
        employer = User.objects.create_employer(
            email='employer@example.com',
            password=self.valid_password
        )
        employer.is_active = True
        employer.save()
        
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password=self.valid_password
        ) # type: ignore
        
        # Test role filtering
        users = User.objects.get_users_by_role('user')
        self.assertIn(job_seeker, users)
        self.assertNotIn(employer, users)
        self.assertNotIn(admin, users)
        
        employers = User.objects.get_users_by_role('employer')
        self.assertIn(employer, employers)
        self.assertNotIn(job_seeker, employers)
        self.assertNotIn(admin, employers)
        
        admins = User.objects.get_users_by_role('admin')
        self.assertIn(admin, admins)
        self.assertNotIn(job_seeker, admins)
        self.assertNotIn(employer, admins)
    
    def test_get_employers(self):
        """Test getting all active employers"""
        employer1 = User.objects.create_employer(
            email='employer1@example.com',
            password=self.valid_password
        )
        employer1.is_active = True
        employer1.save()
        
        employer2 = User.objects.create_employer(
            email='employer2@example.com',
            password=self.valid_password
        )
        employer2.is_active = True
        employer2.save()
        
        # Create inactive employer
        inactive_employer = User.objects.create_employer(
            email='inactive@example.com',
            password=self.valid_password
        )
        # inactive_employer remains inactive
        
        # Create job seeker
        job_seeker = User.objects.create_user(
            email='jobseeker@example.com',
            password=self.valid_password
        )
        job_seeker.is_active = True
        job_seeker.save()
        
        employers = User.objects.get_employers()
        
        self.assertIn(employer1, employers)
        self.assertIn(employer2, employers)
        self.assertNotIn(inactive_employer, employers)
        self.assertNotIn(job_seeker, employers)
    
    def test_get_users(self):
        """Test getting all active job seekers"""
        job_seeker1 = User.objects.create_user(
            email='jobseeker1@example.com',
            password=self.valid_password
        ) # type: ignore
        job_seeker1.is_active = True
        job_seeker1.save()
        
        job_seeker2 = User.objects.create_user(
            email='jobseeker2@example.com',
            password=self.valid_password
        ) # type: ignore
        job_seeker2.is_active = True
        job_seeker2.save()
        
        # Create inactive job seeker
        inactive_seeker = User.objects.create_user(
            email='inactive@example.com',
            password=self.valid_password
        ) # type: ignore
        # inactive_seeker remains inactive
        
        # Create employer
        employer = User.objects.create_employer(
            email='employer@example.com',
            password=self.valid_password
        )
        employer.is_active = True
        employer.save()
        
        job_seekers = User.objects.get_users()
        
        self.assertIn(job_seeker1, job_seekers)
        self.assertIn(job_seeker2, job_seekers)
        self.assertNotIn(inactive_seeker, job_seekers)
        self.assertNotIn(employer, job_seekers)
    
    def test_get_admins(self):
        """Test getting all admin users"""
        admin1 = User.objects.create_superuser(
            email='admin1@example.com',
            password=self.valid_password
        ) # type: ignore
        
        admin2 = User.objects.create_user(
            email='admin2@example.com',
            password=self.valid_password,
            role='admin'
        )
        admin2.is_active = True
        admin2.save()
        
        # Create non-admin users
        job_seeker = User.objects.create_user(
            email='jobseeker@example.com',
            password=self.valid_password
        )
        job_seeker.is_active = True
        job_seeker.save()
        
        employer = User.objects.create_employer(
            email='employer@example.com',
            password=self.valid_password
        )
        employer.is_active = True
        employer.save()
        
        admins = User.objects.get_admins()
        
        self.assertIn(admin1, admins)
        self.assertIn(admin2, admins)
        self.assertNotIn(job_seeker, admins)
        self.assertNotIn(employer, admins)
    
    def test_get_unverified_users(self):
        """Test getting unverified users older than specified days"""
        now = timezone.now()
        
        # Create user from 10 days ago (unverified)
        old_unverified = User.objects.create_user(
            email='old@example.com',
            password=self.valid_password
        )
        old_unverified.created_at = now - timedelta(days=10)
        old_unverified.save()
        
        # Create user from 5 days ago (unverified)
        recent_unverified = User.objects.create_user(
            email='recent@example.com',
            password=self.valid_password
        )
        recent_unverified.created_at = now - timedelta(days=5)
        recent_unverified.save()
        
        # Create old verified user
        old_verified = User.objects.create_user(
            email='verified@example.com',
            password=self.valid_password
        )
        old_verified.created_at = now - timedelta(days=10)
        old_verified.is_verified = True
        old_verified.save()
        
        # Test default 7 days
        unverified_users = User.objects.get_unverified_users()
        self.assertIn(old_unverified, unverified_users)
        self.assertNotIn(recent_unverified, unverified_users)  # Too recent
        self.assertNotIn(old_verified, unverified_users)  # Verified
        
        # Test custom days
        unverified_users_3_days = User.objects.get_unverified_users(days_old=3)
        self.assertIn(old_unverified, unverified_users_3_days)
        self.assertIn(recent_unverified, unverified_users_3_days)
        self.assertNotIn(old_verified, unverified_users_3_days)  # Verified
        
        # Test very recent cutoff
        unverified_users_15_days = User.objects.get_unverified_users(days_old=15)
        self.assertEqual(unverified_users_15_days.count(), 0)  # No users that old
    
    def test_cleanup_unverified_users(self):
        """Test cleanup of old unverified users"""
        now = timezone.now()
        
        # Create old unverified users
        old_user1 = User.objects.create_user(
            email='old1@example.com',
            password=self.valid_password
        )
        old_user1.created_at = now - timedelta(days=35)
        old_user1.save()
        
        old_user2 = User.objects.create_user(
            email='old2@example.com',
            password=self.valid_password
        )
        old_user2.created_at = now - timedelta(days=40)
        old_user2.save()
        
        # Create recent unverified user
        recent_user = User.objects.create_user(
            email='recent@example.com',
            password=self.valid_password
        )
        recent_user.created_at = now - timedelta(days=20)
        recent_user.save()
        
        # Create old verified user
        old_verified = User.objects.create_user(
            email='verified@example.com',
            password=self.valid_password
        )
        old_verified.created_at = now - timedelta(days=35)
        old_verified.is_verified = True
        old_verified.save()
        
        initial_count = User.objects.count()
        
        # Cleanup users older than 30 days
        deleted_count = User.objects.cleanup_unverified_users(days_old=30)
        
        self.assertEqual(deleted_count, 2)  # old_user1 and old_user2
        self.assertEqual(User.objects.count(), initial_count - 2)
        
        # Verify correct users were deleted
        self.assertFalse(User.objects.filter(email='old1@example.com').exists())
        self.assertFalse(User.objects.filter(email='old2@example.com').exists())
        
        # Verify correct users were preserved
        self.assertTrue(User.objects.filter(email='recent@example.com').exists())
        self.assertTrue(User.objects.filter(email='verified@example.com').exists())
    
    def test_password_creation_without_password(self):
        """Test creating user without password"""
        user = User.objects.create_user(
            email=self.valid_email,
            password=None
        )
        
        # User should exist but not be able to authenticate
        self.assertFalse(user.has_usable_password())
    
    def test_verification_token_uniqueness(self):
        """Test that verification tokens are unique across users"""
        user1 = User.objects.create_user(
            email='user1@example.com',
            password=self.valid_password
        )
        
        user2 = User.objects.create_user(
            email='user2@example.com',
            password=self.valid_password
        )
        
        self.assertNotEqual(user1.verification_token, user2.verification_token)
        self.assertIsNotNone(user1.verification_token)
        self.assertIsNotNone(user2.verification_token)
    
    def test_extra_fields_handling(self):
        """Test that extra fields are properly handled"""
        user = User.objects.create_user(
            email=self.valid_email,
            password=self.valid_password,
            first_name='John',
            last_name='Doe',
            phone_number='+1234567890'
        )
        
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.phone_number, '+1234567890')
    
    def test_manager_method_chaining(self):
        """Test that manager methods can be chained"""
        # Create test users
        employer1 = User.objects.create_employer(
            email='emp1@example.com',
            password=self.valid_password
        )
        employer1.is_active = True
        employer1.is_verified = True
        employer1.save()
        
        employer2 = User.objects.create_employer(
            email='emp2@example.com',
            password=self.valid_password
        )
        employer2.is_active = True
        # employer2 remains unverified
        employer2.save()
        
        # Test chaining filters
        verified_employers = User.objects.get_employers().filter(is_verified=True)
        self.assertIn(employer1, verified_employers)
        self.assertNotIn(employer2, verified_employers)


class UserManagerEdgeCasesTest(TestCase):
    """Test edge cases and error conditions for UserManager"""
    
    def test_very_long_email_prefix(self):
        """Test username generation with very long email prefix"""
        long_prefix = 'a' * 100
        email = f'{long_prefix}@example.com'
        
        user = User.objects.create_user(
            email=email,
            password='testpass123'
        )
        
        # Username should be truncated or handled appropriately
        self.assertEqual(user.username, long_prefix)
        self.assertTrue(len(user.username) <= 150)  # Django's username max length
    
    def test_special_characters_in_email_prefix(self):
        """Test username generation with special characters in email"""
        test_cases = [
            'user.name@example.com',
            'user+tag@example.com',
            'user-name@example.com',
            'user_name@example.com',
        ]
        
        for email in test_cases:
            user = User.objects.create_user(
                email=email,
                password='testpass123'
            )
            
            # Username should be derived from email prefix
            expected_username = email.split('@')[0]
            self.assertEqual(user.username, expected_username)
    
    def test_cleanup_with_no_old_users(self):
        """Test cleanup when no old users exist"""
        # Create only recent users
        recent_user = User.objects.create_user(
            email='recent@example.com',
            password='testpass123'
        )
        
        deleted_count = User.objects.cleanup_unverified_users(days_old=30)
        self.assertEqual(deleted_count, 0)
        
        # User should still exist
        self.assertTrue(User.objects.filter(email='recent@example.com').exists())