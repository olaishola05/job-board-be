from rest_framework import permissions
from rest_framework.permissions import BasePermission
from functools import wraps
from django.http import JsonResponse
from django.http import HttpResponseForbidden
from rest_framework import status


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IsAdminUser(BasePermission):
    """
    Permission for admin users only
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            getattr(request.user, "role", None) == "admin"
        )


class IsEmployerUser(BasePermission):
    """
    Permission for employer users only
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'employer'
        )


class IsJobSeekerUser(BasePermission):
    """
    Permission for job seeker users only
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'user'
        )


class IsEmployerOrAdmin(BasePermission):
    """
    Permission for employer or admin users
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['employer', 'admin']
        )


class IsVerifiedUser(BasePermission):
    """
    Permission for verified users only
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_verified
        )


class IsActiveUser(BasePermission):
    """
    Permission for active users only
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_active
        )


class IsOwner(BasePermission):
    """
    Permission to check if user is owner of the object
    """
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id
        return False


class CanManageUsers(BasePermission):
    """
    Permission for users who can manage other users (admin only)
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'admin' and
            request.user.is_staff
        )


class CanViewUserProfile(BasePermission):
    """
    Permission to view user profiles - own profile or admin
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj.user == request.user if hasattr(obj, 'user') else obj == request.user

def admin_required(view_func):
    """
    Decorator for views that require admin role
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if request.user.role != 'admin':
            return JsonResponse({'error': 'Admin access required'}, status=HttpResponseForbidden)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def employer_required(view_func):
    """
    Decorator for views that require employer role
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if request.user.role != 'employer':
            return JsonResponse({'error': 'Employer access required'}, status=HttpResponseForbidden)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def job_seeker_required(view_func):
    """
    Decorator for views that require job seeker or user role
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if request.user.role != 'user':
            return JsonResponse({'error': 'user access required'}, status=HttpResponseForbidden)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def verified_required(view_func):
    """
    Decorator for views that require verified email
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not request.user.is_verified:
            return JsonResponse({'error': 'Email verification required'}, status=HttpResponseForbidden)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def active_required(view_func):
    """
    Decorator for views that require active account
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not request.user.is_active:
            return JsonResponse({'error': 'Account activation required'}, status=HttpResponseForbidden)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def role_required(*allowed_roles):
    """
    Decorator for views that require specific roles
    Usage: @role_required('admin', 'employer')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            if request.user.role not in allowed_roles:
                return JsonResponse({
                    'error': f'Access denied. Required roles: {", ".join(allowed_roles)}'
                }, status=HttpResponseForbidden)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator



class IsCompanyOwnerOrAdmin(BasePermission):
    """
    Permission for company owners or admin users
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class CanApplyToJob(BasePermission):
    """
    Permission to apply to jobs - user only, not to own company jobs
    """
    def has_object_permission(self, request, view, obj):
        # Only job seekers can apply
        if request.user.role != 'user':
            return False
        
        # Can't apply to jobs from own company (if user is also an employer)
        if hasattr(obj, 'company') and hasattr(obj.company, 'created_by'):
            return obj.company.created_by != request.user
        
        return True


class CanManageJobApplications(BasePermission):
    """
    Permission to manage job applications - company owners and admins
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        
        if hasattr(obj, 'job') and hasattr(obj.job, 'company'):
            return obj.job.company.created_by == request.user
        
        return False


class ReadOnlyOrOwnerWrite(BasePermission):
    """
    Permission that allows read-only access to everyone, but write access only to owner
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return obj == request.user


class IsAccountOwnerOrAdmin(BasePermission):
    """
    Permission for account owners or admin users to manage user accounts
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj == request.user