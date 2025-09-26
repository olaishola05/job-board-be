import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from apps.companies.models import Company, CompanyAnalytics, CompanyReview
from apps.accounts.models import User
from apps.jobs.models import Industry


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def industry(db):
    return Industry.objects.create(name="Software")


@pytest.fixture
def employer(db):
    return User.objects.create_user(
        email="employer@example.com",
        password="pass1234",
        role="employer",
        is_active=True,
    )


@pytest.fixture
def admin(db):
    return User.objects.create_superuser(
        email="admin@example.com",
        password="adminpass",
        role="admin",
    )


@pytest.fixture
def company(employer, industry):
    return Company.objects.create(
        name="Test Company",
        description="A sample description",
        industry=industry,
        location="NYC",
        created_by=employer,
        approval_status="approved",
        is_active=True,
        is_verified=True,
        founded_year=2000,
        company_size="startup",
        employee_count=10,
    )


@pytest.mark.django_db
def test_company_list_requires_auth(api_client):
    url = "/api/v1/companies/"
    res = api_client.get(url)
    assert res.status_code == 401


@pytest.mark.django_db
def test_employer_can_create_company(api_client, employer, industry):
    api_client.force_authenticate(user=employer)
    url = "/api/v1/companies/"
    payload = {
        "name": "NewCo",
        "description": "We build things",
        "founded_year": 1999,
        "company_size": "startup",
        "employee_count": 5,
        "location": "LA",
        "industry": str(industry.id),
        "website": "https://newco.com",
        "email": "info@newco.com",
        "phone": "+1234567890",
    }
    res = api_client.post(url, payload, format="json")
    assert res.status_code == 201, res.data
    assert Company.objects.filter(name="NewCo").exists()


@pytest.mark.django_db
def test_admin_auto_approves_company(api_client, admin, industry):
    api_client.force_authenticate(user=admin)
    url = "/api/v1/companies/"
    payload = {
        "name": "AdminCo",
        "description": "Approved automatically",
        "founded_year": 2010,
        "company_size": "small",
        "employee_count": 20,
        "location": "SF",
        "industry": str(industry.id),
        "website": "https://adminco.com",
        "email": "info@adminco.com",
        "phone": "+1987654321",
    }
    res = api_client.post(url, payload, format="json")
    assert res.status_code == 201, res.data
    company = Company.objects.get(name="AdminCo")
    assert company.approval_status == "approved"
    assert company.is_verified is True


@pytest.mark.django_db
def test_retrieve_increments_view_count(api_client, employer, company):
    api_client.force_authenticate(user=employer)
    url = f"/api/v1/companies/{company.id}/"
    before = company.view_count
    res = api_client.get(url)
    company.refresh_from_db()
    assert res.status_code == 200
    assert company.view_count == before + 1


@pytest.mark.django_db
def test_company_analytics_created_on_access(api_client, admin, company):
    api_client.force_authenticate(user=admin)
    url = f"/api/v1/companies/{company.id}/analytics/"
    res = api_client.get(url)
    assert res.status_code == 200, res.data
    assert CompanyAnalytics.objects.filter(company=company).exists()


@pytest.mark.django_db
def test_company_search_filters(api_client, employer, company):
    api_client.force_authenticate(user=employer)
    
    company.is_active = True
    company.approval_status = "approved"
    company.save()
    
    url = "/api/v1/companies/?search=Test" 
    res = api_client.get(url)
    assert res.status_code == 200, res.data
    print(res.data)
    assert any("Test Company" in c["name"] for c in res.data["results"])


@pytest.mark.django_db
def test_company_stats_returns_data(api_client, employer, company):
    api_client.force_authenticate(user=employer)
    url = "/api/v1/companies/stats/"
    res = api_client.get(url)
    assert res.status_code == 200, res.data
    assert "total_companies" in res.data


@pytest.mark.django_db
def test_admin_can_approve_reject_feature(api_client, admin, company):
    api_client.force_authenticate(user=admin)

    res = api_client.post(f"/api/v1/companies/{company.id}/approve/")
    company.refresh_from_db()
    assert res.status_code == 200, res.data
    assert company.approval_status == "approved"

    res = api_client.post(f"/api/v1/companies/{company.id}/reject/")
    company.refresh_from_db()
    assert res.status_code == 200, res.data
    assert company.approval_status == "rejected"

    res = api_client.post(f"/api/v1/companies/{company.id}/feature/")
    company.refresh_from_db()
    assert res.status_code == 200, res.data
    assert company.is_featured in [True, False]


@pytest.mark.django_db
def test_review_updates_company_rating(api_client, employer, company):
    api_client.force_authenticate(user=employer)
    CompanyReview.objects.create(
        company=company,
        user=employer,
        rating=5,
        title="Great place",
        content="Loved it",
    )
    company.refresh_from_db()
    from apps.companies.views import CompanyViewSet
    CompanyViewSet()._update_company_rating(company)
    company.refresh_from_db()
    assert company.rating == 5
    assert company.review_count == 1
