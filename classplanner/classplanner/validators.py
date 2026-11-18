from django.contrib.auth.password_validation import MinimumLengthValidator as DjangoMinimumLengthValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class MinimumLengthValidator(DjangoMinimumLengthValidator):
    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                f"La contraseña es demasiado corta. Debe tener al menos {self.min_length} caracteres.",
                code="password_too_short",
                params={"min_length": self.min_length},
            )

    def get_help_text(self):
        return f"Tu contraseña debe tener al menos {self.min_length} caracteres."

class ConsecutiveSequenceValidator:
    # Rechaza contraseñas que contengan, en cualquier posición:
    # - Secuencias consecutivas ascendentes o descendentes (1234, 4321, abcd, dcba).
    # - Caracteres repetidos seguidos (1111, aaaa, !!!!).

    def __init__(self, max_sequence=4, max_repeat=4):
        self.max_sequence = max_sequence
        self.max_repeat = max_repeat

    def validate(self, password, user=None):
        pwd = password.lower()
        seq_len = 1
        seq_dir = 0
        rep_len = 1

        for prev, curr in zip(pwd, pwd[1:]):
            diff = ord(curr) - ord(prev)

            if diff == 0:
                rep_len += 1
            else:
                rep_len = 1

            if rep_len >= self.max_repeat:
                raise ValidationError(
                    _("La contraseña no puede contener caracteres repetidos como 1111 o aaaa."),
                    code="repeated_characters",
                )

            if diff in (1, -1) and prev.isalnum() and curr.isalnum():
                if diff == seq_dir:
                    seq_len += 1
                else:
                    seq_dir = diff
                    seq_len = 2
            else:
                seq_dir = 0
                seq_len = 1

            if seq_len >= self.max_sequence:
                raise ValidationError(
                    _("La contraseña no puede contener secuencias consecutivas como 1234 o abcd."),
                    code="consecutive_sequence",
                )

    def get_help_text(self):
        return _(
            "No debe contener secuencias de %(s)d o más caracteres consecutivos (1234, abcd) "
            "ni %(r)d o más caracteres repetidos (1111, aaaa)."
        ) % {"s": self.max_sequence, "r": self.max_repeat}