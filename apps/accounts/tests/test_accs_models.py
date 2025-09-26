from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.accounts.models import Profile
from apps.jobs.models import Skill, SkillCategory
import tempfile
import os

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'user'
        }
    
    def test_user_creation(self):
        """Test basic user creation"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, 'user')
        self.assertFalse(user.is_verified)
        self.assertTrue(user.check_password('testpass123'))
    
    def test_user_str_method(self):
        """Test user string representation"""
        user = User.objects.create_user(**self.user_data)
        expected = f"{user.email} (user)"
        self.assertEqual(str(user), expected)
    
    def test_get_full_name(self):
        """Test get_full_name method"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), "Test User")
        
        # Test with empty names
        user.first_name = ""
        user.last_name = ""
        user.save()
        self.assertEqual(user.get_full_name(), user.email)
    
    def test_role_methods(self):
        """Test role checking methods"""
        user = User.objects.create_user(**self.user_data)
        self.assertTrue(user.is_user())
        self.assertFalse(user.is_employer())
        self.assertFalse(user.is_admin())
        
        user.role = 'employer'
        user.save()
        self.assertFalse(user.is_user())
        self.assertTrue(user.is_employer())
        self.assertFalse(user.is_admin())
        
        user.role = 'admin'
        user.save()
        self.assertFalse(user.is_user())
        self.assertFalse(user.is_employer())
        self.assertTrue(user.is_admin())
    
    def test_email_unique_constraint(self):
        """Test email uniqueness"""
        User.objects.create_user(**self.user_data)
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='testuser2',
                email='test@example.com',  # Same email
                password='testpass456'
            )
    
    def test_phone_number_validation(self):
        """Test phone number validation"""
        user = User.objects.create_user(**self.user_data)
        
        # Valid phone numbers
        valid_phones = ['+1234567890', '1234567890', '+123456789012345']
        for phone in valid_phones:
            user.phone_number = phone
            try:
                user.full_clean()
            except ValidationError:
                self.fail(f"Phone number {phone} should be valid")
        
        # Invalid phone numbers
        invalid_phones = ['123', '+123456789012345678901', 'abc123', '']
        for phone in invalid_phones:
            user.phone_number = phone
            if phone:  # Skip empty string as it's allowed
                with self.assertRaises(ValidationError):
                    user.full_clean()


class ProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.skill_category = SkillCategory.objects.create(
            name='Programming',
            slug='programming'
        )
        self.skill = Skill.objects.create(
            name='Python',
            slug='python',
            category=self.skill_category
        )
    
    def test_profile_creation(self):
        """Test profile creation"""
        profile, _ = Profile.objects.update_or_create(user=self.user)
        
        profile.bio = 'Test bio'
        profile.location = 'New York'
        profile.experience_years=5
        profile.salary_expectation=75000.00
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.bio, 'Test bio')
        self.assertEqual(profile.location, 'New York')
        self.assertEqual(profile.experience_years, 5)
        self.assertEqual(profile.salary_expectation, 75000.00)
        self.assertTrue(profile.is_available)
        self.assertEqual(profile.visibility, 'public')
    
    def test_profile_str_method(self):
        """Test profile string representation"""
        profile = Profile.objects.get(user=self.user)
        expected = f"Profile of {self.user.get_full_name()}"
        self.assertEqual(str(profile), expected)
    
    def test_profile_completion_percentage(self):
        """Test completion percentage calculation"""
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.completion_percentage, 0)
        
        profile.bio = "Test bio"
        profile.location = "Test location"
        self.assertEqual(profile.completion_percentage, 50)
        
        # Create temporary files for avatar and resume
        avatar_file = SimpleUploadedFile("avatar.jpg", b"file_content", content_type="image/jpeg")
        resume_file = SimpleUploadedFile("resume.pdf", b"file_content", content_type="application/pdf")
        
        profile.avatar = avatar_file
        profile.resume = resume_file
        self.assertEqual(profile.completion_percentage, 100)
    
    def test_profile_validation(self):
        """Test profile validation"""
        profile, _ = Profile.objects.update_or_create(user=self.user)
      
        from decimal import Decimal
        profile.salary_expectation = Decimal('-1000')
        # if profile.salary_expectation =< 0: the save method turns it to none
        profile.save()
        
        profile.refresh_from_db()
        self.assertIsNone(profile.salary_expectation)
        
    
    def test_linkedin_url_validation(self):
        """Test LinkedIn URL validation"""
        profile,_ = Profile.objects.update_or_create(user=self.user)
        
        # Valid LinkedIn URLs
        valid_urls = [
            'https://linkedin.com/in/testuser',
            'https://www.linkedin.com/in/test-user/',
            'http://linkedin.com/in/testuser123'
        ]
        
        for url in valid_urls:
            profile.linkedin_url = url
            try:
                profile.full_clean()
            except ValidationError:
                self.fail(f"LinkedIn URL {url} should be valid")
        
        # Invalid LinkedIn URLs
        invalid_urls = [
            'https://facebook.com/testuser',
            'https://linkedin.com/company/test',
            'not-a-url'
        ]
        
        for url in invalid_urls:
            profile.linkedin_url = url
            with self.assertRaises(ValidationError):
                profile.full_clean()
    
    def test_github_url_validation(self):
        """Test GitHub URL validation"""
        profile, _ = Profile.objects.update_or_create(user=self.user)
        
        # Valid GitHub URLs
        valid_urls = [
            'https://github.com/testuser',
            'https://www.github.com/test-user/',
            'http://github.com/testuser123'
        ]
        
        for url in valid_urls:
            profile.github_url = url
            try:
                profile.full_clean()
            except ValidationError:
                self.fail(f"GitHub URL {url} should be valid")
        
        # Invalid GitHub URLs
        invalid_urls = [
            'https://gitlab.com/testuser',
            'https://github.com/testuser/repo',
            'not-a-url'
        ]
        
        for url in invalid_urls:
            profile.github_url = url
            with self.assertRaises(ValidationError):
                profile.full_clean()
