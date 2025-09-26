from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from apps.companies.models import Company, Industry
from apps.companies.serializers import (
    CompanyListSerializer, CompanyDetailSerializer,
    CompanyCreateUpdateSerializer
)


User = get_user_model()

class CompanySerializerTest(TestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            email='employer@test.com', username='employer',
            password='testpass', role='employer'
        )
        self.industry = Industry.objects.create(name='Technology')
        self.company = Company.objects.create(
            name='Test Company',
            description='A test company',
            location='Lagos',
            industry=self.industry,
            created_by=self.employer,
            is_verified=True
        )

    def test_company_list_serializer(self):
        serializer = CompanyListSerializer(self.company)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test Company')
        self.assertEqual(data['industry_name'], 'Technology')
        self.assertIn('job_count', data)
        self.assertIn('follower_count', data)

    def test_company_detail_serializer(self):
        factory = RequestFactory()
        request = factory.get('/companies/')
        request.user = self.employer
      
        serializer = CompanyDetailSerializer(self.company, context={'request': request})
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test Company')
        self.assertEqual(data['description'], 'A test company')
        self.assertTrue(data['is_verified'])
        self.assertIn('industry', data)
        self.assertIn('created_by', data)
        
        self.assertFalse(data['is_following'])

    def test_company_create_serializer_validation(self):
        data = {
            'name': 'New Company',
            'description': 'A new company',
            'location': 'Lagos',
            'founded_year': 2026
        }
        serializer = CompanyCreateUpdateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('founded_year', serializer.errors)