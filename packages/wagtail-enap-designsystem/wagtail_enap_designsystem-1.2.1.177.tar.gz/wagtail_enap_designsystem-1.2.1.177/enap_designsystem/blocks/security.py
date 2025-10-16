import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_safe_characters(value):
    """
    Permite apenas letras, números, espaços e acentos
    Bloqueia caracteres especiais perigosos E comandos SQL
    """
    if not isinstance(value, str) or not value:
        return
    
    # 1. Verificar caracteres permitidos primeiro
    allowed_pattern = r'^[a-zA-Z0-9À-ÿ\s\.\-@]+$'
    
    if not re.match(allowed_pattern, value):
        raise ValidationError(
            _('Este campo só aceita letras, números, espaços e acentos.'),
            code='invalid_characters'
        )
    
    # 2. Verificar comandos SQL proibidos
    sql_commands = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE']
    
    # Converter para maiúsculo para comparação
    value_upper = value.upper()
    
    for command in sql_commands:
        # Verificar se o comando aparece como palavra completa
        if re.search(r'\b' + command + r'\b', value_upper):
            raise ValidationError(
                _('Este campo contém comandos não permitidos.'),
                code='sql_command_detected'
            )


def validate_email_field(value):
    """
    Para campos de email - permite @ e . mas também bloqueia comandos SQL
    """
    if not isinstance(value, str) or not value:
        return
    
    # 1. Verificar caracteres permitidos para email
    allowed_pattern = r'^[a-zA-Z0-9@\.\-_]+$'
    
    if not re.match(allowed_pattern, value):
        raise ValidationError(
            _('Email contém caracteres não permitidos.'),
            code='invalid_email_characters'
        )
    
    # 2. Verificar comandos SQL também em emails
    sql_commands = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE']
    value_upper = value.upper()
    
    for command in sql_commands:
        if re.search(r'\b' + command + r'\b', value_upper):
            raise ValidationError(
                _('Email contém comandos não permitidos.'),
                code='sql_command_in_email'
            )