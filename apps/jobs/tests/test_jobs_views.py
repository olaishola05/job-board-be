import pytest
from rest_framework.test import APIClient
from rest_framework import status

from apps.jobs.models import (
    Job, JobApplication, SavedJob, JobAlert,
    JobCategory, JobType, Industry, Skill
)
from apps.companies.models import Company
from django.core.files.uploadedfile import SimpleUploadedFile


# -------------------------------
# Fixtures
# -------------------------------

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def employer(django_user_model):
    return django_user_model.objects.create_user(
        username="employer",
        email="employer@example.com",
        password="password123",
        role="employer",
    )


@pytest.fixture
def applicant(django_user_model):
    return django_user_model.objects.create_user(
        username="applicant",
        email="applicant@example.com",
        password="password123",
        role="user",
    )


@pytest.fixture
def admin(django_user_model):
    return django_user_model.objects.create_user(
        username="admin",
        email="admin@example.com",
        password="password123",
        role="admin",
    )


@pytest.fixture
def company(employer):
    return Company.objects.create(name="Test Company", created_by=employer)


@pytest.fixture
def job(employer, company):
    return Job.objects.create(
        title="Test Job",
        description="Test description",
        requirements="Some requirements",
        company=company,
        created_by=employer,
        status="published",
        is_featured=True,
    )


# -------------------------------
# JobViewSet
# -------------------------------

@pytest.mark.django_db
def test_list_jobs(api_client, job):
    url = f"/api/v1/jobs/"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["title"] == job.title 

@pytest.mark.django_db
def test_retrieve_job(api_client, job):
    url = f"/api/v1/jobs/{job.id}/"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == str(job.id)
    
@pytest.mark.django_db
def test_apply_job(api_client, applicant, job):
    api_client.force_authenticate(user=applicant)
    url = f"/api/v1/jobs/{job.id}/apply/"
    
    dummy_resume = SimpleUploadedFile(
        "resume.pdf", b"fake-pdf-content", content_type="application/pdf"
    )

    application = {
        "cover_letter": "Please I need a job sir",
        "resume": dummy_resume,
    }
    first_response = api_client.post(url, application, format="multipart")
    assert first_response.status_code == status.HTTP_201_CREATED
    assert JobApplication.objects.filter(job=job, applicant=applicant).exists()
    
    dummy_resume2 = SimpleUploadedFile(
        "resume2.pdf", b"another-fake-pdf-content", content_type="application/pdf"
    )
    application['resume'] = dummy_resume2

    second_response = api_client.post(url, application, format="multipart")

    assert second_response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already applied" in str(second_response.data).lower()
    assert JobApplication.objects.filter(job=job, applicant=applicant).count() == 1



@pytest.mark.django_db
def test_save_and_unsave_job(api_client, applicant, job):
    api_client.force_authenticate(user=applicant)
    url = f"/api/v1/jobs/{job.id}/save/"

    response = api_client.post(url)
    assert response.status_code == status.HTTP_201_CREATED
    assert SavedJob.objects.filter(job=job, user=applicant).exists()

    response = api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not SavedJob.objects.filter(job=job, user=applicant).exists()


@pytest.mark.django_db
def test_featured_jobs(api_client, job):
    url = f"/api/v1/jobs/featured/"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert any(j["id"] == str(job.id) for j in response.data["results"])


@pytest.mark.django_db
def test_stats_for_employer(api_client, employer, job):
    api_client.force_authenticate(user=employer)
    url = f"/api/v1/jobs/stats/"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    print(response.data)
    assert "total_jobs" in response.data


# -------------------------------
# JobApplicationViewSet
# -------------------------------

@pytest.mark.django_db
def test_my_applications(api_client, applicant, job):
    JobApplication.objects.create(job=job, applicant=applicant)
    api_client.force_authenticate(user=applicant)
    url = f"/api/v1/jobs/applications/my_applications/"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["job"]["id"] == str(job.id)

@pytest.mark.django_db
def test_withdraw_application(api_client, applicant, job):
    app = JobApplication.objects.create(job=job, applicant=applicant)
    api_client.force_authenticate(user=applicant)
    url = f"/api/v1/jobs/applications/{app.id}/withdraw/"
    response = api_client.post(url)
    assert response.status_code == status.HTTP_200_OK
    assert "withdrawn" in response.data["message"].lower()

# -------------------------------
# SavedJobViewSet
# -------------------------------

@pytest.mark.django_db
def test_clear_all_saved_jobs(api_client, applicant, job):
    SavedJob.objects.create(job=job, user=applicant)
    api_client.force_authenticate(user=applicant)
    url = f"/api/v1/jobs/saved-jobs/clear_all/"
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["deleted_count"] == 1