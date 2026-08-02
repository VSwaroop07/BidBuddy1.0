from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if not user.username and user.email:
            user.username = user.email
        return user

    def pre_social_login(self, request, sociallogin):
        # Auto-connect social account if a user with the same email already exists
        if sociallogin.is_existing:
            return
        
        email = sociallogin.account.extra_data.get('email') or (
            sociallogin.email_addresses[0].email if sociallogin.email_addresses else None
        )
        
        if not email:
            return

        try:
            user = User.objects.get(email__iexact=email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass
