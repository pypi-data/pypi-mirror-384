# enap_designsystem/context_processors.py

from django.conf import settings
from .models import EnapNavbarSnippet


def global_template_context(request):
    return {
        'debug': settings.DEBUG
    }


def navbar_context(request):
    """
    Adiciona EnapNavbarSnippet a todos os templates
    """
    try:
        navbar = EnapNavbarSnippet.objects.first()
        return {'enap_navbar': navbar}
    except EnapNavbarSnippet.DoesNotExist:
        return {'enap_navbar': None}
    

def recaptcha_context(request):
    """Adiciona configurações do reCAPTCHA ao contexto global"""
    try:
        from django.conf import settings
        
        # Obter chaves do settings
        public_key = getattr(settings, 'RECAPTCHA_PUBLIC_KEY', '')
        private_key = getattr(settings, 'RECAPTCHA_PRIVATE_KEY', '')
        
        print(f"DEBUG reCAPTCHA Context - EXECUTANDO:")
        print(f"- Public Key: {public_key[:20]}..." if public_key else "- Public Key: VAZIA")
        print(f"- Private Key: {private_key[:20]}..." if private_key else "- Private Key: VAZIA")
        print(f"- Has Keys: {bool(public_key and private_key)}")
        
        return {
            'recaptcha_public_key': public_key,
            'has_recaptcha_keys': bool(public_key and private_key),
        }
    except Exception as e:
        print(f"ERRO no context processor: {e}")
        return {
            'recaptcha_public_key': '',
            'has_recaptcha_keys': False,
        }