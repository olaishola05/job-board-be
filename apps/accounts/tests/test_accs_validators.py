from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.accounts.models import phone_regex, validate_linkedin_url, validate_github_url
from apps.jobs.models import validate_salary_range
from decimal import Decimal


class ValidatorsTest(TestCase):
    def test_phone_number_validator(self):
        """Test phone number validation"""
        # Valid phone numbers
        valid_phones = [
            '+1234567890',
            '1234567890',
            '+123456789012345',
            '987654321'
        ]
        
        for phone in valid_phones:
            try:
                phone_regex(phone)
            except ValidationError:
                self.fail(f"Phone number {phone} should be valid")
        
        # Invalid phone numbers
        invalid_phones = [
            '123',  # Too short
            '+123456789012345678901',  # Too long
            'abc123',  # Contains letters
            '+abc123456789',  # Contains letters with +
            '12-34-56-78-90',  # Contains dashes
        ]
        
        for phone in invalid_phones:
            with self.assertRaises(ValidationError):
                phone_regex(phone)
    
    def test_linkedin_url_validator(self):
        """Test LinkedIn URL validation"""
        # Valid LinkedIn URLs
        valid_urls = [
            'https://linkedin.com/in/testuser',
            'https://www.linkedin.com/in/test-user/',
            'http://linkedin.com/in/testuser123',
            'https://www.linkedin.com/in/test_user_name'
        ]
        
        for url in valid_urls:
            try:
                validate_linkedin_url(url)
            except ValidationError:
                self.fail(f"LinkedIn URL {url} should be valid")
        
        # Invalid LinkedIn URLs
        invalid_urls = [
            'https://facebook.com/testuser',
            'https://linkedin.com/company/test',
            'https://linkedin.com/pub/test',
            'not-a-url',
            'https://linkedin.com/in/',
            'https://linkedin.com/in',
        ]
        
        for url in invalid_urls:
            with self.assertRaises(ValidationError):
                validate_linkedin_url(url)
    
    def test_github_url_validator(self):
        """Test GitHub URL validation"""
        # Valid GitHub URLs
        valid_urls = [
            'https://github.com/testuser',
            'https://www.github.com/test-user/',
            'http://github.com/testuser123'
        ]
        
        for url in valid_urls:
            try:
                validate_github_url(url)
            except ValidationError:
                self.fail(f"GitHub URL {url} should be valid")
        
        # Invalid GitHub URLs
        invalid_urls = [
            'https://gitlab.com/testuser',
            'https://github.com/testuser/repo',
            'not-a-url',
            'https://github.com/',
            'https://github.com'
        ]
        
        for url in invalid_urls:
            with self.assertRaises(ValidationError):
                validate_github_url(url)
    
    def test_salary_range_validator(self):
        """Test salary range validation"""
        # Valid ranges
        try:
            validate_salary_range(Decimal('50000'), Decimal('80000'))
            validate_salary_range(Decimal('50000'), Decimal('50000'))  # Equal
            validate_salary_range(None, Decimal('80000'))  # Min only
            validate_salary_range(Decimal('50000'), None)  # Max only
            validate_salary_range(None, None)  # Both None
        except ValidationError:
            self.fail("Valid salary ranges should not raise ValidationError")
        
        # Invalid range (min > max)
        with self.assertRaises(ValidationError):
            validate_salary_range(Decimal('80000'), Decimal('50000'))
