from django.contrib.auth import get_user_model
from .models import Company


User = get_user_model()

def set_user_context(obj, user, action='update'):
    """
    Utility function to set user context on model instances
    for audit logging purposes
    """
    if action == 'update':
        obj._updated_by = user
    elif action == 'delete':
        obj._deleted_by = user
    return obj


def verify_company(company, verified_by):
    """
    Utility function to verify a company with proper audit logging
    """
    from .signals import company_verified
    
    company.is_verified = True
    company = set_user_context(company, verified_by, 'update')
    company.save()
    
    # Send custom signal for additional processing
    company_verified.send(
        sender=Company,
        company=company,
        verified_by=verified_by
    )
    
    return company


def feature_company(company, featured_by):
    """
    Utility function to feature a company with proper audit logging
    """
    from .signals import company_featured
    
    company.is_featured = True
    company = set_user_context(company, featured_by, 'update')
    company.save()
    
    # Send custom signal for additional processing
    company_featured.send(
        sender=Company,
        company=company,
        featured_by=featured_by
    )
    
    return company
