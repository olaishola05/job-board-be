from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Profile, RefreshToken

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user model
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = (
            'user', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'is_verified', 'is_active', 'created_at',
            'updated_at', 'last_login'
        )
        read_only_fields = (
            'id', 'email', 'username', 'role', 'is_verified', 'is_active',
            'created_at', 'updated_at', 'last_login'
        )
class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True, max_length=30)
    last_name = serializers.CharField(required=True, max_length=30)
    username = serializers.CharField(required=True, max_length=30)
    
    class Meta:
        model = User
        fields = (
            'email', 'password', 'password_confirm', 'first_name', 
            'last_name', 'phone_number', 'role', 'username'
        )
    
    def validate(self, attrs):
        """Validate password confirmation and role"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        
        valid_roles = ['user', 'employer']
        if attrs.get('role') not in valid_roles:
            attrs['role'] = 'user'
        
        return attrs
    
    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm', None)
        
        user = User.objects.create_user(**validated_data)
        user.generate_verification_token()
        
        return user
      
class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    remember_me = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        """Validate login credentials"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                raise serializers.ValidationError({
                    'email': 'No account found with this email address.'
                })
            
            if user.is_account_locked:
                raise serializers.ValidationError({
                    'non_field_errors': 'Account is temporarily locked due to too many failed login attempts. Please try again later.'
                })
            
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                try:
                    existing_user = User.objects.get(email__iexact=email)
                    existing_user.increment_failed_attempts()
                except User.DoesNotExist:
                    pass
                
                raise serializers.ValidationError({
                    'non_field_errors': 'Invalid email or password.'
                })
            
            if not user.is_active:
                raise serializers.ValidationError({
                    'non_field_errors': 'This account is not active. Please verify your email address.'
                })

            if not user.is_verified: # type: ignore
                raise serializers.ValidationError({
                    'non_field_errors': 'Please verify your email address before logging in.'
                })
            
            attrs['user'] = user
            return attrs
        
        raise serializers.ValidationError({
            'non_field_errors': 'Must include email and password.'
        })
        
class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Validate that user exists"""
        try:
            user = User.objects.get(email__iexact=value, is_active=True)
            return value
        except User.DoesNotExist:
            return value
          
class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation
    """
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        write_only=True
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        """Validate token and password confirmation"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Password fields didn't match."
            })
        token = attrs.get('token')
        try:
            user = User.objects.get(
                password_reset_token=token,
                is_active=True
            )
            if not user.is_token_valid('password_reset', token):
                raise serializers.ValidationError({
                    'token': 'Token is invalid or expired.'
                })
            attrs['user'] = user
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'token': 'Invalid token.'
            })
        
        return attrs

class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        write_only=True
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Password fields didn't match."
            })
        return attrs
      
class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification
    """
    token = serializers.CharField(required=True)
    
    def validate_token(self, value):
        """Validate verification token"""
        try:
            user = User.objects.get(verification_token=value)
            if not user.is_token_valid('verification', value):
                raise serializers.ValidationError('Token is invalid or expired.')
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid token.')


class ResendVerificationSerializer(serializers.Serializer):
    """
    Serializer for resending verification email
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Validate that user exists and is not already verified"""
        try:
            user = User.objects.get(email__iexact=value)
            if user.is_verified:
                raise serializers.ValidationError('Email is already verified.')
            return value
        except User.DoesNotExist:
            return value
          
class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)
    
    class Meta:
        model = Profile
        fields = (
            'user_email', 'user_name', 'user_role', 'bio', 'location',
            'website', 'linkedin_url', 'github_url', 'avatar', 'resume',
            'experience_years', 'salary_expectation', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')
    
    def validate_avatar(self, value):
        """Validate avatar file size and type"""
        if value:
            # Check file size (max 5MB)
            if int(value.size) > 5 * 1024 * 1024:
                raise serializers.ValidationError('Avatar file size cannot exceed 5MB.')
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError('Avatar must be a JPEG, PNG, or GIF image.')
        
        return value
    
    def validate_resume(self, value):
        """Validate resume file size and type"""
        if value:
            if int(value.size) > 10 * 1024 * 1024:
                raise serializers.ValidationError('Resume file size cannot exceed 10MB.')
            
            allowed_types = ['application/pdf', 'application/msword', 
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError('Resume must be a PDF or Word document.')
        
        return value
 
      
class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user details with profile
    """
    profile = ProfileSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = (
            'user', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'is_verified', 'is_active', 'created_at',
            'updated_at', 'last_login', 'profile'
        )
        read_only_fields = (
            'user', 'email', 'username', 'role', 'is_verified', 'is_active',
            'created_at', 'updated_at', 'last_login'
        )
        
class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user information
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number')
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        if value:
            import re
            phone_regex = re.compile(r'^\+?1?\d{9,15}$')
            if not phone_regex.match(value):
                raise serializers.ValidationError(
                    "Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
                )
        return value
      
class AccountActivationSerializer(serializers.Serializer):
    """
    Serializer for account activation/deactivation
    """
    is_active = serializers.BooleanField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True)
    
    
class TokenRefreshSerializer(serializers.Serializer):
    """
    Serializer for token refresh
    """
    refresh = serializers.CharField(required=True)
    
    def validate_refresh(self, value):
        """Validate refresh token"""
        
        try:
            token = RefreshToken.objects.get(token=value)
            if not token.is_valid:
                raise serializers.ValidationError('Token is invalid or expired.')
            return value
        except RefreshToken.DoesNotExist:
            raise serializers.ValidationError('Token not found.')