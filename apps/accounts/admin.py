from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils import timezone
from .models import User, Profile, RefreshToken, LoginAttempt


class CustomUserCreationForm(UserCreationForm):
    """
    Custom user creation form
    """
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True


class CustomUserChangeForm(UserChangeForm):
    """
    Custom user change form
    """
    class Meta:
        model = User
        fields = '__all__'


class ProfileInline(admin.StackedInline):
    """
    Inline admin for user profiles
    """
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = (
        'bio', 'location', 'website', 'linkedin_url', 'github_url',
        'avatar', 'resume', 'experience_years', 'salary_expectation'
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom user admin
    """
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = (
        'email', 'username', 'first_name', 'last_name', 'role',
        'is_verified', 'is_active', 'is_staff', 'created_at', 'last_login'
    )
    list_filter = (
        'role', 'is_verified', 'is_active', 'is_staff', 'is_superuser',
        'created_at', 'last_login'
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'phone_number')
        }),
        ('Account info', {
            'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Security', {
            'fields': (
                'failed_login_attempts', 'account_locked_until', 'last_login_ip',
                'last_password_change'
            ),
            'classes': ('collapse',)
        }),
        ('Tokens', {
            'fields': (
                'verification_token', 'verification_token_created',
                'password_reset_token', 'password_reset_token_created',
                'activation_token', 'activation_token_created'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_login'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'first_name', 'last_name',
                'role', 'password1', 'password2'
            ),
        }),
    )
    
    readonly_fields = (
        'created_at', 'updated_at', 'last_login', 'last_password_change',
        'verification_token_created', 'password_reset_token_created',
        'activation_token_created'
    )
    
    inlines = [ProfileInline]
    
    actions = [
        'activate_users', 'deactivate_users', 'verify_users',
        'send_verification_emails', 'unlock_accounts', 'reset_failed_attempts'
    ]
    
    def activate_users(self, request, queryset):
        """Activate selected users"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} users were activated.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} users were deactivated.')
    deactivate_users.short_description = 'Deactivate selected users'
    
    def verify_users(self, request, queryset):
        """Verify selected users"""
        count = 0
        for user in queryset:
            if not user.is_verified:
                user.verify_email()
                count += 1
        self.message_user(request, f'{count} users were verified.')
    verify_users.short_description = 'Verify selected users'
    
    def send_verification_emails(self, request, queryset):
        """Send verification emails to selected users"""
        from .tasks import send_verification_email
        
        count = 0
        for user in queryset.filter(is_verified=False):
            user.generate_verification_token()
            send_verification_email.delay(user.id)
            count += 1
        
        self.message_user(request, f'Verification emails sent to {count} users.')
    send_verification_emails.short_description = 'Send verification emails'
    
    def unlock_accounts(self, request, queryset):
        """Unlock selected accounts"""
        count = 0
        for user in queryset.filter(account_locked_until__isnull=False):
            user.unlock_account()
            count += 1
        self.message_user(request, f'{count} accounts were unlocked.')
    unlock_accounts.short_description = 'Unlock selected accounts'
    
    def reset_failed_attempts(self, request, queryset):
        """Reset failed login attempts"""
        count = queryset.filter(failed_login_attempts__gt=0).update(failed_login_attempts=0)
        self.message_user(request, f'Failed attempts reset for {count} users.')
    reset_failed_attempts.short_description = 'Reset failed login attempts'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('profile')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Admin for user profiles
    """
    list_display = (
        'user_email', 'user_full_name', 'location', 'experience_years',
        'created_at', 'updated_at'
    )
    list_filter = ('location', 'experience_years', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'location')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Profile Information', {
            'fields': (
                'bio', 'location', 'website', 'linkedin_url', 'github_url',
                'experience_years', 'salary_expectation'
            )
        }),
        ('Files', {
            'fields': ('avatar', 'resume')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def user_full_name(self, obj):
        return obj.user.get_full_name()
    user_full_name.short_description = 'Full Name'
    user_full_name.admin_order_field = 'user__first_name'


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    """
    Admin for refresh tokens
    """
    list_display = (
        'user_email', 'token_short', 'created_at', 'expires_at',
        'is_revoked', 'is_expired_display', 'device_info', 'ip_address'
    )
    list_filter = ('is_revoked', 'expires_at', 'created_at')
    search_fields = ('user__email', 'token', 'ip_address', 'device_info')
    readonly_fields = ('token', 'created_at', 'expires_at', 'is_expired_display')
    
    fieldsets = (
        ('Token Info', {
            'fields': ('user', 'token', 'is_revoked')
        }),
        ('Device Info', {
            'fields': ('device_info', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at', 'is_expired_display'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['revoke_tokens', 'delete_expired_tokens']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def token_short(self, obj):
        return f"{obj.token[:20]}..." if len(obj.token) > 20 else obj.token
    token_short.short_description = 'Token'
    
    def is_expired_display(self, obj):
        return obj.is_expired
    is_expired_display.short_description = 'Is Expired'
    is_expired_display.boolean = True
    
    def revoke_tokens(self, request, queryset):
        """Revoke selected tokens"""
        count = queryset.filter(is_revoked=False).update(is_revoked=True)
        self.message_user(request, f'{count} tokens were revoked.')
    revoke_tokens.short_description = 'Revoke selected tokens'
    
    def delete_expired_tokens(self, request, queryset):
        """Delete expired tokens"""
        expired_tokens = queryset.filter(expires_at__lt=timezone.now())
        count = expired_tokens.count()
        expired_tokens.delete()
        self.message_user(request, f'{count} expired tokens were deleted.')
    delete_expired_tokens.short_description = 'Delete expired tokens'


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """
    Admin for login attempts
    """
    list_display = (
        'email', 'ip_address', 'success', 'failure_reason',
        'timestamp', 'user_agent_short'
    )
    list_filter = ('success', 'failure_reason', 'timestamp')
    search_fields = ('email', 'ip_address')
    readonly_fields = ('email', 'ip_address', 'user_agent', 'success', 'failure_reason', 'timestamp')
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Login Info', {
            'fields': ('email', 'success', 'failure_reason')
        }),
        ('Client Info', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        })
    )
    
    actions = ['delete_old_attempts']
    
    def user_agent_short(self, obj):
        return f"{obj.user_agent[:50]}..." if len(obj.user_agent) > 50 else obj.user_agent
    user_agent_short.short_description = 'User Agent'
    
    def delete_old_attempts(self, request, queryset):
        """Delete login attempts older than 30 days"""
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=30)
        old_attempts = queryset.filter(timestamp__lt=cutoff_date)
        count = old_attempts.count()
        old_attempts.delete()
        self.message_user(request, f'{count} old login attempts were deleted.')
    delete_old_attempts.short_description = 'Delete old attempts (30+ days)'
    
    def has_add_permission(self, request):
        """Disable adding login attempts through admin"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable changing login attempts through admin"""
        return False