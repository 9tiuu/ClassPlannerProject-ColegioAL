from django.forms import ValidationError
from django.views.generic.detail import DetailView 
from django.views.generic.edit import UpdateView 
from django.contrib.auth.mixins import LoginRequiredMixin

from tickets.models import Usuario
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
        username = form.cleaned_data.get('username')
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚ\s]+$', username):
            form.add_error('username', 'El nombre de usuario solo puede contener letras y espacios.')
            return self.form_invalid(form)

        rut = form.cleaned_data.get('rut')
        try:
            validar_rut(rut)
        except ValidationError as e:
            form.add_error('rut', str(e))
            return self.form_invalid(form)

        name = form.cleaned_data.get('name')
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚ\s]+$', name):
            form.add_error('name', 'El nombre solo puede contener letras y espacios.')
            return self.form_invalid(form)
        
        last_name = form.cleaned_data.get('last_name')
        if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚ\s]+$', last_name):
            form.add_error('last_name', 'El apellido solo puede contener letras y espacios.')
            return self.form_invalid(form)

        # validar numero telefonico

        password_actual = self.request.POST.get('password_actual', '').strip()
        password_nueva = self.request.POST.get('password_nueva', '').strip()
        password_confirmacion = self.request.POST.get('password_confirmacion', '').strip()
        usuario = self.get_object()

        if not password_actual and not password_nueva and not password_confirmacion:
            pass

        else:
            if not usuario.check_password(password_actual):
                form.add_error(None, 'La contraseña actual es incorrecta.')
                return self.form_invalid(form)

            if not password_nueva:
                form.add_error(None, 'Debe ingresar una nueva contraseña.')
                return self.form_invalid(form)

            if password_nueva != password_confirmacion:
                form.add_error(None, 'Las nuevas contraseñas no coinciden.')
                return self.form_invalid(form)

            usuario.set_password(password_nueva)
            usuario.save()
            update_session_auth_hash(self.request, usuario)

        messages.success(self.request, '¡Perfil de Usuario Actualizado!')
        return super().form_valid(form)