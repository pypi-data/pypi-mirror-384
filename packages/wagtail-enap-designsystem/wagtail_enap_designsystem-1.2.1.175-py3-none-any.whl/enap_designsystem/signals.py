from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from wagtail.models import Page
from wagtail.signals import page_published, page_unpublished
from .services.chatbot_service import ChatbotService
from .models import PaginaIndexada
import logging

logger = logging.getLogger(__name__)

def verificar_e_indexar_inicial():
    """Verifica se precisa fazer indexação inicial"""
    try:
        total_paginas_site = Page.objects.live().count()
        total_indexadas = PaginaIndexada.objects.count()
        
        # Se não tem nada indexado OU tem menos de 50% indexado
        if total_indexadas == 0 or total_indexadas < (total_paginas_site * 0.5):
            print(f"🚀 Indexação automática necessária: {total_indexadas}/{total_paginas_site}")
            service = ChatbotService()
            service.indexar_todas_paginas()
            return True
        return False
    except Exception as e:
        print(f"❌ Erro na verificação inicial: {e}")
        return False

@receiver(page_published)
def indexar_pagina_publicada(sender, instance, **kwargs):
    """Indexa quando página é PUBLICADA no Wagtail"""
    try:
        service = ChatbotService()
        success = service.indexar_pagina_especifica(instance)
        if success:
            logger.info(f"🤖✅ Página '{instance.title}' indexada no chatbot")
    except Exception as e:
        logger.error(f"🤖❌ Erro ao indexar '{instance.title}': {e}")

@receiver(page_unpublished)
def remover_pagina_despublicada(sender, instance, **kwargs):
    """Remove do índice quando página é DESPUBLICADA"""
    try:
        deleted_count = PaginaIndexada.objects.filter(
            wagtail_page_id=instance.id
        ).delete()[0]
        if deleted_count > 0:
            logger.info(f"🤖🗑️ Página '{instance.title}' removida do chatbot")
    except Exception as e:
        logger.error(f"🤖❌ Erro ao remover '{instance.title}': {e}")