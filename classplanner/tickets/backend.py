from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

USER = get_user_model()

class EmailOrRutValidation(ModelBackend):
    def authenticate(self, request, username = None, password = None, **kwargs):
        if not username or not password:
            return None

        try:
            user = USER.objects.get(email=username)
        except USER.DoesNotExist:
            try:
                user = USER.objects.get(rut=username)
            except USER.DoesNotExist:
                return None

        if user.check_password(password):
            return user
        
        return None