from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.companies.models import Company, Industry, CompanyFollow
from apps.jobs.models import Job

User = get_user_model()


class IndustryModelTest(TestCase):
    def setUp(self):
        self.industry_data = {
            'name': 'Technology',
            'slug': 'technology',
            'description': 'Tech industry'
        }
    
    def test_industry_creation(self):
        """Test industry creation"""
        industry = Industry.objects.create(**self.industry_data)
        self.assertEqual(industry.name, 'Technology')
        self.assertEqual(industry.slug, 'technology')
        self.assertTrue(industry.is_active)
    
    def test_industry_str_method(self):
        """Test industry string representation"""
        industry = Industry.objects.create(**self.industry_data)
        self.assertEqual(str(industry), 'Technology')
    
    def test_industry_slug_auto_generation(self):
        """Test automatic slug generation"""
        industry = Industry.objects.create(
            name='Artificial Intelligence',
            description='AI industry'
        )
        self.assertEqual(industry.slug, 'artificial-intelligence')
    
    def test_industry_active_manager(self):
        """Test active manager"""
        active_industry = Industry.objects.create(name='Active Tech', slug='active-tech')
        inactive_industry = Industry.objects.create(
            name='Inactive Tech', 
            slug='inactive-tech',
            is_active=False
        )
        
        # Test default manager
        self.assertEqual(Industry.objects.count(), 2)
        
        # Test active manager
        self.assertEqual(Industry.active.count(), 1)
        self.assertIn(active_industry, Industry.active.all())
        self.assertNotIn(inactive_industry, Industry.active.all())


class CompanyModelTest(TestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            email='employer@test.com',
            username='employer',
            password='testpass',
            role='employer'
        )
        self.industry = Industry.objects.create(name='Technology')
        self.company_data = {
            'name': 'Test Company',
            'description': 'A test company',
            'website': 'https://test.com',
            'location': 'Lagos, Nigeria',
            'industry': self.industry,
            'created_by': self.employer
        }

    def test_company_creation(self):
        company = Company.objects.create(**self.company_data)
        self.assertEqual(company.name, 'Test Company')
        self.assertEqual(company.slug, 'test-company')
        self.assertEqual(company.approval_status, 'pending')
        self.assertFalse(company.is_verified)

    def test_company_slug_uniqueness(self):
        Company.objects.create(**self.company_data)
        company_data_2 = self.company_data.copy()
        company_data_2['created_by'] = User.objects.create_user(
            email='employer2@test.com', username='employer2', password='testpass', role='employer'
        )
        company2 = Company.objects.create(**company_data_2)
        self.assertEqual(company2.slug, 'test-company-1')

    def test_company_str_representation(self):
        company = Company.objects.create(**self.company_data)
        self.assertEqual(str(company), 'Test Company')

    def test_company_average_salary_property(self):
        from apps.jobs.models import Job, JobCategory
        company = Company.objects.create(**self.company_data)
        category = JobCategory.objects.create(name='Software Development')
        
        Job.objects.create(
            title='Developer',
            company=company,
            category=category,
            description='Test job',
            requirements='Test requirements',
            responsibilities='Test responsibilities',
            job_type='full_time',
            experience_level='mid',
            location='Lagos',
            salary_min=100000,
            salary_max=150000,
            status='published',
            created_by=self.employer
        )
        
        avg_salary = company.average_salary
        self.assertIsNotNone(avg_salary)
        self.assertEqual(avg_salary['avg_min'], 100000)
        self.assertEqual(avg_salary['avg_max'], 150000)

class CompanyFollowModelTest(TestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            email='employer@test.com', username='employer',
            password='testpass', role='employer'
        )
        self.user = User.objects.create_user(
            email='user@test.com', username='user',
            password='testpass', role='user'
        )
        self.company = Company.objects.create(
            name='Test Company',
            description='A test company',
            location='Lagos',
            created_by=self.employer
        )

    def test_company_follow_creation(self):
        follow = CompanyFollow.objects.create(
            company=self.company,
            user=self.user
        )
        self.assertEqual(follow.company, self.company)
        self.assertEqual(follow.user, self.user)
        self.assertTrue(follow.notifications_enabled)

    def test_unique_company_user_follow(self):
        CompanyFollow.objects.create(company=self.company, user=self.user)
        
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            CompanyFollow.objects.create(company=self.company, user=self.user)