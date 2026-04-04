from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend that allows login with either
    email or username. This is necessary because USERNAME_FIELD is 'email'
    but we also want students to log in with generated usernames.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        from .models import User
        
        if username is None or password is None:
            return None
        
        # Try to find user by email OR username
        try:
            user = User.objects.get(
                Q(email__iexact=username) | Q(username__iexact=username)
            )
        except User.DoesNotExist:
            # Run the default password hasher once to reduce timing
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # If somehow multiple matches, try email first
            user = User.objects.filter(email__iexact=username).first()
            if not user:
                user = User.objects.filter(username__iexact=username).first()
            if not user:
                return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
