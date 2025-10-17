# enap_designsystem/blocks/middleware.py

from django.http import HttpResponseBadRequest
from django.core.exceptions import ValidationError
from ..blocks.security import validate_safe_characters, validate_email_field
import logging

logger = logging.getLogger(__name__)

class CharacterFilterMiddleware:
    """
    Middleware que filtra caracteres perigosos - COM EXCEÇÕES PARA ADMIN
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar apenas requisições POST
        if request.method == 'POST':
            
            # EXCEÇÕES: Não validar estes campos/URLs
            if self.should_skip_validation(request):
                return self.get_response(request)
            
            # Verificar cada campo enviado
            for key, value in request.POST.items():
                if isinstance(value, str) and value.strip():
                    
                    # Pular campos administrativos/técnicos
                    if self.is_admin_field(key):
                        continue
                    
                    try:
                        # Para campos de email, usar validação específica
                        if 'email' in key.lower():
                            validate_email_field(value)
                        else:
                            # Para outros campos, validação geral
                            validate_safe_characters(value)
                            
                    except ValidationError as e:
                        # Log da tentativa suspeita
                        logger.warning(f"Caracteres suspeitos bloqueados no campo '{key}': {value[:50]}")
                        
                        # Retornar erro
                        return HttpResponseBadRequest(
                            f"Campo '{key}' contém caracteres não permitidos por motivos de segurança."
                        )
        
        # Continuar processamento normal
        return self.get_response(request)
    
    def should_skip_validation(self, request):
        """
        Determina se deve pular validação para esta requisição
        """
        # URLs que devem ser ignoradas
        skip_urls = [
            '/admin/',          # Painel admin Django
            '/cms/',            # Painel admin Wagtail (se usar esta URL)
            '/django-admin/',   # Admin alternativo
        ]
        
        # Verificar se a URL atual deve ser ignorada
        for skip_url in skip_urls:
            if request.path.startswith(skip_url):
                return True
        
        return False
    
    def is_admin_field(self, field_name):
        """
        Identifica campos administrativos que devem ser ignorados
        """
        # Prefixos de campos administrativos
        admin_prefixes = [
            'form_steps-',      # StreamField do formulário
            'csrfmiddlewaretoken',  # Token CSRF
            'action-',          # Ações do admin
            'select_',          # Seletores do admin
            '_selected_',       # Campos selecionados
            'logo_section-',    # Campos de logo
            'background_image_fundo-',  # Campos de imagem
            'thank_you_image_section-',  # Campos de agradecimento
        ]
        
        # Sufixos de campos administrativos
        admin_suffixes = [
            '-type',            # Tipo do bloco
            '-deleted',         # Campo deletado
            '-order',           # Ordem do campo
            '-id',              # ID do bloco
        ]
        
        # Verificar prefixos
        for prefix in admin_prefixes:
            if field_name.startswith(prefix):
                return True
        
        # Verificar sufixos
        for suffix in admin_suffixes:
            if field_name.endswith(suffix):
                return True
        
        # Campos específicos do Wagtail
        wagtail_fields = [
            'title',            # Título da página
            'slug',             # Slug da página
            'seo_title',        # SEO
            'search_description',  # Descrição
        ]
        
        if field_name in wagtail_fields:
            return True
        
        return False