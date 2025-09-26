from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

from apps.jobs.models import (
    Job, JobApplication, SavedJob, JobAlert, JobView,
    JobCategory, JobType, Industry, Skill, SkillCategory, Company
)
from apps.jobs.serializers import (
    JobListSerializer, JobDetailSerializer, JobCreateUpdateSerializer,
    JobApplicationDetailSerializer, JobApplicationCreateSerializer, 
    JobApplicationUpdateSerializer, SavedJobSerializer, SavedJobCreateSerializer,
    JobAlertDetailSerializer, JobAlertCreateUpdateSerializer, SkillSerializer,
    IndustrySerializer, JobCategorySerializer, JobTypeSerializer,
    BulkJobStatusUpdateSerializer, JobSearchSerializer
)

User = get_user_model()

class SkillSerializerTest(TestCase):
    def setUp(self):
        self.skill_category = SkillCategory.objects.create(name='Programming')
        self.skill = Skill.objects.create(
            name='Python',
            category=self.skill_category,
            popularity_score=100
        )
    
    def test_skill_serialization(self):
        """Test skill serialization"""
        serializer = SkillSerializer(self.skill)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Python')
        self.assertEqual(data['popularity_score'], 100)
        self.assertIn('id', data)
        self.assertIn('slug', data)
    
    def test_skill_deserialization_valid(self):
        """Test skill deserialization with valid data"""
        data = {
            'name': 'JavaScript',
            'category': self.skill_category.id
        }
        serializer = SkillSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['name'], 'JavaScript')
    
    def test_skill_deserialization_invalid(self):
        """Test skill deserialization with invalid data"""
        data = {'name': ''}  # Empty name
        serializer = SkillSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

class JobCategorySerializerTest(TestCase):
    def setUp(self):
        self.parent_category = JobCategory.objects.create(name='Technology')
        self.child_category = JobCategory.objects.create(
            name='Software Development',
            parent=self.parent_category
        )
    
    def test_category_serialization_with_subcategories(self):
        """Test category serialization including subcategories"""
        serializer = JobCategorySerializer(self.parent_category)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Technology')
        self.assertEqual(len(data['subcategories']), 1)
        self.assertEqual(data['subcategories'][0]['name'], 'Software Development')
    
    def test_category_serialization_without_subcategories(self):
        """Test category serialization without subcategories"""
        serializer = JobCategorySerializer(self.child_category)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Software Development')
        self.assertEqual(data['subcategories'], [])

class JobCreateUpdateSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='employer@test.com',
            username='employer',
            role='employer',
            password='testpass123'
        )
        
        self.industry = Industry.objects.create(name='Technology')
        self.category = JobCategory.objects.create(name='Software Development')
        self.skill = Skill.objects.create(name='Python')
        
        self.company = Company.objects.create(
            name='Test Company',
            description='Test description',
            location='Remote',
            created_by=self.user,
            industry=self.industry
        )
        
        self.valid_data = {
            'title': 'Senior Python Developer',
            'description': 'Job description here',
            'requirements': 'Job requirements here',
            'responsibilities': 'Job responsibilities here',
            'category': self.category.id,
            'industry': self.industry.id,
            'skills': [self.skill.id],
            'job_type': 'full_time',
            'experience_level': 'senior',
            'location': 'Remote',
            'salary_min': Decimal('80000.00'),
            'salary_max': Decimal('120000.00'),
            'salary_currency': 'USD',
            'remote_allowed': True,
            'status': 'published'
        }
    
    def test_valid_job_creation(self):
        """Test creating job with valid data"""
        serializer = JobCreateUpdateSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        job = serializer.save(company=self.company, created_by=self.user)
        
        self.assertEqual(job.title, 'Senior Python Developer')
        self.assertEqual(job.job_type, 'full_time')
        self.assertEqual(job.skills.count(), 1)
        self.assertEqual(job.skills.first().name, 'Python')
    
    def test_invalid_salary_range(self):
        """Test validation of invalid salary range"""
        invalid_data = self.valid_data.copy()
        invalid_data['salary_min'] = Decimal('120000.00')
        invalid_data['salary_max'] = Decimal('80000.00')
        
        serializer = JobCreateUpdateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_past_application_deadline(self):
        """Test validation of past application deadline"""
        invalid_data = self.valid_data.copy()
        invalid_data['application_deadline'] = timezone.now() - timedelta(days=1)
        
        serializer = JobCreateUpdateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_job_update(self):
        """Test updating existing job"""
        job = Job.objects.create(
            title='Original Title',
            description='Original description',
            requirements='Original requirements',
            responsibilities='Original responsibilities',
            company=self.company,
            created_by=self.user,
            job_type='part_time',
            experience_level='junior',
            location='New York'
        )
        
        update_data = {
            'title': 'Updated Title',
            'job_type': 'full_time',
            'experience_level': 'senior',
            'skills': [self.skill.id]
        }
        
        serializer = JobCreateUpdateSerializer(job, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_job = serializer.save()
        
        self.assertEqual(updated_job.title, 'Updated Title')
        self.assertEqual(updated_job.job_type, 'full_time')
        self.assertEqual(updated_job.skills.count(), 1)

class JobListSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@test.com',
            username='user',
            role='user',
            password='testpass123'
        )
        
        self.employer = User.objects.create_user(
            email='employer@test.com',
            username='employer',
            role='employer',
            password='testpass123'
        )
        
        self.industry = Industry.objects.create(name='Technology')
        self.category = JobCategory.objects.create(name='Software Development')
        self.skill = Skill.objects.create(name='Python')
        
        self.company = Company.objects.create(
            name='Test Company',
            description='Test description',
            location='Remote',
            created_by=self.employer,
            industry=self.industry
        )
        
        self.job = Job.objects.create(
            title='Python Developer',
            description='Job description',
            requirements='Job requirements',
            responsibilities='Job responsibilities',
            company=self.company,
            category=self.category,
            industry=self.industry,
            created_by=self.employer,
            job_type='full_time',
            experience_level='mid',
            location='Remote',
            status='published',
            salary_min=70000,
            salary_max=90000,
            views_count=100,
            applications_count=5
        )
        self.job.skills.add(self.skill)
    
    def test_job_list_serialization_anonymous_user(self):
        """Test job serialization for anonymous user"""
        serializer = JobListSerializer(self.job)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Python Developer')
        self.assertEqual(data['job_type'], 'full_time')
        self.assertEqual(data['views_count'], 100)
        self.assertEqual(data['applications_count'], 5)
        self.assertFalse(data['is_saved'])
        self.assertFalse(data['has_applied'])
        self.assertEqual(len(data['skills']), 1)
    
    def test_job_list_serialization_with_saved_job(self):
        """Test job serialization when user has saved the job"""
        SavedJob.objects.create(user=self.user, job=self.job)
        
        request_mock = type('Request', (), {'user': self.user})()
        context = {'request': request_mock}
        
        serializer = JobListSerializer(self.job, context=context)
        data = serializer.data
        
        self.assertTrue(data['is_saved'])
        self.assertFalse(data['has_applied'])
    
    def test_job_list_serialization_with_application(self):
        """Test job serialization when user has applied"""
        JobApplication.objects.create(job=self.job, applicant=self.user)
        
        request_mock = type('Request', (), {'user': self.user})()
        context = {'request': request_mock}
        
        serializer = JobListSerializer(self.job, context=context)
        data = serializer.data
        
        self.assertFalse(data['is_saved'])
        self.assertTrue(data['has_applied'])

class JobApplicationCreateSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@test.com',
            username='user',
            role='user',
            password='testpass123'
        )
        
        self.employer = User.objects.create_user(
            email='employer@test.com',
            username='employer',
            role='employer',
            password='testpass123'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            description='Test description',
            location='Remote',
            created_by=self.employer
        )
        
        self.active_job = Job.objects.create(
            title='Active Job',
            description='Job description',
            requirements='Job requirements',
            responsibilities='Job responsibilities',
            company=self.company,
            created_by=self.employer,
            job_type='full_time',
            experience_level='mid',
            location='Remote',
            status='published'
        )
        
        self.closed_job = Job.objects.create(
            title='Closed Job',
            description='Job description',
            requirements='Job requirements',
            responsibilities='Job responsibilities',
            company=self.company,
            created_by=self.employer,
            job_type='full_time',
            experience_level='mid',
            location='Remote',
            status='closed'
        )
    
    def test_valid_application_creation(self):
        """Test creating application with valid data"""
        data = {
            'job': self.active_job.id,
            'cover_letter': 'Test cover letter'
        }
        
        request_mock = type('Request', (), {'user': self.user})()
        context = {'request': request_mock}
        
        serializer = JobApplicationCreateSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        
        application = serializer.save()
        
        self.assertEqual(application.job, self.active_job)
        self.assertEqual(application.applicant, self.user)
        self.assertEqual(application.cover_letter, 'Test cover letter')
    
    def test_application_to_inactive_job(self):
        """Test applying to inactive job"""
        data = {
            'job': self.closed_job.id,
            'cover_letter': 'Test cover letter'
        }
        
        request_mock = type('Request', (), {'user': self.user})()
        context = {'request': request_mock}
        
        serializer = JobApplicationCreateSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('job', serializer.errors)
    
    def test_duplicate_application(self):
        """Test preventing duplicate applications"""
        # Create first application
        JobApplication.objects.create(job=self.active_job, applicant=self.user)
        
        data = {
            'job': self.active_job.id,
            'cover_letter': 'Duplicate application'
        }
        
        request_mock = type('Request', (), {'user': self.user})()
        context = {'request': request_mock}
        
        serializer = JobApplicationCreateSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

class JobApplicationUpdateSerializerTest(TestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            email='employer@test.com',
            username='employer',
            role='employer',
            password='testpass123'
        )
        
        self.user = User.objects.create_user(
            email='user@test.com',
            username='user',
            role='user',
            password='testpass123'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            description='Test description',
            location='Remote',
            created_by=self.employer
        )
        
        self.job = Job.objects.create(
            title='Test Job',
            description='Job description',
            requirements='Job requirements',
            responsibilities='Job responsibilities',
            company=self.company,
            created_by=self.employer,
            job_type='full_time',
            experience_level='mid',
            location='Remote',
            status='published'
        )
        
        self.application = JobApplication.objects.create(
            job=self.job,
            applicant=self.user,
            cover_letter='Test cover letter'
        )
    
    def test_valid_application_update(self):
        """Test updating application with valid data"""
        data = {
            'status': 'under_review',
            'notes': 'Good candidate',
            'score': 8
        }
        
        request_mock = type('Request', (), {'user': self.employer})()
        context = {'request': request_mock}
        
        serializer = JobApplicationUpdateSerializer(
            self.application, data=data, context=context
        )
        self.assertTrue(serializer.is_valid())
        
        updated_application = serializer.save()
        
        self.assertEqual(updated_application.status, 'under_review')
        self.assertEqual(updated_application.notes, 'Good candidate')
        self.assertEqual(updated_application.score, 8)
        self.assertEqual(updated_application.reviewed_by, self.employer)
        self.assertIsNotNone(updated_application.reviewed_at)
    
    def test_update_withdrawn_application(self):
        """Test updating withdrawn application (should fail)"""
        self.application.status = 'withdrawn'
        self.application.save()
        
        data = {'status': 'under_review'}
        
        serializer = JobApplicationUpdateSerializer(self.application, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)

class SavedJobCreateSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@test.com',
            username='user',
            role='user',
            password='testpass123'
        )
        
        self.employer = User.objects.create_user(
            email='employer@test.com',
            username='employer',
            role='employer',
            password='testpass123'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            description='Test description',
            location='Remote',
            created_by=self.employer
        )
        
        self.job = Job.objects.create(
            title='Test Job',
            description='Job description',
            requirements='Job requirements',
            responsibilities='Job responsibilities',
            company=self.company,
            created_by=self.employer,
            job_type='full_time',
            experience_level='mid',
            location='Remote',
            status='published'
        )
    
    def test_valid_saved_job_creation(self):
        """Test creating saved job with valid data"""
        data = {
            'job': self.job.id,
            'notes': 'Interesting position'
        }
        
        request_mock = type('Request', (), {'user': self.user})()
        context = {'request': request_mock}
        
        serializer = SavedJobCreateSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        
        saved_job = serializer.save()
        
        self.assertEqual(saved_job.job, self.job)
        self.assertEqual(saved_job.user, self.user)
        self.assertEqual(saved_job.notes, 'Interesting position')
    
    def test_duplicate_saved_job(self):
        """Test preventing duplicate saved jobs"""
        SavedJob.objects.create(user=self.user, job=self.job)
        
        data = {'job': self.job.id}
        
        request_mock = type('Request', (), {'user': self.user})()
        context = {'request': request_mock}
        
        serializer = SavedJobCreateSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

class JobAlertCreateUpdateSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@test.com',
            username='user',
            role='user',
            password='testpass123'
        )
        
        self.category = JobCategory.objects.create(name='Software Development')
        self.industry = Industry.objects.create(name='Technology')
        self.skill = Skill.objects.create(name='Python')
        self.job_type = JobType.objects.create(name='Full Time')
    
    def test_valid_job_alert_creation(self):
        """Test creating job alert with valid data"""
        data = {
            'name': 'Python Developer Jobs',
            'keywords': 'python, django',
            'location': 'Remote',
            'categories': [self.category.id],
            'industries': [self.industry.id],
            'skills': [self.skill.id],
            'job_types': [self.job_type.id],
            'experience_levels': ['mid', 'senior'],
            'salary_min': Decimal('70000.00'),
            'frequency': 'weekly'
        }
        
        request_mock = type('Request', (), {'user': self.user})()
        context = {'request': request_mock}
        
        serializer = JobAlertCreateUpdateSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        
        alert = serializer.save()
        
        self.assertEqual(alert.name, 'Python Developer Jobs')
        self.assertEqual(alert.user, self.user)
        self.assertEqual(alert.categories.count(), 1)
        self.assertEqual(alert.skills.count(), 1)
        self.assertEqual(len(alert.experience_levels), 2)
    
    def test_job_alert_update(self):
        """Test updating existing job alert"""
        alert = JobAlert.objects.create(
            user=self.user,
            name='Original Alert',
            frequency='daily'
        )
        
        update_data = {
            'name': 'Updated Alert',
            'frequency': 'weekly',
            'skills': [self.skill.id]
        }
        
        serializer = JobAlertCreateUpdateSerializer(
            alert, data=update_data, partial=True
        )
        self.assertTrue(serializer.is_valid())
        
        updated_alert = serializer.save()
        
        self.assertEqual(updated_alert.name, 'Updated Alert')
        self.assertEqual(updated_alert.frequency, 'weekly')
        self.assertEqual(updated_alert.skills.count(), 1)

class BulkJobStatusUpdateSerializerTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@test.com',
            username='admin',
            role='admin',
            password='testpass123'
        )
        
        self.employer = User.objects.create_user(
            email='employer@test.com',
            username='employer',
            role='employer',
            password='testpass123'
        )
        
        self.other_employer = User.objects.create_user(
            email='other@test.com',
            username='other',
            role='employer',
            password='testpass123'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            description='Test description',
            location='Remote',
            created_by=self.employer
        )
        
        self.other_company = Company.objects.create(
            name='Other Company',
            description='Test description',
            location='Remote',
            created_by=self.other_employer
        )
        
        self.job1 = Job.objects.create(
            title='Job 1',
            description='Description',
            requirements='Requirements',
            responsibilities='Responsibilities',
            company=self.company,
            created_by=self.employer,
            job_type='full_time',
            experience_level='mid',
            location='Remote',
            status='draft'
        )
        
        self.job2 = Job.objects.create(
            title='Job 2',
            description='Description',
            requirements='Requirements',
            responsibilities='Responsibilities',
            company=self.company,
            created_by=self.employer,
            job_type='full_time',
            experience_level='mid',
            location='Remote',
            status='draft'
        )
        
        self.other_job = Job.objects.create(
            title='Other Job',
            description='Description',
            requirements='Requirements',
            responsibilities='Responsibilities',
            company=self.other_company,
            created_by=self.other_employer,
            job_type='full_time',
            experience_level='mid',
            location='Remote',
            status='draft'
        )
    
    def test_valid_bulk_update_admin(self):
        """Test bulk update by admin user"""
        data = {
            'job_ids': [str(self.job1.id), str(self.job2.id)],
            'status': 'published'
        }
        
        request_mock = type('Request', (), {'user': self.admin})()
        context = {'request': request_mock}
        
        serializer = BulkJobStatusUpdateSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        
        updated_count = serializer.update_jobs()
        self.assertEqual(updated_count, 2)
        
        self.job1.refresh_from_db()
        self.job2.refresh_from_db()
        
        self.assertEqual(self.job1.status, 'published')
        self.assertEqual(self.job2.status, 'published')
    
    def test_valid_bulk_update_employer_own_jobs(self):
        """Test bulk update by employer for their own jobs"""
        data = {
            'job_ids': [str(self.job1.id), str(self.job2.id)],
            'status': 'published'
        }
        
        request_mock = type('Request', (), {'user': self.employer})()
        context = {'request': request_mock}
        
        serializer = BulkJobStatusUpdateSerializer(data=data, context=context)
        self.assertTrue(serializer.is_valid())
        
        updated_count = serializer.update_jobs()
        self.assertEqual(updated_count, 2)
    
    def test_bulk_update_employer_other_jobs(self):
        """Test bulk update by employer for other user's jobs (should fail)"""
        data = {
            'job_ids': [str(self.job1.id), str(self.other_job.id)],
            'status': 'published'
        }
        
        request_mock = type('Request', (), {'user': self.employer})()
        context = {'request': request_mock}
        
        serializer = BulkJobStatusUpdateSerializer(data=data, context=context)
        self.assertFalse(serializer.is_valid())
        self.assertIn('job_ids', serializer.errors)

class JobSearchSerializerTest(TestCase):
    def test_valid_search_data(self):
        """Test search serializer with valid data"""
        category = JobCategory.objects.create(name='Software Development')
        industry = Industry.objects.create(name='Technology')
        skill = Skill.objects.create(name='Python')
        company = Company.objects.create(
            name='Test Company',
            description='Test description',
            location='Remote',
            created_by=User.objects.create_user(
                email='test@test.com',
                username='test',
                password='test123'
            )
        )
        
        data = {
            'q': 'python developer',
            'location': 'Remote',
            'remote_only': True,
            'job_type': ['full_time', 'contract'],
            'experience_level': ['mid', 'senior'],
            'category': category.id,
            'industry': industry.id,
            'salary_min': Decimal('70000.00'),
            'salary_max': Decimal('120000.00'),
            'company': company.id,
            'is_featured': True,
            'posted_days_ago': 30,
            'has_salary': True,
            'skills': [skill.id]
        }
        
        serializer = JobSearchSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['q'], 'python developer')
        self.assertTrue(validated_data['remote_only'])
        self.assertEqual(len(validated_data['job_type']), 2)
        self.assertEqual(validated_data['posted_days_ago'], 30)
    
    def test_search_serializer_optional_fields(self):
        """Test search serializer with minimal data"""
        data = {'q': 'developer'}
        
        serializer = JobSearchSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['q'], 'developer')
        self.assertNotIn('location', validated_data)
        self.assertNotIn('remote_only', validated_data)