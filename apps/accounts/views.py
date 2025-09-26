from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken
from django.utils import timezone
from django.db import transaction
from .utils import get_req_ip, log_login_attempt, create_jwt_tokens
from .models import User, Profile, RefreshToken
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, TokenRefreshSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    PasswordChangeSerializer, EmailVerificationSerializer,
    ResendVerificationSerializer, ProfileSerializer, UserProfileSerializer,
    UserUpdateSerializer, AccountActivationSerializer
)
from .permissions import (
    IsOwnerOrReadOnly, IsAdminUser, IsVerifiedUser, IsActiveUser,
    IsAccountOwnerOrAdmin, CanViewUserProfile
)
from .tasks import send_verification_email, send_password_reset_email, send_welcome_email, send_password_change_confirmation
from rest_framework import serializers

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management
    """
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsAccountOwnerOrAdmin]
    http_method_names = ['get', 'put', 'patch', 'delete']
    
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == 'update' or self.action == 'partial_update':
            return UserUpdateSerializer
        return UserProfileSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action == 'create':
            permission_classes = [AllowAny]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated, CanViewUserProfile]
        else:
            permission_classes = [IsAuthenticated, IsAccountOwnerOrAdmin]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user

        if not user.is_authenticated:
          return User.objects.none()

        if user.role == "admin":
          return User.objects.all().select_related("profile")

        return User.objects.filter(id=user.user).select_related("profile") 

    
    def retrieve(self, request, *args, **kwargs):
        """Get user profile"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def activate(self, request, pk=None):
        """Activate user account (admin only)"""
        user = self.get_object()
        serializer = AccountActivationSerializer(data=request.data)
        
        if serializer.is_valid():
            is_active = serializer.validated_data['is_active']
            reason = serializer.validated_data.get('reason', '')
            
            if is_active:
                user.activate_account()
                message = 'Account activated successfully'
            else:
                user.deactivate_account()
                message = 'Account deactivated successfully'
            
            return Response({
                'message': message,
                'is_active': user.is_active,
                'reason': reason
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        """Get user statistics (admin only)"""
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        verified_users = User.objects.filter(is_verified=True).count()
        users = User.objects.filter(role='user').count()
        employers = User.objects.filter(role='employer').count()
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'verified_users': verified_users,
            'users': users,
            'employers': employers,
            'unverified_users': total_users - verified_users
        })
        
class UserRegistrationViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for registering new users
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
              if not User.objects.filter(email__iexact=serializer.validated_data['email']).exists():
                user = serializer.save()
                with transaction.atomic():
                    user.generate_verification_token()
                    send_verification_email.delay(user.user)
                    return Response(
                        {
                            "message": "Registration successful. Please check your email for instructions.",
                            "user_id": str(user.user),
                            "email": user.email,
                        },
                        status=status.HTTP_201_CREATED,
                    )
                    
            except serializers.ValidationError as ve:
                return Response({
                "message": "Validation failed.",
                "errors": ve.detail
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(e)
                return Response({"error": f"Registration failed with {e}. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for handling user login
    """
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            remember_me = serializer.validated_data.get("remember_me", False)

            try:
                user.reset_failed_attempts()
                user.last_login_ip = get_req_ip(request)
                user.save(update_fields=["last_login_ip"])

                tokens = create_jwt_tokens(user, request)

                if remember_me:
                    refresh_token = RefreshToken.objects.get(token=tokens["refresh"])
                    refresh_token.expires_at = timezone.now() + timezone.timedelta(days=30)
                    refresh_token.save()
                    tokens["refresh_token_expiry"] = refresh_token.expires_at

                log_login_attempt(user.email, request, success=True)
                return Response(
                    {
                        "message": "Login successful",
                        "tokens": tokens,
                        "user": {
                            "id": str(user.user),
                            "email": user.email,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "role": user.role,
                            "is_verified": user.is_verified,
                            "is_active": user.is_active,
                        },
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as exp:
                return Response({"error": f"Login failed with err {exp}. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if "email" in request.data:
            log_login_attempt(request.data["email"], request, success=False, failure_reason="Invalid credentials")

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
      
class PasswordResetViewSet(viewsets.GenericViewSet):
    """
    A ViewSet for handling password reset requests and confirmations
    """
    permission_classes = [AllowAny]
    serializer_classes = {
        'request_reset': PasswordResetRequestSerializer,
        'confirm_reset': PasswordResetConfirmSerializer,
    }
    http_method_names = ['post']
    
    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, None)
        
    @action(detail=False, methods=['post'], url_path='request')
    def request_reset(self, request):
      """Request password reset"""
      serializer = self.get_serializer(data=request.data)
      
      if serializer.is_valid():
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email__iexact=email, is_active=True)
            user.generate_password_reset_token()
            send_password_reset_email.delay(user.user)
            print(user.password_reset_token)
            return Response(
                {"message": "Password reset instructions sent"},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"error": "No active user found with this email"},
                status=status.HTTP_400_BAD_REQUEST
            )

      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['post'], url_path='confirm')
    def confirm_reset(self, request):
        """Confirm password reset"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            new_password = serializer.validated_data['new_password']
            try:
                user.set_password(new_password)
                user.last_password_change = timezone.now()
                user.clear_token('password_reset')
                RefreshToken.objects.filter(user=user).update(is_revoked=True)
                user.save()
                return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
            except Exception:
                return Response({"error": "Password reset failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TokenRefreshViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for refreshing JWT access tokens
    """
    serializer_class = TokenRefreshSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            refresh_token_value = serializer.validated_data['refresh']
            try:
                refresh_token = RefreshToken.objects.get(token=refresh_token_value)
                if not refresh_token.is_valid:
                    return Response({"error": "Token is invalid or expired"}, status=status.HTTP_401_UNAUTHORIZED)

                jwt_refresh = JWTRefreshToken.for_user(refresh_token.user)
                return Response(
                    {
                        "access": str(jwt_refresh.access_token),
                        "access_token_expiry": timezone.now() + timezone.timedelta(minutes=15),
                    },
                    status=status.HTTP_200_OK,
                )
            except RefreshToken.DoesNotExist:
                return Response({"error": "Token not found"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordChangeViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for changing user passwords
    """
    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            user = request.user
            new_password = serializer.validated_data['new_password']
            try:
                user.set_password(new_password)
                user.last_password_change = timezone.now()
                user.save()
                RefreshToken.objects.filter(user=user).update(is_revoked=True)
                send_password_change_confirmation.delay(user_id=user.user)
                return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)
            except Exception:
                return Response({"error": "Password change failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EmailVerificationViewSet(viewsets.ViewSet):
    """
    A ViewSet for verifying user email addresses
    """
    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        token = request.query_params.get('token') or request.data.get('token')
        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)
        if len(token) < 20:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)  
        try:
            user = User.objects.get(verification_token=token)
            if user.is_token_valid('verification', token):
                user.verify_email()

                send_welcome_email.delay(user.user) # type: ignore
                return Response({"message": "Email verified successfully"}, status=status.HTTP_200_OK)
            return Response({"error": "Verification token expired"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

class LogoutViewSet(viewsets.ViewSet):
    """
    A ViewSet for handling user logout
    """
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                RefreshToken.objects.filter(token=refresh_token, user=request.user).update(is_revoked=True)

            if request.data.get('logout_all', False):
                RefreshToken.objects.filter(user=request.user, is_revoked=False).update(is_revoked=True)

            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Logout failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResendVerificationViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for resending email verification links
    """
    serializer_class = ResendVerificationSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email__iexact=email, is_active=True, is_verified=False)
                user.generate_verification_token()
                send_verification_email.delay(user.user)
                return Response({"message": "Verification email resent"}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "No unverified account found with this email"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user profile management
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, CanViewUserProfile]
    http_method_names = ['get', 'put', 'patch']
  
    def get_queryset(self): # type: ignore
        """Filter queryset to user's own profile"""
        if self.request.user.is_authenticated:
            return Profile.objects.filter(user=self.request.user)
        return Profile.objects.none()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get or update current user's profile"""
        try:
            print(request.user)
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=request.user)
        
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
            