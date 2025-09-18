from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
class AuditLog(models.Model):
    """
    Audit log for tracking important actions
    """
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('apply', 'Apply'),
        ('view', 'View'),
        ('save_job', 'Save Job'),
        ('unsave_job', 'Unsave Job'),
        ('withdraw_application', 'Withdraw Application'),
        ('change_status', 'Change Status'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, db_index=True)
    object_type = models.CharField(max_length=50, db_index=True)
    object_id = models.CharField(max_length=100, db_index=True)
    object_repr = models.CharField(max_length=200, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['object_type', 'object_id']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['session_key', 'timestamp']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        return f"{self.action} {self.object_type} by {self.user or 'Anonymous'}"
    
    @classmethod
    def log_action(cls, user, action, obj, details=None, request=None):
        """Helper method to create audit log entries"""
        log_data = {
            'user': user,
            'action': action,
            'object_type': obj.__class__.__name__,
            'object_id': str(obj.pk),
            'object_repr': str(obj),
            'details': details or {},
        }
        
        if request:
            log_data.update({
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'session_key': request.session.session_key,
            })
        
        return cls.objects.create(**log_data)

