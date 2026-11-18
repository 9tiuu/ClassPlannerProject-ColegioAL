from django.forms import ValidationError
from django.views.generic.detail import DetailView 
from django.views.generic.edit import UpdateView 
from django.contrib.auth.mixins import LoginRequiredMixin

from classplanner.models import Usuario
from registration.form import ProfileForm, ChangePassowrdForm
from django.contrib.auth import login, authenticate

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, render
import re

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse

from django.contrib.auth import update_session_auth_hash
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


def loginView(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        usuario = authenticate(request, username=username, password=password)

        if usuario is not None:
            login(request, usuario)

            if usuario.passwd_changed:
                return redirect('home')

            return redirect('changepassword')
        
    return render(request, 'registration/login.html')

class CustomLoginView(LoginView):
    def get_success_url(self):
        
        if not self.request.user.passwd_changed:
            return reverse('changepasswordgenered')

        messages.success(self.request, 'loginsuccessful')
        return reverse('home')

# ----------------------------------- # CHANGE PASSWORD VIEW

password_token_generator = PasswordResetTokenGenerator()

def changePasswordGenered(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.user.passwd_changed:
        return redirect('home')

    token = password_token_generator.make_token(request.user)
    return redirect('changepassword', uid=request.user.pk, token=token)

# ----------------------------------- # DEFAULT CHANGE PASSWORD

def changePassword(request, uid, token):
    try:
        usuario = Usuario.objects.get(pk=uid)
        
    except Usuario.DoesNotExist:
        return redirect('login')

    if not password_token_generator.check_token(usuario, token):
        return redirect('login')

    if usuario.passwd_changed:
        return redirect('home')

    if request.method == 'POST':
        form = ChangePassowrdForm(usuario, request.POST)

        if form.is_valid():
            usuario.set_password(form.cleaned_data['password_nueva'])
            usuario.passwd_changed = True
            usuario.save()

            update_session_auth_hash(request, usuario)
            # messages.success(request, 'contraseñaactualizada')

            return redirect('home')
    else:
        form = ChangePassowrdForm(usuario)

    return render(request, 'registration/changepassword.html', { "form": form })

# ----------------------------------- # PROFILE UPDATE

def validar_rut(rut):
    rut = rut.replace(".", "").upper()
    match = re.match(r"^(\d{1,8})[-]([0-9Kk])$", rut)

    if not match:
        raise ValidationError("El RUT tiene un formato incorrecto")
    return True

class ProfileView(LoginRequiredMixin, DetailView):
    model = Usuario
    template_name = 'registration/profile.html'
    context_object_name = 'usuario'

    def get_object(self):
        return self.request.user

@method_decorator(login_required, name='dispatch')
class ProfileUpdateView(UpdateView):
    model = Usuario
    form_class = ProfileForm
    template_name = 'registration/profile_update.html'
    success_url = reverse_lazy('profile')
    context_object_name = 'profile'

    def get_object(self):
        return self.request.user

    def post(self, request, *args, **kwargs):
        if 'avatar_clear' in request.POST:
            usuario = self.get_object()

            if usuario.avatar:
                usuario.avatar.delete(save=False)
                usuario.avatar = None
                usuario.save(update_fields=['avatar'])

            messages.success(request,'¡Imagen de perfil eliminada!')
            return redirect(self.success_url)
        
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        nueva = form.cleaned_data.get('password_nueva')
        
        if nueva:
            form.instance.set_password(nueva)
        response = super().form_valid(form)

        if nueva:
            update_session_auth_hash(self.request, form.instance)

        messages.success(self.request, '¡Perfil de Usuario Actualizado!')
        return response