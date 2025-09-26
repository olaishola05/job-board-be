from rest_framework.throttling import AnonRateThrottle


class AuthenticationThrottle(AnonRateThrottle):
    """Custom throttle for authentication endpoints"""
    scope = 'auth'
    rate = '10/min'


class PasswordResetThrottle(AnonRateThrottle):
    """Custom throttle for password reset endpoints"""
    scope = 'password_reset'
    rate = '3/min'
