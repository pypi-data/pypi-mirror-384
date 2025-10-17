from django.db import models
from wagtail.admin.panels import FieldPanel
from django.utils.translation import gettext_lazy as _
from wagtail.fields import StreamField, RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import RichTextBlock
from wagtail import blocks
from wagtail.admin.panels import PageChooserPanel
from wagtail.models import Page
from .blocks.semana_inovacao import *
from .blocks.semana_blocks import *
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.images.blocks import ImageChooserBlock
from wagtail.fields import StreamField
from coderedcms.models import CoderedWebPage
from modelcluster.models import ClusterableModel
from wagtail.blocks import URLBlock
from wagtail.search import index
import requests
import os
from .blocks.html_blocks import RecaptchaBlock, EnapCardInfo
from django.db.models.signals import pre_delete
from django.dispatch import receiver
import shutil
import os
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from wagtail.snippets.models import register_snippet
from django.utils.html import strip_tags
import re
from wagtail.admin.panels import FieldPanel
from enap_designsystem.blocks import TextoImagemBlock
from django.shortcuts import redirect, render
from django.conf import settings
from datetime import datetime
from .utils.sso import get_valid_access_token
from wagtail.blocks import PageChooserBlock, StructBlock, CharBlock, BooleanBlock, ListBlock, IntegerBlock
from django.conf import settings
from django.utils import timezone
from .blocks.layout_blocks import EnapAccordionBlock

from wagtail.blocks import StreamBlock, StructBlock, CharBlock, ChoiceBlock, RichTextBlock, ChooserBlock, ListBlock

import uuid
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from wagtail.models import Page
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet

from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import MultiFieldPanel, FieldPanel, InlinePanel
from wagtail.documents.models import Document
from wagtail.fields import StreamField
from .blocks import ButtonBlock
from .blocks import ImageBlock
from modelcluster.fields import ParentalKey
from wagtail.models import Orderable

from wagtail.images.models import Image
from django.dispatch import receiver
from wagtail.images import get_image_model_string
from enap_designsystem.blocks import EnapFooterGridBlock
from enap_designsystem.blocks import EnapFooterSocialGridBlock 
from enap_designsystem.blocks import EnapAccordionPanelBlock
from enap_designsystem.blocks import EnapNavbarLinkBlock
from enap_designsystem.blocks import EnapCardBlock

from enap_designsystem.blocks import EnapCardGridBlock
from enap_designsystem.blocks import EnapSectionBlock
from .blocks import ClientesBlock 

from django.http import Http404
from django.shortcuts import render
from wagtail.models import Page

from enap_designsystem.blocks import PageListBlock
from enap_designsystem.blocks import NewsCarouselBlock
from enap_designsystem.blocks import DropdownBlock
from enap_designsystem.blocks import CoursesCarouselBlock
from enap_designsystem.blocks import SuapCourseBlock
from enap_designsystem.blocks import HolofoteCarouselBlock
from enap_designsystem.blocks import SuapEventsBlock
from enap_designsystem.blocks import PreviewCoursesBlock
from enap_designsystem.blocks import EventsCarouselBlock
from enap_designsystem.blocks import EnapBannerBlock
from enap_designsystem.blocks import FeatureImageTextBlock
from enap_designsystem.blocks import EnapAccordionBlock
from enap_designsystem.blocks.base_blocks import ButtonGroupBlock
from enap_designsystem.blocks.content_blocks import CardBlock
from enap_designsystem.blocks.base_blocks import CarouselBlock
from enap_designsystem.blocks import CourseIntroTopicsBlock
from .blocks import WhyChooseEnaptBlock
from .blocks import CourseFeatureBlock
from .blocks import CourseModulesBlock
from .blocks import ProcessoSeletivoBlock
from .blocks import TeamCarouselBlock  
from .blocks import TestimonialsCarouselBlock
from .blocks import CarouselGreen
from .blocks import TeamModern
from .blocks import HeroBlockv3
from .blocks import TopicLinksBlock
from .blocks import AvisoBlock
from .blocks import FeatureListBlock
from .blocks import ServiceCardsBlock
from .blocks import CitizenServerBlock
from .blocks import CarrosselCursosBlock
from .blocks import Banner_Image_cta
from .blocks import FeatureWithLinksBlock
from .blocks import QuoteBlockModern
from .blocks import CardCursoBlock
from .blocks import HeroAnimadaBlock
from .blocks import EventoBlock
from .blocks import ContainerInfo
from .blocks import CtaDestaqueBlock
from .blocks import SecaoAdesaoBlock
from .blocks import SectionTabsCardsBlock
from .blocks import GalleryModernBlock
from .blocks import ContatoBlock
from .blocks import FormContato
from .blocks import DownloadBlock
from .blocks import SectionCardTitleCenterBlock
from .blocks import CTA2Block
from .blocks import AccordionItemBlock
from .blocks.html_blocks import HeroMenuItemBlock 
from .blocks.form import FormularioPage
from .blocks.html_blocks import TemaFAQBlock

from wagtail.snippets.blocks import SnippetChooserBlock

from enap_designsystem.blocks import LAYOUT_STREAMBLOCKS
from enap_designsystem.blocks import DYNAMIC_CARD_STREAMBLOCKS
from enap_designsystem.blocks import CARD_CARDS_STREAMBLOCKS

# class ComponentLayout(models.Model):
#     name = models.CharField(max_length=255)
#     content = models.TextField()

#     panels = [
#         FieldPanel("name"),
#         FieldPanel("content"),
#     ]

#     class Meta:
#         abstract = True



class ENAPComponentes(Page):
	"""Página personalizada independente do CoderedWebPage."""
	
	admin_notes = models.TextField(
		verbose_name="Anotações Internas",
		blank=True,
		help_text="Escreva observações importantes. Este campo é visível apenas para administradores."
	)

	template = "enap_designsystem/pages/enap_layout.html"

	body = StreamField(
		LAYOUT_STREAMBLOCKS,
		null=True,
		blank=True,
		use_json_field=True,
	)
	

	navbar = models.ForeignKey(
		"EnapNavbarSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	footer = models.ForeignKey(
		"EnapFooterSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	content_panels = Page.content_panels + [
		FieldPanel("navbar"),
		FieldPanel("body"),
		FieldPanel("footer"),
		FieldPanel("admin_notes"),
	]

	@property
	def url_filter(self):
		if hasattr(self, 'full_url') and self.full_url:
			return self.full_url
		return self.get_url_parts()[2] if self.get_url_parts() else ""
	
	@property
	def titulo_filter(self):
		for block in self.body:
			if block.block_type == "enap_herobanner":
				return block.value.get("title", "")
		return ""

	@property
	def descricao_filter(self):
		for block in self.body:
			if block.block_type == "enap_herobanner":
				desc = block.value.get("description", "")
				if hasattr(desc, "source"):
					return strip_tags(desc.source).strip()
				return strip_tags(str(desc)).strip()
		return ""

	@property
	def data_atualizacao_filter(self):
		return self.last_published_at or self.latest_revision_created_at

	@property
	def categoria(self):
		return "Especialização"
	
	@property
	def imagem_filter(self):
		tipos_com_imagem = [
			("enap_herobanner", "background_image"),
			("bannertopics", "imagem_fundo"),
			("banner_image_cta", "hero_image"),
			("hero", "background_image"),
			("banner_search", "imagem_principal"),
		]

		try:
			for bloco in self.body:
				for tipo, campo_imagem in tipos_com_imagem:
					if bloco.block_type == tipo:
						imagem = bloco.value.get(campo_imagem)
						if imagem:
							return imagem.file.url
		except Exception:
			pass

		return ""
	
	@property
	def texto_unificado(self):
		def extract_text_from_block(block_value):
			result = []

			if isinstance(block_value, list):
				for subblock in block_value:
					result.extend(extract_text_from_block(subblock))
			elif hasattr(block_value, "get"):  # StructValue
				for key, val in block_value.items():
					result.extend(extract_text_from_block(val))
			elif isinstance(block_value, str):
				cleaned = strip_tags(block_value).strip()
				if cleaned and cleaned.lower() not in {
					"default", "tipo terciário", "tipo secundário", "tipo bg image",
					"bg-gray", "bg-blue", "bg-white", "fundo cinza", "fundo branco"
				}:
					result.append(cleaned)
			elif hasattr(block_value, "source"):  # RichText
				cleaned = strip_tags(block_value.source).strip()
				if cleaned:
					result.append(cleaned)

			return result

		textos = []
		if hasattr(self, "body") and self.body:
			for block in self.body:
				textos.extend(extract_text_from_block(block.value))

		# Junta tudo em uma string e remove quebras de linha duplicadas
		texto_final = " ".join([t for t in textos if t])
		texto_final = re.sub(r"\s+", " ", texto_final).strip()  # Remove espaços e quebras em excesso
		return texto_final

	search_fields = Page.search_fields + [
		index.SearchField("title", boost=3),
		index.SearchField("titulo_filter", name="titulo"),
		index.SearchField("descricao_filter", name="descricao"),
		index.FilterField("categoria", name="categoria_filter"),
		index.SearchField("url_filter", name="url"),
		index.SearchField("data_atualizacao_filter", name="data_atualizacao"),
		index.SearchField("imagem_filter", name="imagem"),
		index.SearchField("texto_unificado", name="body"),
	]


	class Meta:
		verbose_name = "ENAP Componentes"
		verbose_name_plural = "ENAP Componentes"





class ENAPSemana(Page):
	"""Página personalizada independente do CoderedWebPage."""
	
	admin_notes = models.TextField(
		verbose_name="Anotações Internas",
		blank=True,
		help_text="Escreva observações importantes. Este campo é visível apenas para administradores."
	)

	template = "enap_designsystem/pages/enap_layout_semana.html"

	body = StreamField(
		SEMANA_INOVACAO_STREAMBLOCKS,
		null=True,
		blank=True,
		use_json_field=True,
	)
	

	navbar = models.ForeignKey(
		"EnapNavbarSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	footer = models.ForeignKey(
		"EnapFooterSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	content_panels = Page.content_panels + [
		FieldPanel("navbar"),
		FieldPanel("body"),
		FieldPanel("footer"),
		FieldPanel("admin_notes"),
	]

	class Meta:
		verbose_name = "ENAP Semana"
		verbose_name_plural = "ENAP Semana"




class ENAPFormacao(CoderedWebPage):
	"""Página personalizada herdando todas as características de CoderedWebPage."""

	admin_notes = models.TextField(
		verbose_name="Anotações Internas",
		blank=True,
		help_text="Escreva observações importantes."
	)

	template = "enap_designsystem/pages/template_cursos.html"
	miniview_template = "coderedcms/pages/article_page.mini.html"
	search_template = "coderedcms/pages/article_page.search.html"

	content = StreamField(
		[("banner", EnapBannerBlock())],
		null=True,
		blank=True,
		use_json_field=True,
	)

	feature = StreamField(
		[("enap_herofeature", FeatureImageTextBlock())],
		null=True,
		blank=True,
		use_json_field=True,
	)

	accordion_cursos = StreamField(
		[
			("enap_accordion", EnapAccordionBlock()),
			("button_group", ButtonGroupBlock()),
			("carousel", CarouselBlock()),
			("dropdown", DropdownBlock()),
		],
		null=True,
		blank=True,
		use_json_field=True,
	)

	body = StreamField(
		CARD_CARDS_STREAMBLOCKS,
		null=True,
		blank=True,
		use_json_field=True,
	)

	modal = models.ForeignKey("enap_designsystem.Modal", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
	navbar = models.ForeignKey("EnapNavbarSnippet", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
	footer = models.ForeignKey("EnapFooterSnippet", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
	modalenap = models.ForeignKey("enap_designsystem.ModalBlock", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
	alert = models.ForeignKey("Alert", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
	wizard = models.ForeignKey("Wizard", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
	FormularioContato = models.ForeignKey("FormularioContato", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
	tab = models.ForeignKey("Tab", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

	@property
	def titulo_filter(self):
		return strip_tags(self.title or "").strip()

	@property
	def descricao_filter(self):
		return strip_tags(self.admin_notes or "").strip()

	@property
	def categoria(self):
		return "Cursos"

	@property
	def data_atualizacao_filter(self):
		return self.last_published_at or self.latest_revision_created_at or self.first_published_at

	@property
	def url_filter(self):
		if hasattr(self, 'full_url') and self.full_url:
			return self.full_url
		return self.get_url_parts()[2] if self.get_url_parts() else ""

	@property
	def imagem_filter(self):
		try:
			for bloco in self.content:
				if bloco.block_type == "banner":
					background = bloco.value.get("background_image")
					if background:
						return background.file.url
		except Exception:
			pass
		return ""
	
	@property
	def texto_unificado(self):
		def extract_text_from_block(block_value):
			result = []
			if isinstance(block_value, list):
				for subblock in block_value:
					result.extend(extract_text_from_block(subblock))
			elif hasattr(block_value, "get"):
				for _, val in block_value.items():
					result.extend(extract_text_from_block(val))
			elif isinstance(block_value, str):
				cleaned = strip_tags(block_value).strip()
				if cleaned and cleaned.lower() not in {
					"default", "tipo terciário", "tipo secundário", "tipo bg image",
					"bg-gray", "bg-blue", "bg-white", "fundo cinza", "fundo branco"
				}:
					result.append(cleaned)
			elif hasattr(block_value, "source"):
				cleaned = strip_tags(block_value.source).strip()
				if cleaned:
					result.append(cleaned)
			return result

		textos = []
		for sf in [self.content, self.feature, self.accordion_cursos, self.body]:
			if sf:
				for block in sf:
					textos.extend(extract_text_from_block(block.value))

		if self.admin_notes:
			textos.append(strip_tags(self.admin_notes).strip())

		return re.sub(r"\s+", " ", " ".join([t for t in textos if t])).strip()

	search_fields = CoderedWebPage.search_fields + [
		index.SearchField("title", boost=3),
		index.SearchField("titulo_filter", name="titulo"),
		index.SearchField("descricao_filter", name="descricao"),
		index.FilterField("categoria", name="categoria_filter"),
		index.SearchField("url_filter", name="url"),
		index.SearchField("data_atualizacao_filter", name="data_atualizacao"),
		index.SearchField("imagem_filter", name="imagem"),
		index.SearchField("texto_unificado", name="body"),
	]

	content_panels = CoderedWebPage.content_panels + [
		FieldPanel('navbar'),
		FieldPanel('modal'),
		FieldPanel('modalenap'),
		FieldPanel('wizard'),
		FieldPanel('alert'),
		FieldPanel('FormularioContato'),
		FieldPanel('tab'),
		FieldPanel('footer'),
		FieldPanel('content'),
		FieldPanel('feature'),
		FieldPanel('accordion_cursos'),
	]
	
	class Meta:
		verbose_name = "Template ENAP Curso"
		verbose_name_plural = "Template ENAP Cursos"


class ENAPTemplatev1(CoderedWebPage):
	"""Página personalizada herdando todas as características de CoderedWebPage."""
	
	admin_notes = models.TextField(
		verbose_name="Anotações Internas",
		blank=True,
		help_text="Escreva observações importantes."
	)

	template = "enap_designsystem/pages/template_homeI.html"
	miniview_template = "coderedcms/pages/article_page.mini.html"
	search_template = "coderedcms/pages/article_page.search.html"

	page_destaque = RichTextField(
		max_length=255, 
		default="Título Padrão", 
		verbose_name="Título da Página"
	)

	hero_menu_items = StreamField(
        [("menu_item", HeroMenuItemBlock())],
        null=True,
        blank=True,
        use_json_field=True,
        verbose_name="Itens do Menu Hero",
        help_text="Adicione quantos itens de menu quiser. Cada item terá um dropdown com as páginas filhas.",
		default=list
    )

	body_stream = StreamField(
		LAYOUT_STREAMBLOCKS,
		null=True,
		blank=True,
		use_json_field=True,
	)

	body = StreamField(
		DYNAMIC_CARD_STREAMBLOCKS,
		null=True,
		blank=True,
		use_json_field=True,
	)

	suap_courses = StreamField(
		[("suap_courses", SuapCourseBlock())],
		null=True,
		blank=True,
		use_json_field=True,
	)

	suap_events = StreamField(
		[("suap_events", SuapEventsBlock())],
		null=True,
		blank=True,
		use_json_field=True,
	)

	noticias = StreamField(
		[("eventos_carousel", EventsCarouselBlock())], 
		null=True,
		blank=True,
		use_json_field=True,
	)

	teste_noticia = StreamField(
		[("noticias_carousel", NewsCarouselBlock())], 
		null=True,
		blank=True,
		use_json_field=True,
	)

	teste_preview = StreamField(
		[("page_preview_teste", HolofoteCarouselBlock())],
		null=True,
		blank=True,
		use_json_field=True,
	)
	
	paragrafo = RichTextField(
		blank=True, 
		help_text="Adicione o texto do parágrafo aqui.", 
		verbose_name="Parágrafo sessao dinamica"
	)
	
	video_background = models.FileField(
		upload_to='media/videos', 
		null=True, 
		blank=True, 
		verbose_name="Vídeo de Fundo"
	)

	background_image = StreamField(
		[
			("image", ImageBlock()),
		],
		null=True,
		blank=True,
		use_json_field=True,
	)

	linkcta = RichTextField(blank=True)
	button_link = models.URLField(
		"Link do Botão",
		blank=True,
		help_text="URL do link do botão"
	)

	parceiros = StreamField([
        ("clientes", ClientesBlock()),
    ], blank=True, help_text="Adicione componentes à sua página", use_json_field=True)
    

	navbar = models.ForeignKey(
		"EnapNavbarSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	footer = models.ForeignKey(
		"EnapFooterSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	# Painéis no admin do Wagtail
	content_panels = CoderedWebPage.content_panels + [
		FieldPanel('navbar'),
		FieldPanel('video_background'),
		FieldPanel('hero_menu_items'),
		MultiFieldPanel(
			[
				FieldPanel('page_destaque'),
				FieldPanel('paragrafo'),
				FieldPanel('background_image'),
				FieldPanel('button_link'),
			],
			heading="Título e Parágrafo CTA Dinamico"
		),
		FieldPanel('suap_courses'),
		FieldPanel('suap_events'),
		FieldPanel('body_stream'),
		FieldPanel('noticias'),
		FieldPanel('teste_preview'),
		FieldPanel('teste_noticia'),
		FieldPanel('parceiros'),  
		FieldPanel('footer'),
	]

	@property
	def url_filter(self):
		if hasattr(self, 'full_url') and self.full_url:
			return self.full_url
		return self.get_url_parts()[2] if self.get_url_parts() else ""

	search_fields = []

	def get_searchable_content(self):
		content = super().get_searchable_content()

		if self.page_title:
			content.append(self.page_title)
		if self.paragrafo:
			content.append(self.paragrafo)
		if self.linkcta:
			content.append(self.linkcta)

		def extract_text_from_block(block_value):
			result = []

			if isinstance(block_value, list):  # lista de blocos (ex: StreamBlock)
				for subblock in block_value:
					result.extend(extract_text_from_block(subblock))
			elif hasattr(block_value, "get"):  # tipo StructValue
				for key, val in block_value.items():
					result.extend(extract_text_from_block(val))
			elif isinstance(block_value, str):
				result.append(block_value)
			elif hasattr(block_value, "source"):  # RichText
				result.append(block_value.source)

			return result

		# StreamFields a indexar
		streamfields = [
			self.body,
			self.teste_courses,
			self.suap_courses,
			self.noticias,
			self.teste_noticia,
			self.teste_preview,
			self.dropdown_content,
		]

		for sf in streamfields:
			if sf:
				for block in sf:
					content.extend(extract_text_from_block(block.value))

		return content

	
	
	class Meta:
		verbose_name = "Enap home v1"
		verbose_name_plural = "Enap Home v1"


class ENAPTeste(CoderedWebPage):
	"""Página personalizada herdando todas as características de CoderedWebPage."""
	
	admin_notes = models.TextField(
		verbose_name="Anotações Internas",
		blank=True,
		help_text="Escreva observações importantes."
	)

	template = "enap_designsystem/pages/template_homeII.html"
	miniview_template = "coderedcms/pages/article_page.mini.html"
	search_template = "coderedcms/pages/article_page.search.html"

	page_title = models.CharField(
		max_length=255, 
		default="Título Padrão", 
		verbose_name="Título da Página"
	)


	body = StreamField(
		DYNAMIC_CARD_STREAMBLOCKS,
		null=True,
		blank=True,
		use_json_field=True,
	)


	teste_courses = StreamField(
		[("courses_carousel", CoursesCarouselBlock())], 
		null=True,
		blank=True,
		use_json_field=True,
	)

	suap_courses = StreamField(
		[("suap_courses", SuapCourseBlock())],
		null=True,
		blank=True,
		use_json_field=True,
	)

	noticias = StreamField(
		[("eventos_carousel", EventsCarouselBlock())], 
		null=True,
		blank=True,
		use_json_field=True,
	)

	teste_noticia = StreamField(
		[("noticias_carousel", NewsCarouselBlock())], 
		null=True,
		blank=True,
		use_json_field=True,
	)

	teste_preview = StreamField(
		[("page_preview_teste", HolofoteCarouselBlock())],
		null=True,
		blank=True,
		use_json_field=True,
	)

	dropdown_content = StreamField(
		[("dropdown", DropdownBlock())],
		null=True,
		blank=True,
		use_json_field=True,
	)
	
	paragrafo = RichTextField(
		blank=True, 
		help_text="Adicione o texto do parágrafo aqui.", 
		verbose_name="Parágrafo sessao dinamica"
	)
	
	video_background = models.FileField(
		upload_to='media/videos', 
		null=True, 
		blank=True, 
		verbose_name="Vídeo de Fundo"
	)

	background_image = StreamField(
		[
			("image", ImageBlock()),
		],
		null=True,
		blank=True,
		use_json_field=True,
	)

	linkcta = RichTextField(blank=True)
	button_link = models.URLField(
		"Link do Botão",
		blank=True,
		help_text="URL do link do botão"
	)
	

	navbar = models.ForeignKey(
		"EnapNavbarSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	footer = models.ForeignKey(
		"EnapFooterSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	# Painéis no admin do Wagtail
	content_panels = CoderedWebPage.content_panels + [
		FieldPanel('navbar'),
		FieldPanel('video_background'),
		MultiFieldPanel(
			[
				FieldPanel('page_title'),
				FieldPanel('paragrafo'),
				FieldPanel('background_image'),
				FieldPanel('button_link'),
			],
			heading="Título e Parágrafo CTA Dinamico"
		),
		FieldPanel('teste_courses'),
		FieldPanel('suap_courses'),
		FieldPanel('noticias'),
		FieldPanel('dropdown_content'),
		FieldPanel('teste_preview'),
		FieldPanel('teste_noticia'),  
		FieldPanel('footer'),
	]

	search_fields = []

	class Meta:
		verbose_name = "Enap Home v2"
		verbose_name_plural = "Home V2"





@register_snippet
class EnapFooterSnippet(ClusterableModel):
	"""
	Custom footer for bottom of pages on the site.
	"""

	class Meta:
		verbose_name = "ENAP Footer"
		verbose_name_plural = "ENAP Footers"

	image = StreamField([
		("logo", ImageChooserBlock()),
	], blank=True, use_json_field=True)

	name = models.CharField(
		max_length=255,
		blank=False,
		null=False,
		help_text="Título do snippet"
	)

	links = StreamField([
		("enap_footergrid", EnapFooterGridBlock()),
	], blank=True, use_json_field=True)

	social = StreamField([
		("enap_footersocialgrid", EnapFooterSocialGridBlock()),
	], blank=True, use_json_field=True)

	panels = [
		FieldPanel("name"),
		FieldPanel("image"),
		FieldPanel("social"),
		FieldPanel("links"),
	]

	def __str__(self) -> str:
		return self.name
	

@register_snippet
class EnapAccordionSnippet(ClusterableModel):
	"""
	Snippet de Accordion estilo FAQ.
	"""
	class Meta:
		verbose_name = "ENAP Accordion"
		verbose_name_plural = "ENAP Accordions"

	name = models.CharField(
		max_length=255,
		blank=False,
		null=False,
		help_text="Nome do snippet para facilitar a identificação no admin."
	)

	panels_content = StreamField([
		("accordion_item", EnapAccordionPanelBlock()),
	], blank=True, use_json_field=True)

	panels = [
		FieldPanel("name"),
		FieldPanel("panels_content"),
	]

	def __str__(self):
		return self.name
	





class EnapNavbarChooserPageBlock(blocks.StructBlock):
    """
    ChooserPage dropdown que mostra páginas mãe à esquerda e filhas à direita.
    """
    
    title = blocks.CharBlock(
        max_length=255,
        required=True,
        label="Título do Menu",
        default="Menu Principal",
        help_text="Título que aparece no botão do menu"
    )
    
    parent_pages = blocks.ListBlock(
        blocks.StructBlock([
            ('page', PageChooserBlock(
                required=True,
                help_text="Página mãe (as páginas filhas serão mostradas automaticamente)"
            )),
            ('custom_title', blocks.CharBlock(
                required=False,
                max_length=100,
                help_text="Título customizado (opcional, senão usa o título da página)"
            )),
            ('icon', blocks.CharBlock(
                required=False,
                max_length=50,
                help_text="Ícone Material Icons (opcional) - ex: school, event, book, business"
            )),
        ]),
        required=True,
        min_num=1,
        max_num=8,
        label="Páginas Mãe",
        help_text="Adicione as páginas mãe que aparecerão no menu lateral"
    )
    
    max_child_pages = blocks.IntegerBlock(
        required=False,
        default=10,
        min_value=1,
        max_value=20,
        help_text="Número máximo de páginas filhas a mostrar"
    )
    
    show_child_descriptions = blocks.BooleanBlock(
        required=False,
        default=False,
        help_text="Mostrar descrições das páginas filhas (se disponível)"
    )
    
    class Meta:
        icon = "folder-open-inverse"
        label = "ChooserPage"

    
@register_snippet
class EnapNavbarSnippet(ClusterableModel):
	"""
	Snippet para a Navbar do ENAP, permitindo logo, busca, idioma e botão de contraste.
	"""

	name = models.CharField(
		max_length=255,
		blank=False,
		null=False,
		help_text="Nome do snippet para facilitar a identificação no admin."
	)

	logo = StreamField([
		("image", ImageChooserBlock())
	], blank=True, use_json_field=True, verbose_name="Logo da Navbar")

	links = StreamField([
		("navbar_link", EnapNavbarLinkBlock()),
		("chooserpage", EnapNavbarChooserPageBlock()),
	], blank=True, use_json_field=True)

	logo_link_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Página para onde a logo deve direcionar (deixe em branco para usar a página inicial)",
        verbose_name="Link da Logo"
    )

	panels = [
		FieldPanel("name"),
		PageChooserPanel("logo_link_page"),
		FieldPanel("logo"),
		FieldPanel("links"),
	]

	class Meta:
		verbose_name = " ENAP Navbar"
		verbose_name_plural = "ENAP Navbars"

	def __str__(self):
		return self.name


ALERT_TYPES = [
	('success', 'Sucesso'),
	('error', 'Erro'),
	('warning', 'Aviso'),
	('info', 'Informação'),
]
@register_snippet
class Alert(models.Model):
	
	title = models.CharField(max_length=255, blank=True, null=True, verbose_name="Título")
	message = RichTextField(verbose_name="Mensagem") 
	alert_type = models.CharField(
		max_length=20, 
		choices=ALERT_TYPES, 
		default='success', 
		verbose_name="Tipo de Alerta"
	)
	button_text = models.CharField(
		max_length=50, 
		blank=True, 
		default="Fechar", 
		verbose_name="Texto do Botão"
	)
	show_automatically = models.BooleanField(
		default=True, 
		verbose_name="Mostrar automaticamente"
	)
	
	panels = [
		FieldPanel('title'),
		FieldPanel('message'),
		FieldPanel('alert_type'),
		FieldPanel('button_text'),
		FieldPanel('show_automatically'),
	]
	
	def __str__(self):
		return self.title or f"Alerta ({self.get_alert_type_display()})"
	
	class Meta:
		verbose_name = "ENAP Alerta"
		verbose_name_plural = "ENAP Alertas"




# Os ícones, cores de fundo e cores dos ícones serão aplicados automaticamente
# com base no tipo de alerta selecionado

class AlertBlock(StructBlock):
	title = CharBlock(required=False, help_text="Título do alerta (opcional)")
	message = RichTextBlock(required=True, help_text="Mensagem do alerta")
	alert_type = ChoiceBlock(choices=ALERT_TYPES, default='success', help_text="Tipo do alerta")
	button_text = CharBlock(required=False, default="Fechar", help_text="Texto do botão (deixe em branco para não mostrar botão)")
	
	class Meta:
		template = "enap_designsystem/blocks/alerts.html"
		icon = 'warning'
		label = 'ENAP Alerta'




class WizardChooserBlock(ChooserBlock):
	@property
	def target_model(self):
		from enap_designsystem.models import Wizard  # Importação local para evitar referência circular
		return Wizard

	def get_form_state(self, value):
		return {
			'id': value.id if value else None,
			'title': str(value) if value else '',
		}

@register_snippet
class Wizard(ClusterableModel):
	"""
	Snippet para criar wizards reutilizáveis
	"""
	title = models.CharField(max_length=255, verbose_name="Título")
	
	panels = [
		FieldPanel('title'),
		InlinePanel('steps', label="Etapas do Wizard"),
	]
	
	def __str__(self):
		return self.title
	
	class Meta:
		verbose_name = "ENAP Wizard"
		verbose_name_plural = "ENAP Wizard"


class WizardStep(Orderable):
	"""
	Uma etapa dentro de um wizard
	"""
	wizard = ParentalKey(Wizard, on_delete=models.CASCADE, related_name='steps')
	title = models.CharField(max_length=255, verbose_name="Título da Etapa")
	content = models.TextField(blank=True, verbose_name="Conteúdo")
	
	panels = [
		FieldPanel('title'),
		FieldPanel('content'),
	]
	
	def __str__(self):
		return f"{self.title} - Etapa {self.sort_order + 1}"


class WizardBlock(StructBlock):
	"""
	Bloco para adicionar um wizard a uma página
	"""
	wizard = WizardChooserBlock(required=True)
	current_step = ChoiceBlock(
		choices=[(1, 'Etapa 1'), (2, 'Etapa 2'), (3, 'Etapa 3'), (4, 'Etapa 4'), (5, 'Etapa 5')],
		default=1,
		required=True,
		help_text="Qual etapa deve ser exibida como ativa",
	)
	
	def get_context(self, value, parent_context=None):
		context = super().get_context(value, parent_context)
		wizard = value['wizard']
		
		# Adiciona as etapas do wizard ao contexto
		steps = wizard.steps.all().order_by('sort_order')
		
		# Adapta o seletor de etapa atual para corresponder ao número real de etapas
		current_step = min(int(value['current_step']), steps.count())
		
		context.update({
			'wizard': wizard,
			'steps': steps,
			'current_step': current_step,
		})
		return context
	
	class Meta:
		template = 'enap_designsystem/blocks/wizard.html'
		icon = 'list-ol'
		label = 'ENAP Wizard'




@register_snippet
class Modal(models.Model):
	"""
	Snippet para criar modais reutilizáveis
	"""
	title = models.CharField(max_length=255, verbose_name="Título do Modal")
	content = RichTextField(verbose_name="Conteúdo do Modal")
	button_text = models.CharField(max_length=100, verbose_name="Texto do Botão", default="Abrir Modal")
	button_action_text = models.CharField(max_length=100, verbose_name="Texto do Botão de Ação", blank=True, help_text="Deixe em branco para não exibir um botão de ação")
	
	panels = [
		FieldPanel('title'),
		FieldPanel('content'),
		FieldPanel('button_text'),
		FieldPanel('button_action_text'),
	]
	
	def __str__(self):
		return self.title
	
	class Meta:
		verbose_name = "ENAP Modal"
		verbose_name_plural = "ENAP Modais"




@register_snippet
class ModalBlock(models.Model):
	"""
	Modal configurável que pode ser reutilizado em várias páginas.
	"""
	title = models.CharField(verbose_name="Título", max_length=255)
	content = RichTextField(verbose_name="Conteúdo", blank=True)
	button_text = models.CharField(verbose_name="Texto do botão", max_length=100, default="Abrir Modal")
	button_action_text = models.CharField(verbose_name="Texto do botão de ação", max_length=100, blank=True)
	
	# Novas opções
	SIZE_CHOICES = [
		('small', 'Pequeno'),
		('medium', 'Médio'),
		('large', 'Grande'),
	]
	size = models.CharField(verbose_name="Tamanho do Modal", max_length=10, choices=SIZE_CHOICES, default='medium')
	
	TYPE_CHOICES = [
		('message', 'Mensagem'),
		('form', 'Formulário'),
	]
	modal_type = models.CharField(verbose_name="Tipo de Modal", max_length=10, choices=TYPE_CHOICES, default='message')
	
	# Campos para formulário
	form_placeholder = models.CharField(verbose_name="Placeholder do formulário", max_length=255, blank=True)
	form_message = models.TextField(verbose_name="Mensagem do formulário", blank=True)
	
	panels = [
		FieldPanel('title'),
		FieldPanel('content'),
		FieldPanel('button_text'),
		FieldPanel('button_action_text'),
		FieldPanel('size'),
		FieldPanel('modal_type'),
		FieldPanel('form_placeholder'),
		FieldPanel('form_message'),
	]
	
	def __str__(self):
		return self.title
	
	class Meta:
		verbose_name = "Modal"
		verbose_name_plural = "Modais"


class ModalBlockStruct(blocks.StructBlock):
	modalenap = blocks.PageChooserBlock(
		required=True,
		label="Escolha um Modal",
	)

	class Meta:
		template = "enap_designsysten/blocks/modal_block.html"


@register_snippet
class Tab(ClusterableModel):
	"""
	Snippet para criar componentes de abas reutilizáveis com diferentes estilos
	"""
	title = models.CharField(max_length=255, verbose_name="Título do Componente")
	
	style = models.CharField(
		max_length=20,
		choices=[
			('style1', 'Estilo 1 (Com borda e linha inferior)'),
			('style2', 'Estilo 2 (Fundo verde quando ativo)'),
			('style3', 'Estilo 3 (Fundo verde quando ativo, sem bordas)'),
		],
		default='style1',
		verbose_name="Estilo Visual"
	)
	
	panels = [
		FieldPanel('title'),
		FieldPanel('style'),
		InlinePanel('tab_items', label="Abas"),
	]
	
	def __str__(self):
		return self.title
	
	class Meta:
		verbose_name = "Enap Tab"
		verbose_name_plural = "Enap Tabs"


class TabItem(Orderable):
	"""
	Um item de aba dentro do componente Tab
	"""
	tab = ParentalKey(Tab, on_delete=models.CASCADE, related_name='tab_items')
	title = models.CharField(max_length=255, verbose_name="Título da Aba")
	content = RichTextField(verbose_name="Conteúdo da Aba")
	
	panels = [
		FieldPanel('title'),
		FieldPanel('content'),
	]
	
	def __str__(self):
		return f"{self.tab.title} - {self.title}"
	

class TabBlock(StructBlock):
	tab = SnippetChooserBlock(
		'enap_designsystem.Tab', 
		required=True, 
		help_text="Selecione um componente de abas"
	)
	
	class Meta:
		template = "enap_designsystem/blocks/draft_tab.html"
		icon = 'table'
		label = 'ENAP Abas'

@register_snippet
class FormularioContato(models.Model):
	titulo = models.CharField(max_length=100, default="Formulário de Contato")
	estilo_campo = models.CharField(
		max_length=20,
		choices=[
			('rounded', 'Arredondado (40px)'),
			('square', 'Quadrado (8px)'),
		],
		default='rounded',
		help_text="Escolha o estilo de borda dos campos do formulário"
	)
	
	panels = [
		FieldPanel('titulo'),
		FieldPanel('estilo_campo'),
	]
	
	def __str__(self):
		return self.titulo
	
	class Meta:
		verbose_name = "ENAP Formulário de Contato"
		verbose_name_plural = "ENAP Formulários de Contato"




class DropdownLinkBlock(StructBlock):
	link_text = CharBlock(label="Texto do link", required=True)
	link_url = URLBlock(label="URL do link", required=True)
	
	class Meta:
		template = "enap_designsystem/blocks/dropdown.html"
		icon = "link"
		label = "Link do Dropdown"

# Bloco principal do dropdown
class DropdownBlock(StructBlock):
	label = CharBlock(label="Label", required=True, default="Label")
	button_text = CharBlock(label="Texto do botão", required=True, default="Select")
	dropdown_links = ListBlock(DropdownLinkBlock())
	
	class Meta:
		template = "enap_designsystem/blocks/dropdown.html"
		icon = "arrow-down"
		label = "Dropdown"




class MbaEspecializacao(Page):
	"""Página de MBA e Especialização com componente CourseIntroTopics."""

	template = 'enap_designsystem/pages/mba_especializacao.html'

	subpage_types = ['TemplateEspecializacao', 'ENAPComponentes']

	navbar = models.ForeignKey(
		"EnapNavbarSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)


	introducao = StreamField([
		('course_intro_topics', CourseIntroTopicsBlock()),
		# Outros blocos podem ser adicionados aqui se necessário
	], use_json_field=True, blank=True)


	beneficios = StreamField([
		# Outros blocos existentes
		('why_choose', WhyChooseEnaptBlock()),
	], blank=True, null=True)


	depoimentos = StreamField([
		# Outros blocos existentes
		('testimonials_carousel', TestimonialsCarouselBlock()),
	], blank=True, null=True)


	preview_dos_cursos = StreamField(
		[("preview_courses", PreviewCoursesBlock())],
		null=True,
		blank=True,
		use_json_field=True,
	)


	banner = StreamField(
		[
			("banner", EnapBannerBlock()), 
			("BannerConcurso", BannerConcurso()),
		],
		null=True,
		blank=True,
		use_json_field=True,
	)


	noticia = StreamField(
		[("noticias_carousel", NewsCarouselBlock())], 
		null=True,
		blank=True,
		use_json_field=True,
	)

	cards = StreamField(
		CARD_CARDS_STREAMBLOCKS,
		null=True,
		blank=True,
		use_json_field=True,
	)

	footer = models.ForeignKey(
		"EnapFooterSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	@classmethod  
	def can_create_at(cls, parent):  
		import inspect  
		for frame_record in inspect.stack():  
			if 'request' in frame_record.frame.f_locals:  
				user = frame_record.frame.f_locals['request'].user  
				
				if user.is_superuser: 
					return super().can_create_at(parent)  
				
				from .models import GroupPagePermission  
				has_permission = GroupPagePermission.objects.filter(  
					group__in=user.groups.all(), 
					page_type='MBAPage'  
				).exists()  
				
				return has_permission and super().can_create_at(parent)  
		
		return super().can_create_at(parent)  

	def save(self, *args, **kwargs):
		# Só adiciona os blocos padrão se for uma nova página
		if not self.pk:
			# Adiciona introducao se estiver vazio (antes course_intro_topics)
			if not self.introducao:
				self.introducao = [
					{'type': 'course_intro_topics', 'value': {}}
				]

			# Adiciona beneficios se estiver vazio (antes why_choose)
			if not self.beneficios:
				self.beneficios = [
					{'type': 'why_choose', 'value': {}}
				]

			# Adiciona depoimentos se estiver vazio (antes testimonials_carousel)
			if not self.depoimentos:
				self.depoimentos = [
					{'type': 'testimonials_carousel', 'value': {}}
				]

			# Adiciona preview_dos_cursos se estiver vazio (antes preview_courses)
			if not self.preview_dos_cursos:
				self.preview_dos_cursos = [
					{'type': 'preview_courses', 'value': {}}
				]

			# Adiciona banner no content se estiver vazio (antes content)
			if not self.banner:
				self.banner = [
					{'type': 'banner', 'value': {}}
				]

			# Adiciona noticia se estiver vazio (antes teste_noticia)
			if not self.noticia:
				self.noticia = [
					{'type': 'noticias_carousel', 'value': {}}
				]
		
		super().save(*args, **kwargs)

	content_panels = Page.content_panels + [
		FieldPanel('navbar'),
		FieldPanel('banner'),
		FieldPanel('introducao'),
		FieldPanel('beneficios'),
		FieldPanel('preview_dos_cursos'),
		FieldPanel('depoimentos'),
		FieldPanel('noticia'),
		FieldPanel('cards'),
		FieldPanel("footer"),
	]
	
	@property
	def url_filter(self):
		if hasattr(self, 'full_url') and self.full_url:
			return self.full_url
		return self.get_url_parts()[2] if self.get_url_parts() else ""
	
	@property
	def titulo_filter(self):
		if self.content:
			for block in self.content:
				if block.block_type == "banner":
					return strip_tags(str(block.value.get("title", ""))).strip()
		return ""

	@property
	def descricao_filter(self):
		if self.content:
			for block in self.content:
				if block.block_type == "banner":
					desc = block.value.get("description", "")
					if hasattr(desc, "source"):
						return strip_tags(desc.source).strip()
					return strip_tags(str(desc)).strip()
		return ""

	@property
	def data_atualizacao_filter(self):
		return self.last_published_at or self.latest_revision_created_at

	@property
	def categoria(self):
		return "Serviços"
	
	@property
	def imagem_filter(self):
		try:
			for bloco in self.content:
				if bloco.block_type == "banner":
					background = bloco.value.get("background_image")
					if background:
						return background.file.url
		except Exception:
			pass
		return ""
	
	@property
	def texto_unificado(self):
		def extract_text_from_block(block_value):
			result = []

			if isinstance(block_value, list):
				for subblock in block_value:
					result.extend(extract_text_from_block(subblock))
			elif hasattr(block_value, "get"):  # StructValue
				for key, val in block_value.items():
					result.extend(extract_text_from_block(val))
			elif isinstance(block_value, str):
				cleaned = strip_tags(block_value).strip()
				if cleaned and cleaned.lower() not in {
					"default", "tipo terciário", "tipo secundário", "tipo bg image",
					"bg-gray", "bg-blue", "bg-white", "fundo cinza", "fundo branco"
				}:
					result.append(cleaned)
			elif hasattr(block_value, "source"):  # RichText
				cleaned = strip_tags(block_value.source).strip()
				if cleaned:
					result.append(cleaned)

			return result

		streamfields = [
			self.content,
			self.course_intro_topics,
			self.why_choose,
			self.testimonials_carousel,
			self.preview_courses,
			self.teste_noticia,
		]

		textos = []
		for sf in streamfields:
			if sf:
				for block in sf:
					textos.extend(extract_text_from_block(block.value))

		texto_final = " ".join([t for t in textos if t])
		return re.sub(r"\s+", " ", texto_final).strip()

	search_fields = Page.search_fields + [
		index.SearchField("title", boost=3),
		index.SearchField("titulo_filter", name="titulo"),
		index.SearchField("descricao_filter", name="descricao"),
		index.FilterField("categoria", name="categoria_filter"),
		index.SearchField("url_filter", name="url"),
		index.SearchField("data_atualizacao_filter", name="data_atualizacao"),
		index.SearchField("imagem_filter", name="imagem"),
		index.SearchField("texto_unificado", name="body"),
	]

	class Meta:
		verbose_name = "MBA e Especialização"
		verbose_name_plural = "MBAs e Especializações"



class TemplateEspecializacao(Page):
	"""Página de MBA e Especialização com componente CourseIntroTopics."""

	template = 'enap_designsystem/pages/template_mba.html'
	parent_page_types = ['MbaEspecializacao']

	STATUS_INSCRICAO = [
		('abertas', 'Inscrições Abertas'),
		('encerradas', 'Inscrições Encerradas'),
		('em_andamento', 'Curso em Andamento'),
		('em_breve', 'Inscrições em breve'),
	]

	status_inscricao = models.CharField(
		max_length=20,
		choices=STATUS_INSCRICAO,
		default='abertas',
		verbose_name='Status das Inscrições',
		help_text='Define o status atual do curso/inscrições'
	)

	navbar = models.ForeignKey(
		"EnapNavbarSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	feature_course = StreamField([
    ('feature_course', CourseFeatureBlock()),
    ('card_cards', blocks.StreamBlock(CARD_CARDS_STREAMBLOCKS, required=False)),
	], 
		use_json_field=True, 
		blank=True, 
		null=True,
		default=[
			('feature_course', {
				'title_1': 'Características do Curso',
				'description_1': 'Conheça os principais diferenciais e características que tornam nosso programa único no mercado.',
				'title_2': 'Metodologia Inovadora',
				'description_2': 'Utilizamos as mais modernas práticas pedagógicas para garantir o melhor aprendizado.',
				'image': None
			})
		]
	)

	content = StreamField(
		[
			("banner", EnapBannerBlock()), 
		],
		null=True,
		blank=True,
		use_json_field=True,
		default=[
			('banner', {
				'background_image': None,
				'title': 'MBA e Especialização',
				'description': '<p>Desenvolva suas competências e alcance novos patamares na sua carreira profissional com nossos programas de excelência.</p>'
			})
		]
	)

	cards_one = StreamField(
		CARD_CARDS_STREAMBLOCKS,
		null=True,
		blank=True,
		use_json_field=True,
	)

	feature_estrutura = StreamField([
		('accordion', EnapAccordionBlock()),
		('feature_estrutura', CourseModulesBlock()),
	], use_json_field=True, blank=True, null=True, default=[
		('feature_estrutura', {
			'title': 'Estrutura do Curso',
			'modules': [
				{
					'module_title': '1º Módulo - Fundamentos',
					'module_description': 'Módulo introdutório com os conceitos fundamentais da área',
					'module_items': [
						'Conceitos básicos e terminologias',
						'Fundamentos teóricos essenciais',
						'Práticas introdutórias',
						'Estudos de caso iniciais'
					]
				},
				{
					'module_title': '2º Módulo - Desenvolvimento',
					'module_description': 'Aprofundamento nos conhecimentos e técnicas avançadas',
					'module_items': [
						'Técnicas avançadas',
						'Metodologias práticas',
						'Projetos aplicados',
						'Análise de casos reais'
					]
				},
				{
					'module_title': '3º Módulo - Especialização',
					'module_description': 'Especialização e aplicação prática dos conhecimentos',
					'module_items': [
						'Tópicos especializados',
						'Projeto final',
						'Apresentação e defesa',
						'Networking e mercado'
					]
				}
			]
		})
	])

	feature_processo_seletivo = StreamField([
		('feature_processo_seletivo', ProcessoSeletivoBlock()),
	], use_json_field=True, blank=True, null=True, default=[
		('feature_processo_seletivo', {
			'title': 'Processo Seletivo',
			'description': 'Conheça as etapas do nosso processo seletivo e saiba como participar',
			'module1_title': 'Inscrição',
			'module1_description': 'Realize sua inscrição através do nosso portal online. Preencha todos os dados solicitados e anexe a documentação necessária.',
			'module2_title': 'Análise Curricular',
			'module2_description': 'Nossa equipe realizará uma análise criteriosa do seu perfil profissional e acadêmico para verificar a adequação ao programa.',
			'module3_title': 'Resultado Final',
			'module3_description': 'Os candidatos aprovados serão comunicados via e-mail e receberão todas as orientações para início do curso.'
		})
	])

	team_carousel = StreamField([
    ('team_carousel', TeamCarouselBlock()),
    ('team_modern', TeamModern()),  
	], 
		use_json_field=True, 
		blank=True, 
		null=True,
		default=[
			('team_carousel', {
				'title': 'Nossa Equipe',
				'description': 'Conheça os profissionais especializados que compõem nosso corpo docente',
				'view_all_text': 'Ver todos os professores',
				'members': [
					{
						'name': 'Prof. Dr. Nome Sobrenome',
						'role': '<p>Coordenador Acadêmico</p>',
						'image': None
					},
					{
						'name': 'Prof. Mestre Nome Sobrenome',
						'role': '<p>Docente Especialista</p>',
						'image': None
					},
					{
						'name': 'Prof. Dr. Nome Sobrenome',
						'role': '<p>Professor Convidado</p>',
						'image': None
					},
					{
						'name': 'Prof. Mestre Nome Sobrenome',
						'role': '<p>Consultor Especializado</p>',
						'image': None
					}
				]
			})
		]
	)

	cards = StreamField(
		CARD_CARDS_STREAMBLOCKS,
		null=True,
		blank=True,
		use_json_field=True,
	)

	footer = models.ForeignKey(
		"EnapFooterSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)
	
	content_panels = Page.content_panels + [
		FieldPanel('navbar'),
		FieldPanel('status_inscricao'),
		FieldPanel('content'),
		FieldPanel('feature_course'),
		FieldPanel('cards_one'),
		FieldPanel('feature_estrutura'),
		FieldPanel('team_carousel'),
		FieldPanel('feature_processo_seletivo'),
		FieldPanel('cards'),
		FieldPanel("footer"),
	]
	
	@property
	def url_filter(self):
		if hasattr(self, 'full_url') and self.full_url:
			return self.full_url
		return self.get_url_parts()[2] if self.get_url_parts() else ""

	@property
	def titulo_filter(self):
		if self.content:
			for block in self.content:
				if block.block_type == "banner":
					return strip_tags(str(block.value.get("title", ""))).strip()
		return ""

	@property
	def descricao_filter(self):
		if self.content:
			for block in self.content:
				if block.block_type == "banner":
					desc = block.value.get("description", "")
					if hasattr(desc, "source"):
						return strip_tags(desc.source).strip()
					return strip_tags(str(desc)).strip()
		return ""

	@property
	def categoria(self):
		return "Serviços"

	@property
	def data_atualizacao_filter(self):
		return self.last_published_at or self.latest_revision_created_at or self.first_published_at

	@property
	def imagem_filter(self):
		try:
			for bloco in self.content:
				if bloco.block_type == "banner":
					background = bloco.value.get("background_image")
					if background:
						return background.file.url
		except Exception:
			pass
		return ""
	
	@property
	def texto_unificado(self):
		def extract_text_from_block(block_value):
			result = []

			if isinstance(block_value, list):
				for subblock in block_value:
					result.extend(extract_text_from_block(subblock))
			elif hasattr(block_value, "get"):  # StructValue
				for key, val in block_value.items():
					result.extend(extract_text_from_block(val))
			elif isinstance(block_value, str):
				cleaned = strip_tags(block_value).strip()
				if cleaned and cleaned.lower() not in {
					"default", "tipo terciário", "tipo secundário", "tipo bg image",
					"bg-gray", "bg-blue", "bg-white", "fundo cinza", "fundo branco"
				}:
					result.append(cleaned)
			elif hasattr(block_value, "source"):  # RichText
				cleaned = strip_tags(block_value.source).strip()
				if cleaned:
					result.append(cleaned)

			return result

		streamfields = [
			self.content,
			self.feature_course,
			self.feature_estrutura,
			self.feature_processo_seletivo,
			self.team_carousel,
		]

		textos = []
		for sf in streamfields:
			if sf:
				for block in sf:
					textos.extend(extract_text_from_block(block.value))

		texto_final = " ".join([t for t in textos if t])
		return re.sub(r"\s+", " ", texto_final).strip()

	search_fields = Page.search_fields + [
		index.SearchField("title", boost=3),
		index.SearchField("titulo_filter", name="titulo"),
		index.SearchField("descricao_filter", name="descricao"),
		index.FilterField("categoria", name="categoria_filter"),
		index.SearchField("url_filter", name="url"),
		index.SearchField("data_atualizacao_filter", name="data_atualizacao"),
		index.SearchField("imagem_filter", name="imagem"),
		index.SearchField("texto_unificado", name="body"),
	]

	
	class Meta:
		verbose_name = "MBA e Especialização Especifico"
		verbose_name_plural = "MBAs e Especializações"





class OnlyCards(Page):
	template = 'enap_designsystem/pages/template_only-cards.html'

	featured_card = StreamField([
		("enap_section", EnapSectionBlock([
			("enap_cardgrid", EnapCardGridBlock([
				("enap_card", EnapCardBlock()),
			])),
		])),
	], blank=True, use_json_field=True)

	banner = StreamField(
		[
			("banner", EnapBannerBlock()), 
		],
		null=True,
		blank=True,
		use_json_field=True,
	)

	course_intro_topics = StreamField([
		('course_intro_topics', CourseIntroTopicsBlock()),
		# Outros blocos podem ser adicionados aqui se necessário
	], use_json_field=True, blank=True)

	navbar = models.ForeignKey(
		"EnapNavbarSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	footer = models.ForeignKey(
		"EnapFooterSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)
	
	content_panels = Page.content_panels + [
		FieldPanel('navbar'),
		FieldPanel('banner'),
		FieldPanel('course_intro_topics'),
		FieldPanel('featured_card'),
		FieldPanel("footer"),
	]

	@property
	def url_filter(self):
		if hasattr(self, 'full_url') and self.full_url:
			return self.full_url
		return self.get_url_parts()[2] if self.get_url_parts() else ""

	search_fields = Page.search_fields + [
		index.SearchField("title", boost=3),
		index.SearchField("banner"),
		index.SearchField("course_intro_topics"),
		index.SearchField("featured_card"),
		index.FilterField("url", name="url_filter"),
	]
	
	def get_searchable_content(self):
		content = super().get_searchable_content()

		def extract_text_from_block(block_value):
			result = []
			if isinstance(block_value, list):
				for subblock in block_value:
					result.extend(extract_text_from_block(subblock))
			elif hasattr(block_value, "get"):
				for key, val in block_value.items():
					result.extend(extract_text_from_block(val))
			elif isinstance(block_value, str):
				result.append(block_value)
			elif hasattr(block_value, "source"):
				result.append(block_value.source)
			return result

		streamfields = [
			self.banner,
			self.course_intro_topics,
			self.featured_card,
		]

		for sf in streamfields:
			if sf:
				for block in sf:
					content.extend(extract_text_from_block(block.value))

		return content


	class Meta:
		verbose_name = "ENAP apenas com cards(usar paar informativos)"
		verbose_name_plural = "ENAP Pagina so com cards"






class AreaAluno(Page):
	"""Página personalizada para exibir dados do aluno logado."""

	template = "enap_designsystem/pages/area_aluno.html"

	body = StreamField(
		LAYOUT_STREAMBLOCKS,
		null=True,
		blank=True,
		use_json_field=True,
	)

	navbar = models.ForeignKey(
		"EnapNavbarSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	footer = models.ForeignKey(
		"EnapFooterSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	content_panels = Page.content_panels + [
		FieldPanel("navbar"),
		FieldPanel("footer"),
		FieldPanel("body"),
	]

	# Serve apenas com usuário logado via sessão
	def serve(self, request):
		aluno = request.session.get("aluno_sso")
		if not aluno:
			return redirect("/")

		nome_completo = aluno.get("nome", "")
		primeiro_nome = nome_completo.split(" ")[0] if nome_completo else "Aluno"
		access_token = get_valid_access_token(request.session)
		verify_ssl = not settings.DEBUG

		headers = {
			"Authorization": f"Bearer {access_token}"
		}

		def fetch(endpoint, expect_dict=False):
			try:
				url = f"{settings.BFF_API_URL}{endpoint}"
				resp = requests.get(url, headers=headers, timeout=10, verify=verify_ssl)
				resp.raise_for_status()
				data = resp.json()

				if expect_dict:
					if isinstance(data, list):
						return data[0] if data else {}
					elif isinstance(data, dict):
						return data
					else:
						return {}
				return data

			except Exception as e:
				print(f"Erro ao acessar API {endpoint}: {e}")
				return {} if expect_dict else []

		def parse_date(date_str):
			if not date_str:
				return None
			for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
				try:
					return datetime.strptime(date_str, fmt)
				except ValueError:
					continue
			return None

		aluno_resumo = fetch("/aluno/resumo", expect_dict=True)
		print("aluno_resumo", aluno_resumo)
		cursos_andamento = fetch("/aluno/cursos/andamento")
		cursos_matriculado = fetch("/aluno/cursos/matriculado")
		cursos_analise = fetch("/aluno/cursos/analise")
		cursos_eventos = fetch("/aluno/cursos/eventos")
		

		for lista in [cursos_andamento, cursos_matriculado, cursos_analise, cursos_eventos]:
			lista = lista or []
			for curso in lista:
				curso["dataInicio"] = parse_date(curso.get("dataInicio"))
				curso["dataTermino"] = parse_date(curso.get("dataTermino"))

		TITULOS_CERTIFICADOS = {
			"distancia": "Cursos a distância",
			"outros": "Outros cursos",
			"certificacoes": "Certificações",
			"eventos": "Eventos, Oficinas e Premiações",
			"migrados": "Outros",
			"voluntariado": "Voluntariado",
		}

		certificados = {
			"distancia": fetch("/aluno/certificados/cursos-distancia"),
			"outros": fetch("/aluno/certificados/cursos-outros"),
			"certificacoes": fetch("/aluno/certificados/certificacoes"),
			"eventos": fetch("/aluno/certificados/eventos-oficinas-premiacoes"),
			"migrados": fetch("/aluno/certificados/migrados"),
			"voluntariado": fetch("/aluno/certificados/voluntariado"),
		}

		for lista in certificados.values():
			lista = lista or []
			for cert in lista:
				cert["dataInicioAula"] = parse_date(cert.get("dataInicioAula"))
				cert["dataFimAula"] = parse_date(cert.get("dataFimAula"))
				cert["dataEmissao"] = parse_date(cert.get("dataEmissao"))

		context = self.get_context(request)
		context["aluno"] = aluno
		context["primeiro_nome"] = primeiro_nome
		context["aluno_resumo"] = aluno_resumo
		# Atualmente a API não retorna foto/imagem do usuário
		# de qualquer forma esse método (serve()) e o html já esperam
		context["aluno_foto"] = aluno_resumo.get("foto") or "/static/enap_designsystem/blocks/suap/default_1.png"
		context["aluno_estatisticas"] = {
			"eventos": aluno_resumo.get("eventos") if aluno_resumo else 0,
			"oficinas": aluno_resumo.get("oficinas") if aluno_resumo else 0,
			"cursos": aluno_resumo.get("cursos") if aluno_resumo else 0,
		}
		context["aluno_cursos"] = {
			"eventos": cursos_eventos,
			"andamento": cursos_andamento,
			"matriculado": cursos_matriculado,
			"analise": cursos_analise,
		}
		context["certificados_nomeados"] = [
			{
				"tipo": tipo,
				"titulo": TITULOS_CERTIFICADOS[tipo],
				"lista": certificados.get(tipo, []),
			}
			for tipo in TITULOS_CERTIFICADOS
		]

		return render(request, self.template, context)

	indexed = False

	@classmethod
	def get_indexed_instances(cls):
		return []

	def indexing_is_enabled(self):
		return False

	search_fields = []

	class Meta:
		verbose_name = "Área do Aluno"
		verbose_name_plural = "Área do Aluno"
  
class EnapSearchElastic(Page):
	template = "enap_designsystem/pages/page_search.html"

	navbar = models.ForeignKey("EnapNavbarSnippet", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
	footer = models.ForeignKey("EnapFooterSnippet", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

	content_panels = Page.content_panels + [
		FieldPanel('navbar'),
		FieldPanel("footer"),
	]

	# Caso entre na pagina de Busca sem nada, redireciona para um default
	def serve(self, request, *args, **kwargs):
		if "tipo" not in request.GET:
			query = request.GET.get("q", "")
			ordenacao = request.GET.get("ordenacao", "relevantes")
			return redirect(f"{request.path}?q={query}&tipo=cursos&ordenacao={ordenacao}")

		return super().serve(request, *args, **kwargs)
	
	######### ATENÇÃO JOOMLA-WAGTAIL
	# Imagens atuais usam o enap.gov.br do Joomla para serem exibidas!
	# Após virar a chave pelo Wagtail, as imagens deixarão de funcionar
	# Será necessário tratar com imagens que existam no wagtail
	# ou utilizar algum link no lugar de enap.gov.br
	def parse_images(self, item, tipo):
		try:
			img = item.get("imagem")

			# Caso 1: imagem é dict com image_intro
			if isinstance(img, dict) and img.get("image_intro"):
				item["imagem"] = "https://enap.gov.br/" + img["image_intro"]

			# Caso 2: imagem é string (link parcial)
			elif isinstance(img, str):
				item["imagem"] = img

			# Caso 3: nenhum dos dois — define None ou imagem default
			else:
				if tipo == "noticias":
					item["imagem"] = "/static/enap_designsystem/icons/thumb-noticias-novo.png"
				else:
					item["imagem"] = None  # ou: "/static/enap_designsystem/icons/280-140-default.png"

		except Exception as e:
			print("Erro ao processar imagem:", e)
			item["imagem"] = None

		return item

	def parse_datas(self, item, tipo):
		"""Converte campos de data string ISO para datetime"""
		campos_data = [
			"dataPublicacao",
			"dataAtualizacao",
			"inicioInscricoes",
			"fimInscricoes",
			"inicioRealizacao",
			"fimRealizacao",
			"data_publicacao"
		]

		for campo in campos_data:
			valor = item.get(campo)
			if isinstance(valor, str) and valor:
				try:
					# Substitui Z por +00:00 para compatibilidade com datetime.fromisoformat
					item[campo] = datetime.fromisoformat(valor.replace("Z", "+00:00"))
				except Exception:
					# Se falhar a conversão, deixa como estava
					pass
		
		return self.parse_images(item, tipo)

	def normalize_noticia(self, item):
		# Dicionário com os mapeamentos dos sufixos para os nomes amigáveis
		mapping = {
   			"title": "titulo",
   			"_descricao_filter": "descricao",
			"_url_filter": "url",
			"_data_atualizacao_filter": "data_atualizacao",
			"last_published_at_filter": "data_publicacao",
			"_imagem_filter":"imagem"
		}

		# Inicializa o dicionário resultante
		normalized = {}

		# Itera sobre as chaves do item
		for key, value in item.items():
			for suffix, normalized_key in mapping.items():
				if key.endswith(suffix):
					normalized[normalized_key] = value
					break  # Para caso o sufixo seja encontrado

		return normalized
  
	def normalize_wagtail(self, item):
		# Dicionário com os mapeamentos dos sufixos para os nomes amigáveis
		mapping = {
			"titulo": "titulo",
			"tag": "origem",
			"link": "link",
			"descricao": "descricao",
			"title": "title",
			"_titulo_filter": "titulo_2",
			"_descricao_filter": "descricao_2",
			"_url_filter": "url",
			"last_published_at_filter": "data_atualizacao",
			"first_published_at_filter": "data_publicacao",
			"dataPublicacao": "dataPublicacao"
		}

		# Inicializa o dicionário resultante
		normalized = {}

		# Itera sobre as chaves do item
		for key, value in item.items():
			for suffix, normalized_key in mapping.items():
				if key.endswith(suffix):
					normalized[normalized_key] = value
					break  # Para caso o sufixo seja encontrado

		return normalized

	def normalize_servico(self, item):
		# Dicionário com os mapeamentos dos sufixos para os nomes amigáveis
		mapping = {
   			"title": "titulo",
   			"_descricao_filter": "descricao",
			"_url_filter": "url",
			"_data_atualizacao_filter": "data_atualizacao",
			"first_published_at_filter": "data_publicacao",
		}

		# Inicializa o dicionário resultante
		normalized = {}

		# Itera sobre as chaves do item
		for key, value in item.items():
			for suffix, normalized_key in mapping.items():
				if key.endswith(suffix):
					normalized[normalized_key] = value
					break  # Para caso o sufixo seja encontrado

		return normalized

	# ✅ NOVA FUNÇÃO ADICIONADA
	def get_sort_field(self, tipo_conteudo, ordenacao_atual):
		"""Retorna o campo de ordenação correto baseado na documentação da API"""
		ordenacao_por_endpoint = {
			"eventos": {
				"recentes": "inicioRealizacao",
				"relevantes": "_score", 
				"vistos": "dataPublicacao"
			},
			"noticias": {
				"recentes": "dataAtualizacao",
				"relevantes": "_score",
				"vistos": "dataPublicacao"
			},
			"servicos": {
				"recentes": "dataAtualizacao",
				"relevantes": "_score", 
				"vistos": "dataPublicacao"
			},
			"pesquisa_conhecimento": {
				"recentes": "dataPublicacao",
				"relevantes": "_score",
				"vistos": "dataPublicacao"
			},
			"cursos": {
				"recentes": "dataPublicacao",
				"relevantes": "_score",
				"vistos": "dataPublicacao"
			},
			"todos": {
				"recentes": "dataPublicacao",
				"relevantes": "_score",
				"vistos": "dataPublicacao"
			}
		}
		
		tipo_config = ordenacao_por_endpoint.get(tipo_conteudo, ordenacao_por_endpoint["todos"])
		return tipo_config.get(ordenacao_atual, "dataPublicacao")

	def get_context(self, request, *args, **kwargs):
		context = super().get_context(request, *args, **kwargs)
		verify_ssl = not settings.DEBUG
		query = request.GET.get("q", "").strip()
		tipo = request.GET.get("tipo", "").strip()
		ordenacao = request.GET.get("ordenacao", "relevantes")
		page = int(request.GET.get("page", 1))
		if tipo == "cursos":
			rows_per_page = 12
		else:
			rows_per_page = 10
		
		context["query_navbar"] = request.GET.get("q", "")

		base_url = os.getenv("BFF_API_URL", "https://bff-portal.sandbox.enap.gov.br/v1")

		endpoints = {
			"cursos": "/busca/cursos/pesquisa",
			"noticias": "/busca/wagtail/pesquisa",
			"eventos": "/busca/eventos-oficinas/pesquisa",
			"servicos": "/busca/wagtail/pesquisa",
			"pesquisa_conhecimento": "/busca/repositorio/pesquisa",
			"todos": "/busca/pesquisa-wagtail"
		}

		endpoints_filtros = {
			"modalidade": "/busca/cursos/modalidades",
			"inscricoes": "/busca/cursos/inscricoes",
			"temas": "/busca/cursos/temas",
			"categoria": "/busca/cursos/categorias",
			"competencias": "/busca/cursos/competencias",
		}

		context["filtros"] = {}

		for chave, endpoint in endpoints_filtros.items():
			try:
				resp = requests.get(f"{base_url.rstrip('/')}{endpoint}", timeout=10, verify=verify_ssl)
				resp.raise_for_status()
				context["filtros"][chave] = resp.json()
			except Exception:
				context["filtros"][chave] = []

		# ✅ NOVA LÓGICA DE ORDENAÇÃO
		sort_by = self.get_sort_field(tipo, ordenacao)

		# Filtros principais
		filter_data = {"termo": query}
		mapa_chaves = {
			"modalidade": "modalidades",
			"inscricoes": "inscricoes",
			"temas": "temas",
			"categoria": "categorias",
			"competencias": "competencias"
		}

		for campo, chave_api in mapa_chaves.items():
			valores = request.GET.getlist(campo)
			if valores:
				filter_data[chave_api] = valores

		# Criar payload baseado no tipo
		if tipo == "noticias":
			payload = {
				"sortBy": sort_by,
				"descending": True,
				"page": page,
				"rowsPerPage": rows_per_page,
				"filter": {**filter_data, "categoria": "Notícias"}
			}
		elif tipo == "servicos":
			payload = {
				"sortBy": sort_by,
				"descending": True,
				"page": page,
				"rowsPerPage": rows_per_page,
				"filter": {**filter_data, "categoria": "Serviços"}
			}
		else:
			payload = {
				"sortBy": sort_by,
				"descending": True,
				"page": page,
				"rowsPerPage": rows_per_page,
				"filter": filter_data
			}

		context.update({
			"query": query,
			"tipo": tipo,
			"ordenacao": ordenacao
		})

		# ✅ NOVA LÓGICA DOS TOTAIS - SIMPLIFICADA
		tabs_totais = {}
		for chave, endpoint in endpoints.items():
			# Usa a nova função para cada aba
			sort_tab = self.get_sort_field(chave, ordenacao)
			
			# Filtros específicos
			if chave == "noticias":
				filter_tab = {**filter_data, "categoria": "Notícias"}
			elif chave == "servicos":
				filter_tab = {**filter_data, "categoria": "Serviços"}
			else:
				filter_tab = filter_data

			payload_tab = {
				"sortBy": sort_tab,
				"descending": True,
				"page": 1,
				"rowsPerPage": 1,
				"filter": filter_tab
			}
			
			try:
				resp = requests.post(
					f"{base_url.rstrip('/')}{endpoint}",
					json=payload_tab,
					timeout=10,
					verify=verify_ssl
				)
				resp.raise_for_status()
				tabs_totais[chave] = resp.json().get("total", 0)
			except Exception as e:
				print(f"[ERRO total aba {chave}]", e)
				tabs_totais[chave] = 0

		context["tabs_totais"] = tabs_totais

		# Se tipo atual for válido, busca resultados dessa aba
		if tipo in endpoints:
			try:
				url = f"{base_url.rstrip('/')}{endpoints[tipo]}"
				resp = requests.post(url, json=payload, timeout=10, verify=verify_ssl)
				resp.raise_for_status()
				raw_results = resp.json().get("results", [])
				total_results = resp.json().get("total", 0)
				if tipo == "noticias":
					normalized = [self.normalize_noticia(item) for item in raw_results]
					results = [self.parse_datas(item, tipo) for item in normalized]
				elif tipo == "servicos":
					normalized = [self.normalize_servico(item) for item in raw_results]
					results = [self.parse_datas(item, tipo) for item in normalized]	
				elif tipo == "todos":
					normalized = [self.normalize_wagtail(item) for item in raw_results]
					results = [self.parse_datas(item, tipo) for item in normalized]	
				else:
					results = [self.parse_datas(item, tipo) for item in raw_results]
				
    
				context["results"] = results
				context["results_count"] = total_results
				
				# Paginação
				total_pages = (total_results + rows_per_page - 1) // rows_per_page
				window_size = 5
				half_window = window_size // 2

				if total_pages <= window_size:
					pages = list(range(1, total_pages + 1))
				elif page <= half_window + 1:
					pages = list(range(1, window_size + 1))
				elif page >= total_pages - half_window:
					pages = list(range(total_pages - window_size + 1, total_pages + 1))
				else:
					pages = list(range(page - half_window, page + half_window + 1))

				# Query string base
				from urllib.parse import urlencode
				query_params = request.GET.copy()
				query_params.pop("page", None)
				base_querystring = urlencode(query_params, doseq=True)
				if base_querystring:
					base_querystring += "&"

				# Exibição do intervalo "1 - 10 de 61"
				if total_results == 0 or len(results) == 0:
					start_display = 0
					end_display = 0
				else:
					start_display = ((page - 1) * rows_per_page) + 1
					end_display = start_display + len(results) - 1

				context["pagination"] = {
					"current_page": page,
					"total_pages": total_pages,
					"has_previous": page > 1,
					"has_next": page < total_pages,
					"pages": pages,
					"base_querystring": base_querystring,
					"start_display": start_display,
					"end_display": end_display
				}

			except Exception as e:
				print("Erro na busca:", e)
				context["results"] = []
				context["results_count"] = 0

		return context

	class Meta:
		verbose_name = "ENAP Busca (ElasticSearch)"


class Template001(Page):
	"""Página de MBA e Especialização com vários componentes."""

	template = 'enap_designsystem/pages/template_001.html'

	# Navbar (snippet)
	navbar = models.ForeignKey(
		"EnapNavbarSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	# Banner fields
	
	banner_background_image = models.ForeignKey(
		get_image_model_string(),
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name='+',
		verbose_name=_("Banner Background Image")
	)  

	banner_title = models.CharField(
		max_length=255,
		default="Título do Banner",
		verbose_name=_("Banner Title")
	)
	banner_description = RichTextField(
		features=["bold", "italic", "ol", "ul", "hr", "link", "document-link"],
		default="<p>Descrição do banner. Edite este texto para personalizar o conteúdo.</p>",
		verbose_name=_("Banner Description")
	)
	
	# Feature Course fields
	title_1 = models.CharField(
		max_length=255,
		default="Título da feature 1",
		verbose_name=_("Primeiro título")
	)
	description_1 = models.TextField(
		default="It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. The point of using Lorem Ipsum is that it has a more-or-less normal distribution of letters, as opposed to using 'Content here, content here', making it look like readable English.",
		verbose_name=_("Primeira descrição")
	)
	title_2 = models.CharField(
		max_length=255,
		default="Título da feature 2",
		verbose_name=_("Segundo título")
	)
	description_2 = models.TextField(
		default="It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. The point of using Lorem Ipsum is that it has a more-or-less normal distribution of letters, as opposed to using 'Content here, content here', making it look like readable English.",
		verbose_name=_("Segunda descrição")
	)
	image = models.ForeignKey(
		get_image_model_string(),
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name='+',
		verbose_name=_("Imagem da feature")
	)
	
	# Estrutura como StreamField
	# Estrutura como StreamField
	feature_estrutura = StreamField([
		('feature_estrutura', CourseModulesBlock()),
	], use_json_field=True, blank=True, null=True, default=[
		('feature_estrutura', {
			'title': 'Estrutura do curso',
			'modules': [
				{
					'module_title': '1º Módulo',
					'module_description': 'Descrição do primeiro módulo',
					'module_items': [
						'Conceitos básicos',
						'Fundamentos teóricos',
						'Práticas iniciais'
					]
				},
				{
					'module_title': '2º Módulo',
					'module_description': 'Descrição do segundo módulo',
					'module_items': [
						'Desenvolvimento avançado',
						'Estudos de caso',
						'Projetos práticos'
					]
				},
				{
					'module_title': '3º Módulo',
					'module_description': 'Descrição do terceiro módulo',
					'module_items': [
						'Especialização',
						'Projeto final',
						'Apresentação'
					]
				}
			]
		})
	]) 

	# Team Carousel como StreamField
	team_carousel = StreamField([
		('team_carousel', TeamCarouselBlock()),
	], use_json_field=True, blank=True, null=True, default=[
		('team_carousel', {
			'title': 'Nossa Equipe',
			'description': 'Equipe de desenvolvedores e etc',
			'view_all_text': 'Ver todos',
			'members': [
				{'name': 'Membro 1', 'role': 'Cargo 1', 'image': None},
				{'name': 'Membro 2', 'role': 'Cargo 2', 'image': None},
				{'name': 'Membro 3', 'role': 'Cargo 3', 'image': None},
				{'name': 'Membro 4', 'role': 'Cargo 4', 'image': None},
		]
	})])
	
	# Processo Seletivo fields
	processo_title = models.CharField(
		max_length=255, 
		default="Processo seletivo",
		verbose_name=_("Título do Processo Seletivo")
	)
	processo_description = models.TextField(
		default="Sobre o processo seletivo",
		verbose_name=_("Descrição do Processo Seletivo")
	)
	
	# Módulo 1
	processo_module1_title = models.CharField(
		max_length=255,
		default="Inscrição",
		verbose_name=_("Título do 1º Módulo")
	)
	processo_module1_description = models.TextField(
		default="Lorem ipsum dolor sit amet",
		verbose_name=_("Descrição do 1º Módulo")
	)
	
	# Módulo 2
	processo_module2_title = models.CharField(
		max_length=255,
		default="Seleção",
		verbose_name=_("Título do 2º Módulo")
	)
	processo_module2_description = models.TextField(
		default="Lorem ipsum dolor sit amet",
		verbose_name=_("Descrição do 2º Módulo")
	)
	
	# Módulo 3
	processo_module3_title = models.CharField(
		max_length=255,
		default="Resultado",
		verbose_name=_("Título do 3º Módulo")
	)
	processo_module3_description = models.TextField(
		default="Lorem ipsum dolor sit amet",
		verbose_name=_("Descrição do 3º Módulo")
	)

	# Footer (snippet)
	footer = models.ForeignKey(
		"EnapFooterSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)
	
	# Painéis de conteúdo organizados em seções
	content_panels = Page.content_panels + [
		FieldPanel('navbar'),
		
		MultiFieldPanel([
			FieldPanel('banner_background_image', classname="default-image-14"),
			FieldPanel('banner_title'),
			FieldPanel('banner_description'),
		], heading="Banner"),
		
		MultiFieldPanel([
			FieldPanel('title_1'),
			FieldPanel('description_1'),
			FieldPanel('title_2'),
			FieldPanel('description_2'),
			FieldPanel('image', classname="default-image-14"),
		], heading="Feature Course"),
		
		FieldPanel('feature_estrutura'),
		
		MultiFieldPanel([
			FieldPanel('processo_title'),
			FieldPanel('processo_description'),
			FieldPanel('processo_module1_title'),
			FieldPanel('processo_module1_description'),
			FieldPanel('processo_module2_title'),
			FieldPanel('processo_module2_description'),
			FieldPanel('processo_module3_title'),
			FieldPanel('processo_module3_description'),
		], heading="Processo Seletivo"),
		
		FieldPanel('team_carousel'),
		
		FieldPanel("footer"),
	]
	
	@property
	def url_filter(self):
		if hasattr(self, 'full_url') and self.full_url:
			return self.full_url
		return self.get_url_parts()[2] if self.get_url_parts() else ""

	@property
	def titulo_filter(self):
		return strip_tags(self.banner_title or "").strip()

	@property
	def descricao_filter(self):
		return strip_tags(self.banner_description or "").strip()

	@property
	def categoria(self):
		return "Serviços"

	@property
	def data_atualizacao_filter(self):
		return self.last_published_at or self.latest_revision_created_at or self.first_published_at

	@property
	def imagem_filter(self):
		try:
			if self.image:
				return self.image.file.url
		except Exception:
			pass
		return ""
	
	@property
	def texto_unificado(self):
		def extract_text_from_block(block_value):
			result = []

			if isinstance(block_value, list):
				for subblock in block_value:
					result.extend(extract_text_from_block(subblock))
			elif hasattr(block_value, "get"):
				for key, val in block_value.items():
					result.extend(extract_text_from_block(val))
			elif isinstance(block_value, str):
				cleaned = strip_tags(block_value).strip()
				if cleaned and cleaned.lower() not in {
					"default", "tipo terciário", "tipo secundário", "tipo bg image",
					"bg-gray", "bg-blue", "bg-white", "fundo cinza", "fundo branco"
				}:
					result.append(cleaned)
			elif hasattr(block_value, "source"):
				cleaned = strip_tags(block_value.source).strip()
				if cleaned:
					result.append(cleaned)

			return result

		textos = []

		# Campos simples (char/text/richtext)
		simples = [
			self.banner_title,
			self.banner_description,
			self.title_1,
			self.description_1,
			self.title_2,
			self.description_2,
			self.processo_title,
			self.processo_description,
			self.processo_module1_title,
			self.processo_module1_description,
			self.processo_module2_title,
			self.processo_module2_description,
			self.processo_module3_title,
			self.processo_module3_description,
		]

		for campo in simples:
			if campo:
				textos.append(strip_tags(str(campo)).strip())

		# Campos de blocos
		for sf in [self.feature_estrutura, self.team_carousel]:
			if sf:
				for block in sf:
					textos.extend(extract_text_from_block(block.value))

		return re.sub(r"\s+", " ", " ".join([t for t in textos if t])).strip()

	search_fields = Page.search_fields + [
		index.SearchField("title", boost=3),
		index.SearchField("titulo_filter", name="titulo"),
		index.SearchField("descricao_filter", name="descricao"),
		index.FilterField("categoria", name="categoria_filter"),
		index.SearchField("url_filter", name="url"),
		index.SearchField("data_atualizacao_filter", name="data_atualizacao"),
		index.SearchField("imagem_filter", name="imagem"),
		index.SearchField("texto_unificado", name="body"),
	]
	
	def get_searchable_content(self):
		content = super().get_searchable_content()

		fields = [
			self.banner_title,
			self.banner_description,
			self.title_1,
			self.description_1,
			self.title_2,
			self.description_2,
			self.processo_title,
			self.processo_description,
			self.processo_module1_title,
			self.processo_module1_description,
			self.processo_module2_title,
			self.processo_module2_description,
			self.processo_module3_title,
			self.processo_module3_description,
		]

		for f in fields:
			if f:
				content.append(str(f))

		def extract_text_from_block(block_value):
			result = []
			if isinstance(block_value, list):
				for subblock in block_value:
					result.extend(extract_text_from_block(subblock))
			elif hasattr(block_value, "get"):
				for key, val in block_value.items():
					result.extend(extract_text_from_block(val))
			elif isinstance(block_value, str):
				result.append(block_value)
			elif hasattr(block_value, "source"):
				result.append(block_value.source)
			return result

		if self.feature_estrutura:
			for block in self.feature_estrutura:
				content.extend(extract_text_from_block(block.value))
		if self.team_carousel:
			for block in self.team_carousel:
				content.extend(extract_text_from_block(block.value))

		return content


	class Meta:
		verbose_name = "Template 001"
		verbose_name_plural = "Templates 001"






class HolofotePage(Page):
	"""Template Holofote"""
	subpage_types = ['HolofotePage']

	template = "enap_designsystem/pages/template_holofote.html"

	test_content = models.TextField(
        blank=True,
        null=True,
        help_text="Teste se campos normais funcionam"
    )

	footer = models.ForeignKey(
		"EnapFooterSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	navbar = models.ForeignKey(
		"EnapNavbarSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	# Página "O que é o Holofote?"
	holofote_info_link = models.URLField(
    max_length=200,
    blank=True,
    help_text="Link para informações sobre o Holofote",
    verbose_name="Link Info Holofote"
	)

	holofote_links = StreamField([
        ('holofote_link', StructBlock([
            ('title', CharBlock(
                max_length=50,
                help_text="Texto que aparecerá no link (ex: Servir, Clima, etc.)"
            )),
            ('page', PageChooserBlock(
                help_text="Página para onde o link deve direcionar"
            )),
            ('anchor', CharBlock(
                max_length=50,
                required=False,
                help_text="Âncora opcional (ex: #cuidar) - será adicionada após a URL da página"
            )),
        ], icon='link', label='Link do Holofote')),
    	], blank=True, use_json_field=True, verbose_name="Links de Navegação do Holofote")

    

	body = StreamField([
		('citizen_server', CitizenServerBlock()),
		('topic_links', TopicLinksBlock()),
		('feature_list_text', FeatureWithLinksBlock()), 
		('QuoteModern', QuoteBlockModern()),
		('service_cards', ServiceCardsBlock()),
		('carousel_green', CarouselGreen()),
		('section_block', EnapSectionBlock()),
		('feature_list', FeatureListBlock()),
		('service_cards', ServiceCardsBlock()),
		('banner_image_cta', Banner_Image_cta()),
		('citizen_server', CitizenServerBlock()),
		("carrossel_cursos", CarrosselCursosBlock()),
		("enap_section", EnapSectionBlock([
			("enap_cardgrid", EnapCardGridBlock([
				("enap_card", EnapCardBlock()),
				('card_curso', CardCursoBlock()),
				('texto_imagem', TextoImagemBlock()),
			])),
		])),
		# Outros blocos padrão do Wagtail
		('heading', blocks.CharBlock(form_classname="title", label=_("Título"))),
		('paragraph', blocks.RichTextBlock(label=_("Parágrafo"))),
		('image', ImageChooserBlock(label=_("Imagem"))),
		('html', blocks.RawHTMLBlock(label=_("HTML")))
	], null=True, blank=True, verbose_name=_("Conteúdo da Página"))

	

	content_panels = Page.content_panels + [
		FieldPanel('test_content'), 
		PageChooserPanel('holofote_info_link'),
        FieldPanel('holofote_links'),
		FieldPanel('body'),
		FieldPanel("footer"),
		FieldPanel("navbar"),
	]

	@property
	def titulo_filter(self):
		for block in self.body:
			if hasattr(block.value, "get") and "title" in block.value:
				titulo = block.value.get("title")
				if titulo:
					return strip_tags(str(titulo)).strip()
		return ""

	@property
	def descricao_filter(self):
		for block in self.body:
			if hasattr(block.value, "get") and "description" in block.value:
				desc = block.value.get("description")
				if hasattr(desc, "source"):
					return strip_tags(desc.source).strip()
				return strip_tags(str(desc)).strip()
		return ""

	@property
	def categoria(self):
		return "Outros"

	@property
	def data_atualizacao_filter(self):
		return self.last_published_at or self.latest_revision_created_at or self.first_published_at

	@property
	def url_filter(self):
		if hasattr(self, 'full_url') and self.full_url:
			return self.full_url
		return self.get_url_parts()[2] if self.get_url_parts() else ""

	@property
	def imagem_filter(self):
		try:
			for bloco in self.body:
				if bloco.block_type == "banner_image_cta":
					hero_image = bloco.value.get("hero_image")
					if hero_image:
						return hero_image.file.url
		except Exception:
			pass

		return ""
	
	@property
	def texto_unificado(self):
		def extract_text_from_block(block_value):
			result = []

			if isinstance(block_value, list):
				for subblock in block_value:
					result.extend(extract_text_from_block(subblock))
			elif hasattr(block_value, "get"):  # StructValue
				for key, val in block_value.items():
					result.extend(extract_text_from_block(val))
			elif isinstance(block_value, str):
				cleaned = strip_tags(block_value).strip()
				if cleaned and cleaned.lower() not in {
					"default", "tipo terciário", "tipo secundário", "tipo bg image",
					"bg-gray", "bg-blue", "bg-white", "fundo cinza", "fundo branco"
				}:
					result.append(cleaned)
			elif hasattr(block_value, "source"):
				cleaned = strip_tags(block_value.source).strip()
				if cleaned:
					result.append(cleaned)

			return result

		textos = []
		if self.body:
			for block in self.body:
				textos.extend(extract_text_from_block(block.value))

		texto_final = " ".join([t for t in textos if t])
		return re.sub(r"\s+", " ", texto_final).strip()
		
	search_fields = Page.search_fields + [
		index.SearchField("title", boost=3),
		index.SearchField("titulo_filter", name="titulo"),
		index.SearchField("descricao_filter", name="descricao"),
		index.FilterField("categoria", name="categoria_filter"),
		index.SearchField("url_filter", name="url"),
		index.SearchField("data_atualizacao_filter", name="data_atualizacao"),
		index.SearchField("imagem_filter", name="imagem"),
		index.SearchField("texto_unificado", name="body"),
	]

	class Meta:
		verbose_name = _("Template Holofote")




# Funções para defaults dos StreamFields
def get_default_banner_evento():
    return [{'type': 'enap_herobanner', 'value': {}}]

def get_default_informacoes_evento():
    return [{'type': 'evento', 'value': {}}]

def get_default_por_que_participar():
    return [{'type': 'why_choose', 'value': {}}]

def get_default_palestrantes():
    return [{'type': 'team_carousel', 'value': {}}]

def get_default_inscricao_cta():
    return [{'type': 'cta_destaque', 'value': {}}]

def get_default_faq():
    return [{'type': 'accordion', 'value': {}}]


class PreEventoPage(Page):
    """Template para página de Pré-evento - divulgação e inscrições"""
    
    template = 'enap_designsystem/pages/pre_evento.html'
    
    navbar = models.ForeignKey(
        "EnapNavbarSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    
    # Banner principal do evento
    banner_evento = StreamField([
        ("enap_herobanner", EnapBannerBlock()),
        ("hero_animada", HeroAnimadaBlock()),
    ], use_json_field=True, blank=True, default=get_default_banner_evento)
    
    # Informações sobre o evento
    informacoes_evento = StreamField([
        ("evento", EventoBlock()),
        ("container_info", ContainerInfo()),
    ], use_json_field=True, blank=True, default=get_default_informacoes_evento)
    
    # Por que participar
    por_que_participar = StreamField([
        ("why_choose", WhyChooseEnaptBlock()),
        ("feature_list", FeatureListBlock()),
    ], use_json_field=True, blank=True, default=get_default_por_que_participar)
    
    # Palestrantes/Equipe
    palestrantes = StreamField([
        ("team_carousel", TeamCarouselBlock()),
        ("team_moderna", TeamModern()),
    ], use_json_field=True, blank=True, default=get_default_palestrantes)
    
    # CTA de inscrição
    inscricao_cta = StreamField([
        ("cta_destaque", CtaDestaqueBlock()),
        ("secao_adesao", SecaoAdesaoBlock()),
    ], use_json_field=True, blank=True, default=get_default_inscricao_cta)
    
    # FAQ sobre o evento
    faq = StreamField([
        ("accordion", EnapAccordionBlock()),
    ], use_json_field=True, blank=True, default=get_default_faq)
    
    footer = models.ForeignKey(
        "EnapFooterSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    
    def save(self, *args, **kwargs):
        # Método save simplificado - defaults já estão nos StreamFields
        super().save(*args, **kwargs)
    
    content_panels = Page.content_panels + [
        FieldPanel('navbar'),
        FieldPanel('banner_evento'),
        FieldPanel('informacoes_evento'),
        FieldPanel('por_que_participar'),
        FieldPanel('palestrantes'),
        FieldPanel('inscricao_cta'),
        FieldPanel('faq'),
        FieldPanel('footer'),
    ]

    class Meta:
        verbose_name = _("Enap Pré Evento")



# Funções para defaults - Durante Evento (APENAS UMA VEZ)
def get_default_banner_ao_vivo():
    return [{'type': 'enap_herobanner', 'value': {}}]

def get_default_transmissao():
    return [{'type': 'container_info', 'value': {}}]

def get_default_programacao():
    return [{'type': 'evento', 'value': {}}]

def get_default_palestrantes_atual():
    return [{'type': 'team_moderna', 'value': {}}]

def get_default_galeria_ao_vivo():
    return [{'type': 'galeria_moderna', 'value': {}}]

def get_default_interacao():
    return [{'type': 'contato', 'value': {}}]


class DuranteEventoPage(Page):
    """Template para página Durante o evento - transmissão ao vivo e interação"""
    
    template = 'enap_designsystem/pages/durante_evento.html'

    navbar = models.ForeignKey(
        "EnapNavbarSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    
    # Banner com status ao vivo
    banner_ao_vivo = StreamField([
        ("enap_herobanner", EnapBannerBlock()),
    ], use_json_field=True, blank=True, default=get_default_banner_ao_vivo)
    
    # Streaming/Transmissão
    transmissao = StreamField([
        ("container_info", ContainerInfo()),
        ("texto_imagem", TextoImagemBlock()),
    ], use_json_field=True, blank=True, default=get_default_transmissao)
    
    # Programação atual
    programacao = StreamField([
        ("evento", EventoBlock()),
    ], use_json_field=True, blank=True, default=get_default_programacao)
    
    # Palestrantes ativos
    palestrantes_atual = StreamField([
        ("team_moderna", TeamModern()),
    ], use_json_field=True, blank=True, default=get_default_palestrantes_atual)
    
    # Galeria de fotos ao vivo
    galeria_ao_vivo = StreamField([
        ("galeria_moderna", GalleryModernBlock()),
    ], use_json_field=True, blank=True, default=get_default_galeria_ao_vivo)
    
    # Área de contato/chat
    interacao = StreamField([
        ("contato", ContatoBlock()),
        ("form_contato", FormContato()),
    ], use_json_field=True, blank=True, default=get_default_interacao)

    footer = models.ForeignKey(
        "EnapFooterSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    
    def save(self, *args, **kwargs):
        # Defaults já estão nos StreamFields, método simplificado
        super().save(*args, **kwargs)
    
    content_panels = Page.content_panels + [
        FieldPanel('navbar'),
        FieldPanel('banner_ao_vivo'),
        FieldPanel('transmissao'),
        FieldPanel('programacao'),
        FieldPanel('palestrantes_atual'),
        FieldPanel('galeria_ao_vivo'),
        FieldPanel('interacao'),
        FieldPanel('footer'),
    ]

    class Meta:
        verbose_name = _("Enap Durante Evento")




# Funções para defaults - Pós Evento
def get_default_banner_agradecimento():
    return [{'type': 'enap_herobanner', 'value': {}}]

def get_default_materiais():
    return [{'type': 'download', 'value': {}}]

def get_default_galeria_evento():
    return [{'type': 'galeria_moderna', 'value': {}}]

def get_default_depoimentos():
    return [{'type': 'testimonials_carousel', 'value': {}}]

def get_default_proximos_eventos():
    return [{'type': 'eventos_carousel', 'value': {}}]

def get_default_proximas_acoes():
    return [{'type': 'cta_destaque', 'value': {}}]


class PosEventoPage(Page):
    """Template para página Pós-evento - materiais, feedback e próximos eventos"""
    
    template = 'enap_designsystem/pages/pos_evento.html'

    navbar = models.ForeignKey(
        "EnapNavbarSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    
    # Banner de agradecimento
    banner_agradecimento = StreamField([
        ("enap_herobanner", EnapBannerBlock()),
    ], use_json_field=True, blank=True, default=get_default_banner_agradecimento)
    
    # Materiais do evento
    materiais = StreamField([
        ("download", DownloadBlock()),
        ("section_card_title_center", SectionCardTitleCenterBlock()),
    ], use_json_field=True, blank=True, default=get_default_materiais)
    
    # Galeria de fotos do evento
    galeria_evento = StreamField([
        ("galeria_moderna", GalleryModernBlock()),
    ], use_json_field=True, blank=True, default=get_default_galeria_evento)
    
    # Depoimentos dos participantes
    depoimentos = StreamField([
        ("testimonials_carousel", TestimonialsCarouselBlock()),
        ("QuoteModern", QuoteBlockModern()),
    ], use_json_field=True, blank=True, default=get_default_depoimentos)
    
    # Próximos eventos
    proximos_eventos = StreamField([
        ("eventos_carousel", EventsCarouselBlock()),
        ("carrossel_cursos", CarrosselCursosBlock()),
    ], use_json_field=True, blank=True, default=get_default_proximos_eventos)
    
    # CTA para próximas ações
    proximas_acoes = StreamField([
        ("cta_destaque", CtaDestaqueBlock()),
        ("secao_adesao", SecaoAdesaoBlock()),
    ], use_json_field=True, blank=True, default=get_default_proximas_acoes)

    footer = models.ForeignKey(
        "EnapFooterSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    
    def save(self, *args, **kwargs):
        # Defaults já estão nos StreamFields, método simplificado
        super().save(*args, **kwargs)
    
    content_panels = Page.content_panels + [
        FieldPanel('navbar'),
        FieldPanel('banner_agradecimento'),
        FieldPanel('materiais'),
        FieldPanel('galeria_evento'),
        FieldPanel('depoimentos'),
        FieldPanel('proximos_eventos'),
        FieldPanel('proximas_acoes'),
        FieldPanel('footer'),
    ]

    class Meta:
        verbose_name = _("Enap Pós Evento")







# Função para pegar primeira página disponível
def get_first_available_page():
    from wagtail.models import Page
    try:
        # Tenta pegar a primeira página que não seja root ou home
        page = Page.objects.exclude(
            content_type__model__in=['page', 'rootpage']
        ).live().first()
        return page if page else None
    except:
        return None

# Funções de default para CursoEadPage
def get_default_banner_curso():
    return [{'type': 'hero', 'value': {}}]

def get_default_apresentacao_curso():
    return [{'type': 'course_intro_topics', 'value': {}}]

def get_default_estrutura_curso():
    return [{'type': 'feature_estrutura', 'value': {}}]

def get_default_vantagens():
    return [{'type': 'why_choose', 'value': {}}]

def get_default_depoimentos_alunos():
    return [{'type': 'testimonials_carousel', 'value': {}}]

def get_default_cursos_relacionados():
    default_page = get_first_available_page()
    if default_page:
        return [{
            'type': 'preview_courses', 
            'value': {
                'titulo': 'Cursos relacionados',
                'paginas_relacionadas': default_page.pk
            }
        }]
    else:
        # Se não encontrar página, retorna sem o campo obrigatório preenchido
        return [{
            'type': 'preview_courses', 
            'value': {
                'titulo': 'Cursos relacionados'
            }
        }]

def get_default_inscricao():
    return [{'type': 'cta_2', 'value': {}}]

def get_default_faq_curso():
    return [{
        'type': 'accordion', 
        'value': {
            'title': 'Pergunta Frequente 1',
            'content': 'Esta é uma resposta de exemplo para a primeira pergunta frequente. Você pode editar este conteúdo conforme necessário.'
        }
    }]

def get_default_curso():
    return [{'type': 'enap_section', 'value': {
        'content': [
            {
                'type': 'enap_cardgrid',
                'value': {
                    'cards_per_row': '2',  # Default para "Até 2 cards"
                    'cards': [
                        {'type': 'enap_card', 'value': {
                            'titulo': 'Card Exemplo 1',
                            'descricao': 'Descrição do primeiro card'
                        }},
                        {'type': 'card_curso', 'value': {
                            'titulo': 'Card Curso Exemplo',
                            'descricao': 'Descrição do card de curso'
                        }}
                    ]
                }
            },
            {
                'type': 'aviso',
                'value': {
                    'titulo': 'Aviso Importante',
                    'conteudo': 'Conteúdo do aviso'
                }
            }
        ]
    }}]


class CursoEadPage(Page):
    """Template para Cursos EAD - ensino à distância"""
    
    template = 'enap_designsystem/pages/curso_ead.html'

    navbar = models.ForeignKey(
        "EnapNavbarSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    
    # Banner do curso
    banner_curso = StreamField([
        ("hero", HeroBlockv3()),
        ("enap_herobanner", EnapBannerBlock()),
    ], use_json_field=True, blank=True, default=get_default_banner_curso)
    
    # Apresentação do curso
    apresentacao_curso = StreamField([
        ("course_intro_topics", CourseIntroTopicsBlock()),
        ("feature_course", CourseFeatureBlock()),
    ], use_json_field=True, blank=True, default=get_default_apresentacao_curso)
    
    # Estrutura do curso/módulos
    estrutura_curso = StreamField([
        ("feature_estrutura", CourseModulesBlock()),
        ("section_tabs_cards", SectionTabsCardsBlock()),
    ], use_json_field=True, blank=True, default=get_default_estrutura_curso)
    
    # Por que escolher este curso
    vantagens = StreamField([
        ("why_choose", WhyChooseEnaptBlock()),
        ("feature_list", FeatureListBlock()),
    ], use_json_field=True, blank=True, default=get_default_vantagens)
    
    # Depoimentos de alunos
    depoimentos_alunos = StreamField([
        ("testimonials_carousel", TestimonialsCarouselBlock()),
    ], use_json_field=True, blank=True, default=get_default_depoimentos_alunos)
    
    # Cursos relacionados
    cursos_relacionados = StreamField([
        ("preview_courses", PreviewCoursesBlock()),
        ("carrossel_cursos", CarrosselCursosBlock()),
    ], use_json_field=True, blank=True, default=get_default_cursos_relacionados)
    
    # CTA de inscrição
    inscricao = StreamField([
        ("cta_2", CTA2Block()),
        ("secao_adesao", SecaoAdesaoBlock()),
    ], use_json_field=True, blank=True, default=get_default_inscricao)
    
    # FAQ do curso
    faq_curso = StreamField([
        ("accordion", AccordionItemBlock()),
    ], use_json_field=True, blank=True, default=get_default_faq_curso)

    # Campo adicional com todos os blocos disponíveis
    curso = StreamField([
        ("enap_section", EnapSectionBlock([
            ("enap_cardgrid", EnapCardGridBlock([
                ("enap_card", EnapCardBlock()),
                ('card_curso', CardCursoBlock()),
            ])),
            ('aviso', AvisoBlock()),
        ])),
    ], use_json_field=True, blank=True, default=get_default_curso)

    footer = models.ForeignKey(
        "EnapFooterSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    
    def save(self, *args, **kwargs):
        # Defaults já definidos nos StreamFields, método simplificado
        super().save(*args, **kwargs)
    
    content_panels = Page.content_panels + [
        FieldPanel('navbar'),
        FieldPanel('banner_curso'),
        FieldPanel('apresentacao_curso'),
        FieldPanel('estrutura_curso'),
        FieldPanel('vantagens'),
        FieldPanel('depoimentos_alunos'),
        FieldPanel('cursos_relacionados'),
        FieldPanel('inscricao'),
        FieldPanel('faq_curso'),
        FieldPanel('curso'),  # Campo adicional para blocos extras
        FieldPanel('footer'),
    ]

    class Meta:
        verbose_name = _("Enap Curso EAD")






class Contato(models.Model):
    nome = models.CharField('Nome', max_length=200)
    email = models.EmailField('Email')
    mensagem = models.TextField('Mensagem')
    data = models.DateTimeField('Data de Envio', auto_now_add=True)
    
    def __str__(self):
        return f"{self.nome} - {self.data.strftime('%d/%m/%Y')}"
    
    class Meta:
        verbose_name = "Contato"
        verbose_name_plural = "Contatos"
        ordering = ['-data']





@register_snippet
class FormularioSnippet(models.Model):
    """Formulário configurável como snippet"""
    nome = models.CharField('Nome do Formulário', max_length=100)
    titulo = models.CharField('Título', max_length=200, blank=True)
    descricao = models.TextField('Descrição', blank=True)
    email_destino = models.EmailField('Email de Destino')
    ativo = models.BooleanField('Ativo', default=True)
    
    panels = [
        FieldPanel('nome'),
        FieldPanel('titulo'),
        FieldPanel('descricao'),
        FieldPanel('email_destino'),
        FieldPanel('ativo'),
    ]
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = "Formulário"
        verbose_name_plural = "Formulários"


@register_snippet
class RespostaFormulario(models.Model):
    """Respostas dos formulários"""
    formulario = models.ForeignKey(
        FormularioSnippet,  # <- DEVE SER FormularioSnippet, NÃO FormularioContato
        on_delete=models.CASCADE, 
        related_name='respostas'
    )
    nome = models.CharField('Nome', max_length=200)
    email = models.EmailField('Email')
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    assunto = models.CharField('Assunto', max_length=200)
    mensagem = models.TextField('Mensagem')
    data = models.DateTimeField('Data de Envio', auto_now_add=True)
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    
    def __str__(self):
        return f"{self.nome} - {self.formulario.nome}"
    
    class Meta:
        verbose_name = "Resposta Formulário"
        verbose_name_plural = "Respostas Formulários"
        ordering = ['-data']






@register_snippet
class ChatbotConfig(models.Model):
    """Configurações do chatbot"""
    nome = models.CharField(max_length=100, default="Assistente ENAP")
    mensagem_boas_vindas = models.TextField(
        default="Olá! Sou o assistente virtual da ENAP. Como posso ajudar você hoje?"
    )
    prompt_sistema = models.TextField(
        default="""Você é um assistente virtual da ENAP (Escola Nacional de Administração Pública). 
        Responda perguntas sobre os conteúdos do portal de forma clara e objetiva. 
        Sempre indique links relevantes quando disponíveis."""
    )
    api_key_google = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="API Key do Google AI Studio"
    )
    modelo_ia = models.CharField(
        max_length=50, 
        choices=[
            ('gemini-1.5-flash', 'Gemini 1.5 Flash'),
            ('gemini-1.5-pro', 'Gemini 1.5 Pro'),
            ('gemini-pro', 'Gemini Pro'),
        ],
        default='gemini-1.5-flash'
    )
    ativo = models.BooleanField(default=True)

    panels = [
        FieldPanel('nome'),
        FieldPanel('mensagem_boas_vindas'),
        FieldPanel('prompt_sistema'),
        FieldPanel('api_key_google'),
        FieldPanel('modelo_ia'),
        FieldPanel('ativo'),
    ]

    class Meta:
        verbose_name = "Configuração do Chatbot"
        verbose_name_plural = "Configurações do Chatbot"

    def __str__(self):
        return f"Chatbot: {self.nome}"


@register_snippet
class ChatbotWidget(models.Model):
    """Widget visual do chatbot"""
    nome = models.CharField(max_length=100)
    titulo_widget = models.CharField(max_length=200, default="Assistente Virtual ENAP")
    cor_primaria = models.CharField(
        max_length=7, 
        default="#0066cc", 
        help_text="Cor em hex (#000000)"
    )
    cor_secundaria = models.CharField(
        max_length=7, 
        default="#ffffff", 
        help_text="Cor em hex (#ffffff)"
    )
    posicao = models.CharField(
        max_length=20,
        choices=[
            ('bottom-right', 'Inferior Direito'),
            ('bottom-left', 'Inferior Esquerdo'),
            ('top-right', 'Superior Direito'),
            ('top-left', 'Superior Esquerdo'),
        ],
        default='bottom-right'
    )
    icone_chatbot = models.CharField(
        max_length=50,
        choices=[
            ('💬', 'Balão de conversa'),
            ('🤖', 'Robô'),
            ('💭', 'Balão de pensamento'),
            ('📞', 'Telefone'),
            ('❓', 'Interrogação'),
        ],
        default='🤖'
    )
    mostrar_em_mobile = models.BooleanField(default=True)
    ativo = models.BooleanField(default=True)

    panels = [
        FieldPanel('nome'),
        FieldPanel('titulo_widget'),
        FieldPanel('cor_primaria'),
        FieldPanel('cor_secundaria'),
        FieldPanel('posicao'),
        FieldPanel('icone_chatbot'),
        FieldPanel('mostrar_em_mobile'),
        FieldPanel('ativo'),
    ]

    class Meta:
        verbose_name = "Widget do Chatbot"
        verbose_name_plural = "Widgets do Chatbot"

    def __str__(self):
        return self.nome


class PaginaIndexada(models.Model):
    """Páginas indexadas para o chatbot"""
    pagina = models.ForeignKey(
        'wagtailcore.Page',
        on_delete=models.CASCADE,
        related_name='indexacao_chatbot'
    )
    titulo = models.CharField(max_length=500)
    conteudo_texto = models.TextField()
    url = models.URLField()
    tags = models.TextField(blank=True)  # JSON com tags/palavras-chave
    data_indexacao = models.DateTimeField(auto_now=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Página Indexada"
        verbose_name_plural = "Páginas Indexadas"
        unique_together = ['pagina']

    def __str__(self):
        return f"Indexada: {self.titulo}"


class ConversaChatbot(models.Model):
    """Conversas do chatbot"""
    sessao_id = models.CharField(max_length=100)
    usuario_ip = models.GenericIPAddressField(blank=True, null=True)
    mensagem_usuario = models.TextField()
    resposta_bot = models.TextField()
    paginas_referenciadas = models.TextField(blank=True)  # JSON com links
    data_conversa = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Conversa do Chatbot"
        verbose_name_plural = "Conversas do Chatbot"

    def __str__(self):
        return f"Conversa {self.sessao_id[:8]} - {self.data_conversa.strftime('%d/%m/%Y %H:%M')}"
	






class CartaService(Page):
    
    template = 'enap_designsystem/pages/carta_servico.html'

    navbar = models.ForeignKey(
        "EnapNavbarSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    footer = models.ForeignKey(
        "EnapFooterSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    content_panels = Page.content_panels + [
        FieldPanel('navbar'),
        FieldPanel('footer'),
    ]

    class Meta:
        verbose_name = ("Carta de Serviço")






class ENAPService(Page):
	"""Página personalizada independente do CoderedWebPage."""
	
	admin_notes = models.TextField(
		verbose_name="Anotações Internas",
		blank=True,
		help_text="Escreva observações importantes. Este campo é visível apenas para administradores."
	)

	template = "enap_designsystem/pages/enap_layout.html"

	body = StreamField(
		LAYOUT_STREAMBLOCKS,
		null=True,
		blank=True,
		use_json_field=True,
	)

	navbar = models.ForeignKey(
		"EnapNavbarSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	footer = models.ForeignKey(
		"EnapFooterSnippet",
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="+",
	)

	content_panels = Page.content_panels + [
		FieldPanel("navbar"),
		FieldPanel("body"),
		FieldPanel("footer"),
		FieldPanel("admin_notes"),
	]

	@property
	def url_filter(self):
		"""URL do serviço para busca"""
		if hasattr(self, 'full_url') and self.full_url:
			return self.full_url
		return self.get_url_parts()[2] if self.get_url_parts() else ""
	
	@property
	def titulo_filter(self):
		"""Título extraído do hero banner ou title da página"""
		for block in self.body:
			if block.block_type == "enap_herobanner":
				titulo_hero = block.value.get("title", "")
				if titulo_hero:
					return titulo_hero
		return self.title  # Fallback para o título da página
	
	@property
	def descricao_filter(self):
		"""Descrição extraída do hero banner ou search_description"""
		for block in self.body:
			if block.block_type == "enap_herobanner":
				desc = block.value.get("description", "")
				if desc:
					if hasattr(desc, "source"):
						return strip_tags(desc.source).strip()
					return strip_tags(str(desc)).strip()
		
		# Fallback para search_description
		if self.search_description:
			return self.search_description
		
		return ""

	@property
	def data_atualizacao_filter(self):
		"""Data de atualização para ordenação"""
		return self.last_published_at or self.latest_revision_created_at

	@property
	def data_publicacao_filter(self):
		"""Data de publicação para ordenação"""
		return self.first_published_at

	@property
	def categoria(self):
		"""Categoria do serviço"""
		return "Serviços"
	
	@property
	def imagem_filter(self):
		"""Imagem principal extraída dos blocos"""
		tipos_com_imagem = [
			("enap_herobanner", "background_image"),
			("bannertopics", "imagem_fundo"),
			("banner_image_cta", "hero_image"),
			("hero", "background_image"),
			("banner_search", "imagem_principal"),
		]

		try:
			for bloco in self.body:
				for tipo, campo_imagem in tipos_com_imagem:
					if bloco.block_type == tipo:
						imagem = bloco.value.get(campo_imagem)
						if imagem:
							return imagem.file.url
		except Exception:
			pass

		return ""
	
	@property
	def texto_unificado(self):
		"""Texto completo para busca textual"""
		def extract_text_from_block(block_value):
			result = []

			if isinstance(block_value, list):
				for subblock in block_value:
					result.extend(extract_text_from_block(subblock))
			elif hasattr(block_value, "get"):  # StructValue
				for key, val in block_value.items():
					result.extend(extract_text_from_block(val))
			elif isinstance(block_value, str):
				cleaned = strip_tags(block_value).strip()
				if cleaned and cleaned.lower() not in {
					"default", "tipo terciário", "tipo secundário", "tipo bg image",
					"bg-gray", "bg-blue", "bg-white", "fundo cinza", "fundo branco"
				}:
					result.append(cleaned)
			elif hasattr(block_value, "source"):  # RichText
				cleaned = strip_tags(block_value.source).strip()
				if cleaned:
					result.append(cleaned)

			return result

		textos = []
		if hasattr(self, "body") and self.body:
			for block in self.body:
				textos.extend(extract_text_from_block(block.value))

		# Junta tudo em uma string e remove quebras de linha duplicadas
		texto_final = " ".join([t for t in textos if t])
		texto_final = re.sub(r"\s+", " ", texto_final).strip()
		return texto_final

	# ✅ Search fields seguindo o padrão de notícias
	search_fields = Page.search_fields + [
		index.SearchField("title", boost=3),
		index.SearchField("titulo_filter", name="titulo"),
		index.SearchField("descricao_filter", name="descricao"),
		index.FilterField("categoria", name="categoria_filter"),
		index.SearchField("url_filter", name="url"),
		index.FilterField("data_atualizacao_filter", name="data_atualizacao"),
		index.FilterField("data_publicacao_filter", name="data_publicacao"),
		index.SearchField("imagem_filter", name="imagem"),
		index.SearchField("texto_unificado", name="body"),
	]

	class Meta:
		verbose_name = "serviços Enap"
		verbose_name_plural = "serviços Enap"






class LiaPage(Page):
	
    page_title = models.CharField(
        max_length=255, 
        default="Título Padrão", 
        verbose_name="Título da Página",
		blank=False, 
    )

    template = "enap_designsystem/blocks/page/lia.html"


    body = RichTextField(
        blank=True, 
        verbose_name="Título da sessão: O que é IA"
    )
    paragrafo = RichTextField(
        blank=True, 
        help_text="Adicione o texto do parágrafo aqui.", 
        verbose_name="Parágrafo card: O que é IA?"
    )
    
    video_background = models.FileField(
        upload_to='media/imagens', 
        null=True, 
        blank=True, 
        verbose_name="Vídeo de Fundo"
    )

    # Painéis no admin do Wagtail
    content_panels = Page.content_panels + [
        FieldPanel('page_title'),
        FieldPanel('body'),
        FieldPanel('paragrafo'),
        FieldPanel('video_background'),
    ]








# seo_models.py - Implementação manual de SEO para Wagtail
from django.db import models
from django.utils.html import strip_tags
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField
import re

class SEOMixin(models.Model):
    """
    Mixin para adicionar funcionalidades de SEO a qualquer página Wagtail
    Compatível com páginas existentes - não quebra nada!
    """
    
    # Campos SEO opcionais
    seo_title = models.CharField(
        max_length=60,
        blank=True,
        help_text="Título para SEO (máx. 60 caracteres). Se vazio, usa o título da página."
    )
    
    meta_description = models.TextField(
        max_length=160,
        blank=True,
        help_text="Descrição para SEO (máx. 160 caracteres). Se vazio, gera automaticamente."
    )
    
    og_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Imagem para redes sociais (1200x630px recomendado)"
    )
    
    # Propriedades que funcionam automaticamente
    @property
    def get_meta_title(self):
        """Retorna título para SEO ou título da página"""
        return self.seo_title or self.title
    
    @property
    def get_meta_description(self):
        """Retorna descrição para SEO ou gera automaticamente"""
        if self.meta_description:
            return self.meta_description
        
        # Auto-gerar a partir do conteúdo da página
        return self._generate_auto_description()
    
    @property
    def get_og_image(self):
        """Retorna imagem para Open Graph"""
        if self.og_image:
            return self.og_image
        
        # Tenta encontrar primeira imagem no conteúdo
        return self._find_first_image()
    
    def _generate_auto_description(self):
        """Gera descrição automaticamente a partir do conteúdo"""
        description_sources = []
        
        # Tenta várias fontes de conteúdo
        content_fields = ['body', 'content', 'introduction', 'summary', 'description']
        
        for field_name in content_fields:
            if hasattr(self, field_name):
                field_value = getattr(self, field_name)
                if field_value:
                    if hasattr(field_value, 'source'):  # RichTextField
                        text = strip_tags(field_value.source)
                    else:
                        text = strip_tags(str(field_value))
                    
                    if text.strip():
                        description_sources.append(text.strip())
        
        if description_sources:
            # Pega o primeiro conteúdo encontrado
            full_text = description_sources[0]
            # Remove quebras de linha extras e espaços
            clean_text = re.sub(r'\s+', ' ', full_text).strip()
            # Corta em 160 caracteres
            if len(clean_text) > 160:
                return clean_text[:157] + '...'
            return clean_text
        
        # Fallback padrão
        return f"Conheça mais sobre {self.title} na ENAP - Escola Nacional de Administração Pública."
    
    def _find_first_image(self):
        """Encontra primeira imagem no conteúdo para Open Graph"""
        content_fields = ['body', 'content']
        
        for field_name in content_fields:
            if hasattr(self, field_name):
                field_value = getattr(self, field_name)
                if hasattr(field_value, 'stream_data'):  # StreamField
                    for block_data in field_value.stream_data:
                        if block_data.get('type') == 'image' and block_data.get('value'):
                            try:
                                from wagtail.images import get_image_model
                                Image = get_image_model()
                                return Image.objects.get(id=block_data['value'])
                            except:
                                continue
        return None
    
    # Painéis para o admin do Wagtail
    seo_panels = [
        MultiFieldPanel([
            FieldPanel('seo_title'),
            FieldPanel('meta_description'),
            FieldPanel('og_image'),
        ], heading="SEO & Redes Sociais", classname="collapsible collapsed")
    ]
    
    class Meta:
        abstract = True


class OpenGraphMixin(models.Model):
    """
    Mixin adicional para Open Graph completo
    Use junto com SEOMixin se precisar de mais controle
    """
    
    og_title = models.CharField(
        max_length=60,
        blank=True,
        help_text="Título para redes sociais (se diferente do SEO)"
    )
    
    og_description = models.TextField(
        max_length=160,
        blank=True,
        help_text="Descrição para redes sociais (se diferente do SEO)"
    )
    
    twitter_card_type = models.CharField(
        max_length=20,
        choices=[
            ('summary', 'Summary'),
            ('summary_large_image', 'Summary Large Image'),
            ('app', 'App'),
            ('player', 'Player'),
        ],
        default='summary_large_image',
        help_text="Tipo de card do Twitter"
    )
    
    @property
    def get_og_title(self):
        return self.og_title or self.get_meta_title
    
    @property
    def get_og_description(self):
        return self.og_description or self.get_meta_description
    
    # Painéis adicionais
    og_panels = [
        MultiFieldPanel([
            FieldPanel('og_title'),
            FieldPanel('og_description'),
            FieldPanel('twitter_card_type'),
        ], heading="Open Graph Avançado", classname="collapsible collapsed")
    ]
    
    class Meta:
        abstract = True


# Classe combinada para uso mais fácil
class FullSEOMixin(SEOMixin, OpenGraphMixin):
    """
    Mixin completo com todas as funcionalidades de SEO
    """
    
    @property
    def all_seo_panels(self):
        return self.seo_panels + self.og_panels
    
    class Meta:
        abstract = True







@register_snippet
class FormularioDinamicoSubmission(models.Model):
    """
    Modelo para submissões do FormularioDinâmico
    Pode ser usado em qualquer página
    """
    # Referência genérica para qualquer página
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    page = GenericForeignKey('content_type', 'object_id')
    
    # Dados da submissão (mesmo formato do FormularioSubmission)
    form_data = models.JSONField(verbose_name="Dados do formulário", default=dict)
    files_data = models.JSONField(verbose_name="Metadados dos arquivos", default=dict)
    uploaded_files = models.JSONField(
        verbose_name="Caminhos dos arquivos salvos", 
        default=dict,
        help_text="Caminhos onde os arquivos foram salvos no sistema"
    )
    
    # Metadados (mesmo formato)
    submit_time = models.DateTimeField(auto_now_add=True)
    user_ip = models.GenericIPAddressField(verbose_name="IP do usuário", null=True, blank=True)
    user_agent = models.TextField(verbose_name="User Agent", blank=True)
    
    # Campos extraídos automaticamente para facilitar consultas e exportação
    user_name = models.CharField(max_length=200, blank=True, verbose_name="Nome")
    user_email = models.EmailField(blank=True, verbose_name="E-mail")
    user_phone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    page_title = models.CharField(max_length=200, blank=True, verbose_name="Título da Página")
    
    class Meta:
        verbose_name = "Submissão de Formulário Dinâmico"
        verbose_name_plural = "Submissões de Formulários Dinâmicos"
        ordering = ['-submit_time']

    def __str__(self):
        nome = self.user_name or "Anônimo"
        return f"{nome} - {self.page_title} - {self.submit_time.strftime('%d/%m/%Y %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Extrair informações automaticamente dos dados do formulário
        if self.form_data:
            self.extract_user_info()
        
        # Extrair título da página
        if hasattr(self.page, 'title'):
            self.page_title = self.page.title
        
        super().save(*args, **kwargs)
    
    def extract_user_info(self):
        """Extrai informações do usuário dos dados do formulário"""
        for field_name, value in self.form_data.items():
            if not value:
                continue
                
            field_lower = field_name.lower()
            
            # Detectar nome
            if any(keyword in field_lower for keyword in ['nome', 'name']) and not self.user_name:
                self.user_name = str(value)[:200]
            
            # Detectar email
            elif 'email' in field_lower and not self.user_email:
                self.user_email = str(value)[:254]
            
            # Detectar telefone
            elif any(keyword in field_lower for keyword in ['telefone', 'phone', 'celular']) and not self.user_phone:
                self.user_phone = str(value)[:20]
    
    def get_readable_data(self):
        """Retorna dados em formato legível (mesmo método do FormularioSubmission)"""
        readable = {}
        for key, value in self.form_data.items():
            if isinstance(value, list):
                readable[key] = ', '.join(str(v) for v in value)
            else:
                readable[key] = str(value)
        return readable
	






@receiver(pre_delete, sender=FormularioDinamicoSubmission)
def delete_dynamic_submission_files(sender, instance, **kwargs):
    """Deleta arquivos quando submissão é deletada"""
    page_id = instance.object_id
    submission_folder = os.path.join(
        settings.MEDIA_ROOT, 
        'formularios', 
        f'page_{page_id}', 
        f'submission_{instance.id}'
    )
    
    if os.path.exists(submission_folder):
        shutil.rmtree(submission_folder)
        print(f"🗑️ Pasta deletada: {submission_folder}")

@receiver(pre_delete, sender=FormularioPage)
def delete_form_page_files(sender, instance, **kwargs):
    """Deleta TODOS os arquivos quando formulário é deletado"""
    form_folder = os.path.join(
        settings.MEDIA_ROOT, 
        'formularios', 
        f'page_{instance.id}'
    )
    
    if os.path.exists(form_folder):
        shutil.rmtree(form_folder)
        print(f"🗑️ FORMULÁRIO DELETADO: {form_folder}")













@register_snippet
class GroupPageTypePermission(models.Model):
    """
    Modelo para controlar quais tipos de página cada grupo pode acessar
    Registrado como snippet para fácil gerenciamento no admin
    """
    group = models.OneToOneField(
        Group, 
        on_delete=models.CASCADE,
        related_name='page_type_permissions',
        verbose_name='Grupo'
    )
    content_types = models.ManyToManyField(
        ContentType, 
        verbose_name='Tipos de Página Permitidos',
        help_text='Selecione todos os tipos de página que este grupo pode acessar',
        blank=True
    )
    
    panels = [
        FieldPanel('group'),
        FieldPanel('content_types'),
    ]
    
    class Meta:
        verbose_name = 'Permissão de Tipos de Página por Grupo'
        verbose_name_plural = 'Permissões de Tipos de Página por Grupo'
    
    def __str__(self):
        count = self.content_types.count()
        if count == 0:
            return f"{self.group.name} → Nenhum tipo permitido"
        elif count == 1:
            return f"{self.group.name} → {self.content_types.first().name}"
        else:
            return f"{self.group.name} → {count} tipos permitidos"

    @classmethod
    def get_allowed_page_types_for_user(cls, user):
        """
        Retorna os tipos de página que um usuário pode acessar
        """
        if user.is_superuser:
            return Page.get_page_types()
        
        user_groups = user.groups.all()
        allowed_types = set()
        
        for group in user_groups:
            try:
                permission = cls.objects.get(group=group)
                group_types = [ct.model_class() for ct in permission.content_types.all() if ct.model_class()]
                allowed_types.update(group_types)
            except cls.DoesNotExist:
                # Grupo não tem permissões configuradas
                continue
        
        return list(allowed_types) if allowed_types else []
    
    def get_allowed_content_types(self):
        """
        Retorna apenas ContentTypes que são páginas Wagtail válidas
        """
        page_content_types = []
        for ct in ContentType.objects.all():
            try:
                model_class = ct.model_class()
                if (model_class and 
                    issubclass(model_class, Page) and 
                    model_class != Page and
                    not model_class._meta.abstract):
                    page_content_types.append(ct)
            except:
                pass
        return page_content_types

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Após salvar, filtrar apenas ContentTypes válidos
        valid_content_types = self.get_allowed_content_types()
        self.content_types.set([ct for ct in self.content_types.all() if ct in valid_content_types])











@register_snippet
class CategoriaVotacao(models.Model):
    """
    Categorias/Tabs do sistema de votação
    Gerenciadas dinamicamente pelo admin
    """
    nome = models.CharField(
        max_length=100,
        verbose_name="Nome da Categoria",
        help_text="Ex: Inovação Tecnológica, Sustentabilidade, etc."
    )
    
    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição",
        help_text="Descrição opcional da categoria"
    )
    
    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordem de Exibição",
        help_text="Ordem das tabs (menor número = primeiro)"
    )
    
    ativo = models.BooleanField(
        default=True,
        verbose_name="Categoria Ativa",
        help_text="Desmarque para ocultar esta categoria"
    )
    
    icone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Ícone (classe CSS)",
        help_text="Ex: fa-microchip, fa-leaf, fa-users"
    )
    
    cor_destaque = models.CharField(
        max_length=7,
        default="#00E5CC",
        verbose_name="Cor de Destaque",
        help_text="Cor hexadecimal para esta categoria"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoria de Votação"
        verbose_name_plural = "Categorias de Votação"
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome

    @property
    def total_projetos(self):
        """Retorna total de projetos ativos nesta categoria"""
        return self.projetos.filter(ativo=True).count()

    @property
    def total_votos(self):
        """Retorna total de votos recebidos nesta categoria"""
        return VotoRegistrado.objects.filter(
            projeto__categoria=self,
            projeto__ativo=True
        ).count()


@register_snippet  
class ProjetoVotacao(ClusterableModel):
    """
    Projetos participantes da votação
    Cards dinâmicos configuráveis pelo admin
    """
    titulo = models.CharField(
        max_length=200,
        verbose_name="Título do Projeto"
    )
    
    descricao = RichTextField(
        verbose_name="Descrição do Projeto",
        help_text="Descrição completa do projeto"
    )
    
    categoria = models.ForeignKey(
        CategoriaVotacao,
        on_delete=models.CASCADE,
        related_name='projetos',
        verbose_name="Categoria"
    )
    
    # Equipe
    nome_equipe = models.CharField(
        max_length=150,
        verbose_name="Nome da Equipe/Organização"
    )
    
    icone_equipe = models.ImageField(
        upload_to='votacao/equipes/',
        blank=True,
        null=True,
        verbose_name="Logo/Ícone da Equipe"
    )
    
    # Vídeo
    video_youtube = models.URLField(
        blank=True,
        verbose_name="URL do Vídeo YouTube",
        help_text="Cole a URL completa do YouTube"
    )
    
    video_arquivo = models.FileField(
        upload_to='votacao/videos/',
        blank=True,
        null=True,
        verbose_name="Arquivo de Vídeo",
        help_text="Alternativamente, faça upload de um vídeo"
    )
    
    # Contato
    email_contato = models.EmailField(
        blank=True,
        verbose_name="Email de Contato",
        help_text="Email da equipe (opcional)"
    )
    
    # Configurações
    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordem na Categoria",
        help_text="Ordem do projeto dentro da categoria"
    )
    
    ativo = models.BooleanField(
        default=True,
        verbose_name="Projeto Ativo",
        help_text="Desmarque para ocultar este projeto"
    )
    
    destacado = models.BooleanField(
        default=False,
        verbose_name="Projeto em Destaque",
        help_text="Marque para destacar este projeto"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        MultiFieldPanel([
            FieldPanel('titulo'),
            FieldPanel('categoria'),
            FieldPanel('descricao'),
        ], heading="Informações Básicas"),
        
        MultiFieldPanel([
            FieldPanel('nome_equipe'),
            FieldPanel('icone_equipe'),
            FieldPanel('email_contato'),
            InlinePanel('apresentadores', label="Apresentadores"),
        ], heading="Equipe"),
        
        MultiFieldPanel([
            FieldPanel('video_youtube'),
            FieldPanel('video_arquivo'),
        ], heading="Vídeo do Projeto"),
        
        MultiFieldPanel([
            FieldPanel('ordem'),
            FieldPanel('ativo'),
            FieldPanel('destacado'),
        ], heading="Configurações"),
    ]

    class Meta:
        verbose_name = "Projeto de Votação"
        verbose_name_plural = "Projetos de Votação"
        ordering = ['categoria__ordem', 'ordem', 'titulo']

    def __str__(self):
        return f"{self.titulo} ({self.categoria.nome})"

    @property
    def total_votos(self):
        """Retorna total de votos recebidos por este projeto"""
        return self.votos.count()

    @property
    def video_embed_url(self):
        """Converte URL do YouTube para embed"""
        if self.video_youtube:
            if "youtube.com/watch?v=" in self.video_youtube:
                video_id = self.video_youtube.split("watch?v=")[1].split("&")[0]
                return f"https://www.youtube.com/embed/{video_id}"
            elif "youtu.be/" in self.video_youtube:
                video_id = self.video_youtube.split("youtu.be/")[1].split("?")[0]
                return f"https://www.youtube.com/embed/{video_id}"
        return None

    def get_apresentadores_list(self):
        """Retorna lista de apresentadores como badges"""
        return [ap.nome for ap in self.apresentadores.all()]


class ApresentadorProjeto(Orderable):
    """
    Apresentadores de cada projeto
    Inline para criar badges dinâmicas
    """
    projeto = ParentalKey(
        ProjetoVotacao,
        related_name='apresentadores',
        on_delete=models.CASCADE
    )
    
    nome = models.CharField(
        max_length=100,
        verbose_name="Nome do Apresentador"
    )
    
    cargo = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Cargo/Função",
        help_text="Ex: Desenvolvedor, Designer, etc."
    )

    panels = [
        FieldPanel('nome'),
        FieldPanel('cargo'),
    ]

    def __str__(self):
        return self.nome


class VotoRegistrado(models.Model):
    """
    Registro de cada voto realizado
    Para auditoria e controle básico anti-fraude
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    projeto = models.ForeignKey(
        ProjetoVotacao,
        on_delete=models.CASCADE,
        related_name='votos',
        verbose_name="Projeto Votado"
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name="Endereço IP"
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent",
        help_text="Navegador utilizado"
    )
    
    timestamp = models.DateTimeField(
        default=timezone.now,
        verbose_name="Data/Hora do Voto"
    )
    
    # Campos para relatórios
    categoria_nome = models.CharField(
        max_length=100,
        verbose_name="Nome da Categoria",
        help_text="Cache do nome da categoria no momento do voto"
    )

    class Meta:
        verbose_name = "Voto Registrado"
        verbose_name_plural = "Votos Registrados"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['projeto', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['categoria_nome', 'timestamp']),
        ]

    def __str__(self):
        return f"Voto em {self.projeto.titulo} - {self.timestamp}"

    def save(self, *args, **kwargs):
        # Cache do nome da categoria
        if not self.categoria_nome:
            self.categoria_nome = self.projeto.categoria.nome
        super().save(*args, **kwargs)



class SistemaVotacaoPage(Page):
    """
    Página principal do sistema de votação
    Configurações gerais editáveis pelo admin
    """

    navbar = models.ForeignKey(
        "EnapNavbarSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    background_image_fundo = StreamField(
        [('background_image_stream', ImageChooserBlock(
            label="Imagem de Fundo",
            help_text="Selecione uma imagem de fundo para o formulário"
        ))],
        verbose_name="Imagem de Fundo",
        use_json_field=True,
        max_num=1,
        blank=True,
        help_text="Adicione uma imagem de fundo para o formulário"
    )

    subtitulo = models.CharField(
        max_length=255,
        default="Escolha os melhores projetos em cada categoria",
        verbose_name="Subtítulo",
        help_text="Texto que aparece abaixo do título"
    )
    
    descricao_header = RichTextField(
        blank=True,
        verbose_name="Descrição do Header",
        help_text="Texto adicional no topo da página (opcional)"
    )

    # Campos para reCAPTCHA
    texto_pre_recaptcha = RichTextField(
        default="<p>Para acessar o sistema de votação, confirme que você não é um robô:</p>",
        verbose_name="Texto antes do reCAPTCHA",
        help_text="Mensagem exibida antes da verificação do reCAPTCHA"
    )

    texto_pos_recaptcha = RichTextField(
        blank=True,
        verbose_name="Texto após verificação",
        help_text="Mensagem exibida após verificação bem-sucedida (opcional)"
    )

    exigir_recaptcha = models.BooleanField(
        default=True,
        verbose_name="Exigir reCAPTCHA",
        help_text="Marque para exigir verificação reCAPTCHA antes de mostrar votação"
    )

    imagem_fundo = StreamField([
        ("image", ImageChooserBlock(
            required=False,
            help_text="Selecione uma imagem para usar como fundo da página"
        ))
    ], 
    blank=True, 
    use_json_field=True, 
    verbose_name="Imagem de Fundo",
    )

    conteudo_pagina = StreamField([
        ('secao_apresentacao', SecaoApresentacaoBlock()),
    ], 
    blank=True, 
    use_json_field=True, 
    verbose_name="Conteúdo da Página",
    help_text="Adicione seções de conteúdo para a página"
    )
    
    mostrar_progresso = models.BooleanField(
        default=True,
        verbose_name="Mostrar Barra de Progresso",
        help_text="Exibe progresso de quantas categorias o usuário votou"
    )
    
    permitir_multiplos_votos = models.BooleanField(
        default=True,
        verbose_name="Permitir Múltiplos Votos",
        help_text="Usuário pode votar em diferentes projetos de diferentes categorias"
    )
    
    ordenacao_projetos = models.CharField(
        max_length=20,
        choices=[
            ('ordem', 'Ordem Manual'),
            ('votos_desc', 'Mais Votados Primeiro'),
            ('votos_asc', 'Menos Votados Primeiro'),
            ('alfabetica', 'Ordem Alfabética'),
            ('recentes', 'Mais Recentes Primeiro'),
        ],
        default='ordem',
        verbose_name="Ordenação dos Projetos"
    )
    
    votacao_ativa = models.BooleanField(
        default=True,
        verbose_name="Votação Ativa",
        help_text="Desmarque para pausar a votação"
    )
    
    data_inicio = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data de Início",
        help_text="Data/hora de início da votação (opcional)"
    )
    
    data_fim = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data de Encerramento", 
        help_text="Data/hora de encerramento da votação (opcional)"
    )

    configuracoes_votacao = StreamField([
        ('recaptcha', RecaptchaBlock()),
    ], 
    blank=True,
    use_json_field=True,
    verbose_name="Configurações e Elementos da Votação",
    help_text="Adicione reCAPTCHA para a página de votação"
    )

    footer = models.ForeignKey(
        "EnapFooterSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('subtitulo'),
            FieldPanel('descricao_header'),
            FieldPanel('imagem_fundo'),
            FieldPanel('navbar'),
            FieldPanel('footer'),
            FieldPanel('background_image_fundo'),
        ], heading="Conteúdo do Header"),

        # Nova seção para reCAPTCHA
        MultiFieldPanel([
            FieldPanel('exigir_recaptcha'),
            FieldPanel('texto_pre_recaptcha'),
            FieldPanel('texto_pos_recaptcha'),
        ], heading="Configurações do reCAPTCHA"),

        FieldPanel('conteudo_pagina'),
        FieldPanel('configuracoes_votacao'),
        
        MultiFieldPanel([
            FieldPanel('mostrar_progresso'),
            FieldPanel('permitir_multiplos_votos'),
            FieldPanel('ordenacao_projetos'),
        ], heading="Configurações de Exibição"),
        
        MultiFieldPanel([
            FieldPanel('votacao_ativa'),
            FieldPanel('data_inicio'),
            FieldPanel('data_fim'),
        ], heading="Controle da Votação"),
    ]

    class Meta:
        verbose_name = "Sistema de Votação"

    def get_context(self, request):
        context = super().get_context(request)
		
		# Adicionar configuração do reCAPTCHA ao contexto
        context.update({
        'exigir_recaptcha': self.exigir_recaptcha,
        'recaptcha_config': {
            'tema': 'light',
            'tamanho': 'normal',
            'css_classes': 'text-center my-4'
        }
        })
		
		# SEMPRE carregar dados de votação (sem verificação de reCAPTCHA)
        print("✅ Carregando dados de votação...")
		
		# Buscar categorias ativas
        categorias = CategoriaVotacao.objects.filter(ativo=True).order_by('ordem')
		
		# Buscar projetos por categoria
        projetos_por_categoria = {}
        for categoria in categorias:
            projetos = categoria.projetos.filter(ativo=True)
			
			# Aplicar ordenação
            if self.ordenacao_projetos == 'votos_desc':
                projetos = sorted(projetos, key=lambda p: p.total_votos, reverse=True)
            elif self.ordenacao_projetos == 'votos_asc':
                projetos = sorted(projetos, key=lambda p: p.total_votos)
            elif self.ordenacao_projetos == 'alfabetica':
                projetos = projetos.order_by('titulo')
            elif self.ordenacao_projetos == 'recentes':
                projetos = projetos.order_by('-created_at')
            else:  # 'ordem'
                projetos = projetos.order_by('ordem', 'titulo')
			
            projetos_por_categoria[categoria] = projetos
		
		# Estatísticas gerais
        total_categorias = categorias.count()
        total_projetos = ProjetoVotacao.objects.filter(ativo=True).count()
        total_votos = VotoRegistrado.objects.count()
		
		# Adicionar todos os dados ao contexto
        context.update({
			'categorias': categorias,
			'projetos_por_categoria': projetos_por_categoria,
			'total_categorias': total_categorias,
			'total_projetos': total_projetos,
			'total_votos': total_votos,
		})
		
        context['votacao_ativa'] = self.is_votacao_ativa()
        return context

    def is_votacao_ativa(self):
        """Verifica se a votação está ativa baseado nas configurações"""
        if not self.votacao_ativa:
            return False
			
        from django.utils import timezone
        now = timezone.now()
		
        if self.data_inicio and now < self.data_inicio:
            return False
			
        if self.data_fim and now > self.data_fim:
            return False
        return True
	





@register_snippet
class FAQSnippet(models.Model):
    """Snippet de FAQ Temático - Reutilizável entre páginas"""
    
    titulo = models.CharField(
        _("Título do FAQ"),
        max_length=255,
        default="Perguntas Frequentes",
        help_text=_("Título principal do FAQ")
    )
    
    temas = StreamField([
        ('tema', TemaFAQBlock()),
    ], 
        blank=True,
        use_json_field=True,
        verbose_name=_("Temas do FAQ")
    )
    
    panels = [
        FieldPanel('titulo'),
        FieldPanel('temas'),
    ]
    
    def __str__(self):
        return self.titulo
    
    def get_searchable_content(self):
        """Torna o conteúdo do FAQ pesquisável"""
        content = [self.titulo]
        
        for tema_block in self.temas:
            if tema_block.block_type == 'tema':
                tema = tema_block.value
                content.append(tema.get("tema_titulo", ""))
                
                if tema.get("tema_descricao"):
                    content.append(tema["tema_descricao"].source)
                
                for accordion in tema.get("accordions", []):
                    if accordion.block_type == "accordion_item":
                        item = accordion.value
                        content.append(item.get("title", ""))
                        content.append(item.get("content", "").source if hasattr(item.get("content", ""), "source") else "")
        
        return content
    
    class Meta:
        verbose_name = _("FAQ")
        verbose_name_plural = _("FAQs")
        ordering = ['titulo']







import logging
import traceback
from wagtail.blocks import StreamBlock, StructBlock, ListBlock

logger = logging.getLogger(__name__)

class ShowcaseComponentesDireto(Page):
    """
    Showcase que renderiza componentes COMPLETOS visualmente
    """
    
    description = RichTextField(
        verbose_name="Descrição",
        help_text="Descrição da biblioteca de componentes",
        blank=True,
        default="Showcase visual dos componentes completos"
    )
    
    debug_mode = models.BooleanField(
        default=False,  # False por padrão para foco na estética
        verbose_name="Modo Debug",
        help_text="Ativar para ver informações técnicas"
    )
    
    show_errors_only = models.BooleanField(
        default=False,
        verbose_name="Mostrar Apenas Erros",
        help_text="Mostrar apenas componentes que falharam na renderização"
    )
    
    filter_category = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Filtrar Categoria",
        help_text="banners, galerias, carousels, dashboards, formularios, cursos, eventos, navegacao, botoes, conteudo, secoes, cards, interativos, midia, especialidades"
    )
    
    content_panels = Page.content_panels + [
        FieldPanel('description'),
        FieldPanel('filter_category'),
        FieldPanel('show_errors_only'),
        FieldPanel('debug_mode'),
    ]
    
    template = 'enap_designsystem/pages/showcase_components.html'
    
    class Meta:
        verbose_name = "Showcase Visual de Componentes"
        verbose_name_plural = "Showcases Visuais de Componentes"
    
    def get_context(self, request):
        context = super().get_context(request)
        debug_log = []
        
        try:
            # Importar LAYOUT_STREAMBLOCKS
            debug_log.append("Importando LAYOUT_STREAMBLOCKS...")
            
            try:
                from .blocks import LAYOUT_STREAMBLOCKS
                debug_log.append(f"✅ Importado: {len(LAYOUT_STREAMBLOCKS)} categorias")
            except Exception as e:
                debug_log.append(f"❌ Erro de import: {str(e)}")
                raise Exception(f"Erro ao importar LAYOUT_STREAMBLOCKS: {str(e)}")
            
            # Descobrir e renderizar componentes COMPLETOS
            categories_with_components = self.discover_and_render_complete_components(LAYOUT_STREAMBLOCKS, debug_log)
            
            # Aplicar filtros
            if self.filter_category:
                categories_with_components = {
                    k: v for k, v in categories_with_components.items() 
                    if k == self.filter_category
                }
                debug_log.append(f"Filtro aplicado: {self.filter_category}")
            
            if self.show_errors_only:
                filtered_categories = {}
                for cat_name, cat_data in categories_with_components.items():
                    error_components = [c for c in cat_data['rendered_components'] if c.get('has_error', False)]
                    if error_components:
                        cat_data_copy = cat_data.copy()
                        cat_data_copy['rendered_components'] = error_components
                        filtered_categories[cat_name] = cat_data_copy
                categories_with_components = filtered_categories
                debug_log.append("Filtro de erros aplicado")
            
            # Calcular estatísticas
            total_components = sum(len(cat['rendered_components']) for cat in categories_with_components.values())
            components_ok = sum(
                len([c for c in cat['rendered_components'] if not c.get('has_error', False)]) 
                for cat in categories_with_components.values()
            )
            components_error = total_components - components_ok
            
            context.update({
                'categories_with_components': categories_with_components,
                'total_components': total_components,
                'components_ok': components_ok,
                'components_error': components_error,
                'total_categories': len(categories_with_components),
                'page_title': 'Showcase Visual - Componentes ENAP',
                'page_description': 'Visualização estética dos componentes do Design System',
                'debug_log': debug_log if self.debug_mode else [],
                'debug_mode': self.debug_mode,
                'available_categories': [name for name, _ in LAYOUT_STREAMBLOCKS],
            })
            
        except Exception as e:
            debug_log.append(f"❌ ERRO GERAL: {str(e)}")
            debug_log.append(f"Traceback: {traceback.format_exc()}")
            logger.error(f"Erro no showcase: {e}", exc_info=True)
            
            context.update({
                'error_message': f'Erro ao carregar componentes: {str(e)}',
                'categories_with_components': {},
                'total_components': 0,
                'components_ok': 0,
                'components_error': 0,
                'total_categories': 0,
                'debug_log': debug_log,
                'debug_mode': self.debug_mode,
                'available_categories': [],
            })
            
        return context
    
    def discover_and_render_complete_components(self, layout_streamblocks, debug_log):
        """Descobre e renderiza componentes COMPLETOS, não os campos individuais"""
        categories = {}
        debug_log.append("\n=== DESCOBRINDO COMPONENTES COMPLETOS ===")
        
        for stream_name, stream_block in layout_streamblocks:
            debug_log.append(f"\nProcessando categoria: {stream_name}")
            
            # Pular categorias que são muito complexas ou não visuais
            if self.should_skip_category(stream_name):
                debug_log.append(f"  ⏭️ Pulando categoria complexa: {stream_name}")
                continue
            
            # Criar categoria
            category_info = {
                'name': stream_name,
                'display_name': self.format_category_name(stream_name),
                'icon': self.get_category_icon(stream_name),
                'description': self.get_category_description(stream_name),
                'rendered_components': []
            }
            
            # Extrair componentes da categoria
            if hasattr(stream_block, 'child_blocks') and stream_block.child_blocks:
                debug_log.append(f"  📦 Categoria com {len(stream_block.child_blocks)} componentes")
                
                for comp_name, comp_block in stream_block.child_blocks.items():
                    debug_log.append(f"    🔧 Renderizando: {comp_name}")
                    
                    # Renderizar o componente COMPLETO
                    rendered_comp = self.render_complete_component(
                        comp_name, comp_block, stream_name, debug_log
                    )
                    
                    if rendered_comp:
                        category_info['rendered_components'].append(rendered_comp)
                        status = "❌" if rendered_comp.get('has_error') else "✅"
                        debug_log.append(f"      {status} Adicionado")
                    else:
                        debug_log.append(f"      ❌ Falhou completamente")
            
            elif self.is_single_renderable_component(stream_block):
                # Se a categoria é um componente único
                debug_log.append(f"  🎯 Categoria é componente único")
                rendered_comp = self.render_complete_component(
                    stream_name, stream_block, stream_name, debug_log
                )
                if rendered_comp:
                    category_info['rendered_components'].append(rendered_comp)
            
            else:
                debug_log.append(f"  ⚠️ Categoria não processável: {stream_block.__class__.__name__}")
            
            # Adicionar categoria se tiver componentes
            if category_info['rendered_components']:
                categories[stream_name] = category_info
                debug_log.append(f"  ✅ Categoria adicionada com {len(category_info['rendered_components'])} componentes")
            else:
                debug_log.append(f"  ❌ Categoria ignorada (sem componentes)")
        
        debug_log.append(f"\n📊 TOTAL: {len(categories)} categorias processadas")
        return categories
    
    def should_skip_category(self, stream_name):
        """Determina se deve pular uma categoria"""
        skip_list = [
            'enap_section',  # Muito complexa
            'recaptcha',     # Não visual
        ]
        return stream_name in skip_list
    
    def is_single_renderable_component(self, block):
        """Verifica se o bloco é um componente único renderizável"""
        class_name = block.__class__.__name__
        
        # Se termina com Block e tem método render, é renderizável
        if class_name.endswith('Block') and hasattr(block, 'render'):
            return True
        
        return False
    
    def render_complete_component(self, comp_name, comp_block, category_name, debug_log):
        """Renderiza um componente COMPLETO com dados realistas"""
        try:
            debug_log.append(f"      🎨 Tipo: {comp_block.__class__.__name__}")
            
            component_data = self.generate_realistic_component_data(comp_name, comp_block, debug_log)
            
            try:
                if hasattr(comp_block, 'child_blocks'):
                    for field_name, field_block in comp_block.child_blocks.items():
                        if field_name in component_data:
                            field_type = field_block.__class__.__name__
                            value = component_data[field_name]
                            
                            if 'Stream' in field_type and not isinstance(value, list):
                                component_data[field_name] = []
                                debug_log.append(f"         🔧 Corrigido {field_name}: StreamBlock precisa de lista")
                            
                            elif 'List' in field_type and not isinstance(value, list):
                                component_data[field_name] = []
                                debug_log.append(f"         🔧 Corrigido {field_name}: ListBlock precisa de lista")
                            
                            elif 'Choice' in field_type and not isinstance(value, str):
                                component_data[field_name] = 'opcao1'
                                debug_log.append(f"         🔧 Corrigido {field_name}: ChoiceBlock precisa de string")
                            
                            elif 'RichText' in field_type and not isinstance(value, str):
                                component_data[field_name] = '<p>Texto exemplo</p>'
                                debug_log.append(f"         🔧 Corrigido {field_name}: RichText precisa de string")
            
            except Exception as validation_error:
                debug_log.append(f"         ⚠️ Erro na validação: {str(validation_error)}")
                component_data = {}
            
            rendered_html = None
            render_error = None

            try:
                debug_log.append(f"      🎯 Tentando renderizar componente completo...")
                rendered_html = comp_block.render(component_data)
                debug_log.append(f"      ✅ Renderizado com sucesso ({len(rendered_html)} chars)")
                has_error = False
            except Exception as e:
                debug_log.append(f"      ❌ Erro na renderização: {str(e)}")
                render_error = str(e)
                
                try:
                    debug_log.append(f"      🔄 Tentando com dados mínimos...")
                    minimal_data = self.generate_minimal_component_data(comp_block)
                    rendered_html = comp_block.render(minimal_data)
                    debug_log.append(f"      ✅ Renderizado com dados mínimos")
                    has_error = False
                except Exception as e2:
                    debug_log.append(f"      ❌ Falhou também com dados mínimos: {str(e2)}")
                    rendered_html = self.create_visual_placeholder(comp_name, category_name, str(e))
                    has_error = True
            
            return {
                'name': comp_name,
                'display_name': self.get_component_display_name(comp_block, comp_name),
                'class_name': comp_block.__class__.__name__,
                'rendered_html': rendered_html,
                'category_name': category_name,
                'has_error': has_error,
                'error_message': render_error if has_error else None,
                'data_used': component_data if self.debug_mode else {},
            }
            
        except Exception as e:
            debug_log.append(f"      💥 ERRO GERAL: {str(e)}")
            return None
    
    def generate_realistic_component_data(self, comp_name, comp_block, debug_log):
        """Gera dados realistas para renderização visual completa"""
        if not hasattr(comp_block, 'child_blocks'):
            return {}
        
        data = {}
        debug_log.append(f"        📝 Gerando dados para {len(comp_block.child_blocks)} campos")
        
        for field_name, field_block in comp_block.child_blocks.items():
            value = self.generate_realistic_field_value(field_name, field_block, comp_name)
            data[field_name] = value
            
            if self.debug_mode:
                debug_log.append(f"          {field_name}: {str(value)[:50]}...")
        
        return data
    
    def generate_realistic_field_value(self, field_name, field_block, comp_name):
        """Gera valores realistas baseados no contexto ENAP com defaults específicos por tipo"""
        field_type = field_block.__class__.__name__
        field_lower = field_name.lower()
        
        # Usar default se existir
        if hasattr(field_block, 'default') and field_block.default is not None:
            return field_block.default
        
        # DEFAULTS ESPECÍFICOS POR TIPO DE CAMPO
        
        # === IMAGENS ===
        if field_type in ['ImageChooserBlock', 'ImageBlock']:
            return self.get_default_image_value(field_name)
        
        # === DOCUMENTOS ===
        elif field_type in ['DocumentChooserBlock', 'DocumentBlock']:
            return self.get_default_document_value(field_name)
        
        # === PÁGINAS ===
        elif field_type in ['PageChooserBlock', 'PageBlock']:
            return self.get_default_page_value(field_name)
        
        # === SNIPPETS ===
        elif field_type in ['SnippetChooserBlock']:
            return None  # Snippets são mais complexos, deixar vazio
        
        # === BLOCOS ESTRUTURADOS ===
        elif field_type == 'StructBlock':
            return {}  # Será processado recursivamente
        
        elif field_type == 'ListBlock':
            return self.generate_listblock_default_data(field_block, field_name)
        
        elif field_type == 'StreamBlock':
            return self.generate_streamblock_default_data(field_block, field_name)
        
        # === CAMPOS DE ESCOLHA ===
        elif field_type == 'ChoiceBlock':
            return self.get_choice_default_value(field_block, field_name)
        
        # === CAMPOS BÁSICOS ===
        elif field_type == 'BooleanBlock':
            return self.get_boolean_default_value(field_name)
        
        elif field_type in ['IntegerBlock', 'FloatBlock', 'DecimalBlock']:
            return self.get_numeric_default_value(field_name, field_type)
        
        elif field_type in ['DateBlock', 'TimeBlock', 'DateTimeBlock']:
            return self.get_datetime_default_value(field_type)
        
        elif field_type == 'RichTextBlock':
            return self.get_richtext_default_value(field_name)
        
        elif field_type in ['URLBlock']:
            return self.get_url_default_value(field_name)
        
        elif field_type == 'EmailBlock':
            return self.get_email_default_value(field_name)
        
        elif field_type in ['TextBlock', 'CharBlock']:
            return self.get_text_default_value(field_name, field_lower)
        
        elif field_type == 'RegexBlock':
            return 'ABC123'  # Valor que geralmente passa em regex básicas
        
        elif field_type == 'RawHTMLBlock':
            return '<div class="exemplo">Conteúdo HTML de exemplo</div>'
        
        # === BLOCOS CUSTOMIZADOS ===
        elif 'Color' in field_type:
            return '#3B82F6'  # Azul padrão
        
        elif 'Icon' in field_type:
            return 'fas fa-star'  # Ícone padrão
        
        # Valor padrão genérico
        return f'Exemplo ENAP - {field_name}'
    
    def get_default_image_value(self, field_name):
        """Gera valor padrão para campos de imagem"""
        from wagtail.images.models import Image
        
        # Tentar encontrar uma imagem existente no sistema
        try:
            # Buscar por imagens que possam ser usadas como placeholder
            placeholder_images = Image.objects.filter(
                title__icontains='placeholder'
            ).first()
            
            if placeholder_images:
                return placeholder_images
            
            # Buscar por imagens com nomes genéricos
            generic_names = ['exemplo', 'sample', 'test', 'demo', 'enap', 'logo']
            for name in generic_names:
                image = Image.objects.filter(title__icontains=name).first()
                if image:
                    return image
            
            # Se não encontrar, usar qualquer imagem
            any_image = Image.objects.first()
            if any_image:
                return any_image
                
        except Exception:
            pass
        
        # Se não houver imagens, criar uma imagem placeholder via código
        return self.create_placeholder_image_object(field_name)
    
    def create_placeholder_image_object(self, field_name):
        """Cria um objeto placeholder para representar uma imagem"""
        # Como não podemos criar imagens reais sem arquivos, 
        # retornamos None e deixamos o template lidar com isso
        # O template deve mostrar um placeholder visual
        return None
    
    def get_default_document_value(self, field_name):
        """Gera valor padrão para campos de documento"""
        from wagtail.documents.models import Document
        
        try:
            # Buscar documento de exemplo
            example_doc = Document.objects.filter(
                title__icontains='exemplo'
            ).first()
            
            if example_doc:
                return example_doc
            
            # Qualquer documento
            any_doc = Document.objects.first()
            if any_doc:
                return any_doc
                
        except Exception:
            pass
        
        return None
    
    def get_default_page_value(self, field_name):
        """Gera valor padrão para campos de página"""
        from wagtail.models import Page
        
        try:
            # Buscar página home ou root
            home_page = Page.objects.filter(
                slug__in=['home', 'inicio', 'root']
            ).first()
            
            if home_page:
                return home_page
            
            # Qualquer página que não seja root
            any_page = Page.objects.filter(depth__gt=1).first()
            if any_page:
                return any_page
                
        except Exception:
            pass
        
        return None
    
    def get_choice_default_value(self, field_block, field_name):
        """Gera valor padrão para campos de escolha"""
        try:
            if hasattr(field_block, 'choices') and field_block.choices:
                # Retornar a primeira opção
                return field_block.choices[0][0]
        except Exception:
            pass
        
        return 'opcao1'
    
    def get_boolean_default_value(self, field_name):
        """Gera valor padrão para campos boolean"""
        field_lower = field_name.lower()
        
        # Campos que geralmente são False por padrão
        false_defaults = [
            'disable', 'hidden', 'private', 'draft', 'inactive',
            'closed', 'locked', 'disabled', 'hide'
        ]
        
        for false_word in false_defaults:
            if false_word in field_lower:
                return False
        
        # Maioria dos booleans são True para melhor visualização
        return True
    
    def get_numeric_default_value(self, field_name, field_type):
        """Gera valor padrão para campos numéricos"""
        field_lower = field_name.lower()
        
        # Valores específicos baseados no nome
        if 'price' in field_lower or 'preco' in field_lower:
            return 299.90 if field_type == 'FloatBlock' else 299
        elif 'year' in field_lower or 'ano' in field_lower:
            return 2024
        elif 'month' in field_lower or 'mes' in field_lower:
            return 6
        elif 'day' in field_lower or 'dia' in field_lower:
            return 15
        elif 'hour' in field_lower or 'hora' in field_lower:
            return 14
        elif 'minute' in field_lower or 'minuto' in field_lower:
            return 30
        elif 'percent' in field_lower or 'porcentagem' in field_lower:
            return 85.5 if field_type == 'FloatBlock' else 85
        elif 'count' in field_lower or 'total' in field_lower:
            return 42
        elif 'order' in field_lower or 'ordem' in field_lower:
            return 1
        
        # Valor padrão genérico
        return 100.0 if field_type == 'FloatBlock' else 100
    
    def get_datetime_default_value(self, field_type):
        """Gera valor padrão para campos de data/hora"""
        if field_type == 'DateBlock':
            return '2024-06-15'
        elif field_type == 'TimeBlock':
            return '14:30:00'
        elif field_type == 'DateTimeBlock':
            return '2024-06-15T14:30:00'
        
        return '2024-06-15'
	
    def generate_streamblock_default_data(self, stream_block, field_name):
        """Gera dados padrão para StreamBlocks"""
        if not hasattr(stream_block, 'child_blocks'):
            return []
        
        stream_data = []
        available_blocks = list(stream_block.child_blocks.items())[:2]
        
        for block_name, block_instance in available_blocks:
            if hasattr(block_instance, 'child_blocks'):
                block_data = {}
                for child_field, child_block in block_instance.child_blocks.items():
                    block_data[child_field] = self.generate_realistic_field_value(
                        child_field, child_block, f"{field_name}_{block_name}"
                    )
            else:
                block_data = self.generate_realistic_field_value(
                    block_name, block_instance, field_name
                )
            
            stream_data.append({
                'type': block_name,
                'value': block_data
            })
        
        return stream_data

    def generate_listblock_default_data(self, field_block, field_name):
        """Gera dados padrão para ListBlocks"""
        if hasattr(field_block, 'child_block'):
            child_block = field_block.child_block
            items = []
            
            for i in range(2):
                if hasattr(child_block, 'child_blocks'):
                    item_data = {}
                    for sub_field, sub_block in child_block.child_blocks.items():
                        item_data[sub_field] = self.generate_realistic_field_value(
                            sub_field, sub_block, f"{field_name}_item_{i}"
                        )
                else:
                    item_data = self.generate_realistic_field_value(
                        f"{field_name}_item_{i}", child_block, f"{field_name}_list"
                    )
                items.append(item_data)
            
            return items
        
        return []
    
    def get_richtext_default_value(self, field_name):
        """Gera valor padrão para campos de texto rico"""
        field_lower = field_name.lower()
        
        # Conteúdos específicos baseados no nome do campo
        if 'about' in field_lower or 'sobre' in field_lower:
            return '''
            <h3>Sobre a ENAP</h3>
            <p>A <strong>Escola Nacional de Administração Pública</strong> é responsável pela capacitação e desenvolvimento de servidores públicos federais.</p>
            <ul>
                <li>Cursos presenciais e à distância</li>
                <li>Eventos e seminários</li>
                <li>Pesquisas em gestão pública</li>
            </ul>
            '''
        elif 'content' in field_lower or 'conteudo' in field_lower:
            return '''
            <h2>Modernização da Gestão Pública</h2>
            <p>A Enap promove a <em>excelência na administração pública</em> através de:</p>
            <ol>
                <li><strong>Capacitação continuada</strong> de servidores</li>
                <li><strong>Pesquisa aplicada</strong> em gestão pública</li>
                <li><strong>Inovação</strong> em processos governamentais</li>
            </ol>
            <blockquote>
                <p>"Transformando a administração pública através do conhecimento"</p>
            </blockquote>
            '''
        elif 'description' in field_lower or 'descricao' in field_lower:
            return '''
            <p>Desenvolvemos <strong>competências e habilidades</strong> dos servidores para uma gestão pública moderna, eficiente e orientada ao cidadão.</p>
            <p>Nossa missão é contribuir para a modernização do Estado através da capacitação de seus servidores.</p>
            '''
        
        # Conteúdo padrão genérico
        return '''
        <h3>Título de Exemplo</h3>
        <p>Este é um conteúdo de <strong>exemplo</strong> em texto rico para demonstrar a funcionalidade do componente.</p>
        <p>Inclui <em>formatação básica</em> e <a href="https://www.enap.gov.br">links externos</a>.</p>
        '''
    
    def get_url_default_value(self, field_name):
        """Gera valor padrão para campos de URL"""
        field_lower = field_name.lower()
        
        # URLs específicas baseadas no nome do campo
        url_mapping = {
            'site': 'https://www.enap.gov.br',
            'home': 'https://www.enap.gov.br',
            'curso': 'https://www.enap.gov.br/cursos',
            'course': 'https://www.enap.gov.br/cursos',
            'event': 'https://www.enap.gov.br/eventos',
            'evento': 'https://www.enap.gov.br/eventos',
            'news': 'https://www.enap.gov.br/noticias',
            'noticia': 'https://www.enap.gov.br/noticias',
            'contact': 'https://www.enap.gov.br/contato',
            'contato': 'https://www.enap.gov.br/contato',
            'blog': 'https://www.enap.gov.br/blog',
            'video': 'https://www.youtube.com/watch?v=example',
            'youtube': 'https://www.youtube.com/watch?v=example',
            'social': 'https://www.linkedin.com/company/enap',
            'linkedin': 'https://www.linkedin.com/company/enap',
            'facebook': 'https://www.facebook.com/enap.oficial',
            'twitter': 'https://twitter.com/enap_oficial',
            'instagram': 'https://instagram.com/enap_oficial',
        }
        
        for key, url in url_mapping.items():
            if key in field_lower:
                return url
        
        # URL padrão
        return 'https://www.enap.gov.br'
    
    def get_email_default_value(self, field_name):
        """Gera valor padrão para campos de email"""
        field_lower = field_name.lower()
        
        # Emails específicos baseados no nome do campo
        email_mapping = {
            'contact': 'contato@enap.gov.br',
            'contato': 'contato@enap.gov.br',
            'support': 'suporte@enap.gov.br',
            'suporte': 'suporte@enap.gov.br',
            'admin': 'admin@enap.gov.br',
            'curso': 'cursos@enap.gov.br',
            'course': 'cursos@enap.gov.br',
            'event': 'eventos@enap.gov.br',
            'evento': 'eventos@enap.gov.br',
            'news': 'noticias@enap.gov.br',
            'noticia': 'noticias@enap.gov.br',
            'inscricao': 'inscricoes@enap.gov.br',
            'registration': 'inscricoes@enap.gov.br',
        }
        
        for key, email in email_mapping.items():
            if key in field_lower:
                return email
        
        # Email padrão
        return 'contato@enap.gov.br'
    
    def get_text_default_value(self, field_name, field_lower):
        """Gera valor padrão para campos de texto"""
        # Conteúdos específicos da ENAP baseados no nome do campo
        
        if 'title' in field_lower or 'titulo' in field_lower:
            titles = [
                'Escola Nacional de Administração Pública',
                'Capacitação para o Serviço Público',
            ]
            import random
            return random.choice(titles)
            
        elif 'subtitle' in field_lower or 'subtitulo' in field_lower:
            return 'Excelência em capacitação para o serviço público'
            
        elif 'description' in field_lower or 'descricao' in field_lower:
            descriptions = [
                'A ENAP é a escola de governo do Poder Executivo federal, responsável pela formação e capacitação de servidores públicos.'
            ]
            import random
            return random.choice(descriptions)
            
        elif 'button' in field_lower or 'botao' in field_lower or 'cta' in field_lower:
            buttons = ['Saiba Mais', 'Inscreva-se', 'Conheça', 'Participe', 'Acesse', 'Baixar', 'Ver Mais']
            import random
            return random.choice(buttons)
            
        elif 'name' in field_lower or 'nome' in field_lower:
            return 'ENAP - Escola Nacional de Administração Pública'
            
        elif 'author' in field_lower or 'autor' in field_lower:
            return 'Equipe ENAP'
            
        elif 'phone' in field_lower or 'telefone' in field_lower:
            return '(61) 2020-3000'
            
        elif 'address' in field_lower or 'endereco' in field_lower:
            return 'SAIS - Área 2-A - Brasília/DF - CEP: 70610-900'
            
        elif 'city' in field_lower or 'cidade' in field_lower:
            return 'Brasília'
            
        elif 'state' in field_lower or 'estado' in field_lower:
            return 'Distrito Federal'
            
        elif 'country' in field_lower or 'pais' in field_lower:
            return 'Brasil'
            
        elif 'price' in field_lower or 'preco' in field_lower:
            return 'Gratuito'
            
        elif 'duration' in field_lower or 'duracao' in field_lower:
            return '40 horas'
            
        elif 'level' in field_lower or 'nivel' in field_lower:
            return 'Intermediário'
            
        elif 'category' in field_lower or 'categoria' in field_lower:
            return 'Gestão Pública'
            
        elif 'tag' in field_lower:
            return 'capacitacao'
            
        elif 'slug' in field_lower:
            return 'exemplo-componente-enap'
        
        # Valor padrão baseado no nome do campo
        return f'Exemplo ENAP - {field_name.replace("_", " ").title()}'
    
    def generate_minimal_component_data(self, comp_block):
        """Gera dados mínimos para fallback"""
        if not hasattr(comp_block, 'child_blocks'):
            return {}
        
        minimal = {}
        for field_name, field_block in comp_block.child_blocks.items():
            field_type = field_block.__class__.__name__
            
            if 'title' in field_name.lower():
                minimal[field_name] = 'ENAP'
            elif field_type == 'BooleanBlock':
                minimal[field_name] = True
            elif field_type in ['IntegerBlock', 'FloatBlock']:
                minimal[field_name] = 1
        
        return minimal
    
    def create_visual_placeholder(self, comp_name, category_name, error_msg):
        """Cria um placeholder visual para componentes com erro"""
        return f'''
        <div style="
            padding: 2rem; 
            background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); 
            border: 2px dashed #dc2626; 
            border-radius: 12px; 
            text-align: center; 
            color: #7f1d1d; 
            margin: 1rem 0;
            box-shadow: 0 4px 8px rgba(220, 38, 38, 0.1);
        ">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚠️</div>
            <h3 style="margin: 0 0 0.5rem 0; color: #dc2626; font-size: 1.25rem;">{comp_name}</h3>
            <p style="margin: 0 0 0.5rem 0; font-size: 0.875rem;">Componente não pôde ser renderizado</p>
            <small style="color: #991b1b; display: block;">Categoria: {category_name}</small>
            {f'<details style="margin-top: 1rem;"><summary style="cursor: pointer;">Ver erro técnico</summary><div style="margin-top: 0.5rem; font-family: monospace; font-size: 0.75rem; text-align: left; background: rgba(0,0,0,0.1); padding: 0.5rem; border-radius: 4px;">{error_msg}</div></details>' if self.debug_mode else ''}
        </div>
        '''
    
    def get_component_display_name(self, block, comp_name):
        """Nome de exibição limpo do componente"""
        if hasattr(block, 'label') and block.label:
            label = block.label
            # Remove emojis do início
            emoji_prefixes = ['🎯', '🎨', '🏢', '🚀', '🔍', '📑', '🖼️', '⭐', '🎬', '📋', '⚡', '📞', '👂']
            for emoji in emoji_prefixes:
                if label.startswith(emoji):
                    parts = label.split(' ', 1)
                    if len(parts) > 1:
                        return parts[1]
                    break
            return label
        
        # Formatar nome da classe
        class_name = block.__class__.__name__
        if class_name.endswith('Block'):
            class_name = class_name[:-5]
        
        return class_name.replace('_', ' ').title()
    
    def format_category_name(self, category_name):
        """Formata nome da categoria"""
        category_names = {
            'banners': 'Banners e Heroes',
            'galerias': 'Galerias e Imagens',
            'carousels': 'Carrosséis',
            'dashboards': 'Dashboards e Métricas',
            'formularios': 'Formulários',
            'cursos': 'Cursos e Educação',
            'eventos': 'Eventos',
            'navegacao': 'Navegação',
            'menus': 'Menus',
            'botoes': 'Botões e CTAs',
            'conteudo': 'Conteúdo e Texto',
            'secoes': 'Seções e Containers',
            'cards': 'Cards',
            'interativos': 'Componentes Interativos',
            'midia': 'Mídia e Vídeos',
            'especialidades': 'Componentes Especializados',
        }
        
        return category_names.get(category_name, category_name.replace('_', ' ').title())
    
    def get_category_icon(self, category_name):
        """Ícone da categoria"""
        icons = {
            'banners': 'image',
            'galerias': 'images',
            'carousels': 'arrows-up-down',
            'dashboards': 'chart-bar',
            'formularios': 'edit',
            'cursos': 'graduation-cap',
            'eventos': 'calendar',
            'navegacao': 'bars',
            'menus': 'list',
            'botoes': 'mouse-pointer',
            'conteudo': 'file-text',
            'secoes': 'th-large',
            'cards': 'clone',
            'interativos': 'cogs',
            'midia': 'play-circle',
            'especialidades': 'puzzle-piece',
        }
        return icons.get(category_name, 'cube')
    
    def get_category_description(self, category_name):
        """Descrição da categoria"""
        descriptions = {
            'banners': 'Componentes para seções de destaque, heroes e banners promocionais',
            'galerias': 'Componentes para exibição de imagens, galerias e portfolios visuais',
            'carousels': 'Componentes de carrosséis, sliders e apresentações rotativas',
            'dashboards': 'Componentes para dashboards, KPIs, gráficos e visualização de dados',
            'formularios': 'Componentes de formulários, campos de entrada e validação',
            'cursos': 'Componentes específicos para cursos, educação e capacitação online',
            'eventos': 'Componentes para eventos, cronogramas e calendários',
            'navegacao': 'Componentes de navegação, menus e estruturas de site',
            'menus': 'Componentes específicos de menu e navegação secundária',
            'botoes': 'Componentes de botões, call-to-actions e elementos clicáveis',
            'conteudo': 'Componentes de conteúdo, texto rico, citações e artigos',
            'secoes': 'Componentes de seções, containers e estruturas de layout',
            'cards': 'Componentes de cards, grids e elementos organizacionais',
            'interativos': 'Componentes interativos, acordeões, modais e elementos dinâmicos',
            'midia': 'Componentes de vídeo, áudio, podcasts e conteúdo multimídia',
            'especialidades': 'Componentes especializados e funcionalidades específicas da ENAP',
        }
        return descriptions.get(category_name, f'Componentes da categoria {category_name}')
	














class LinkBlockVariavel(blocks.StructBlock):
    """Block para links simples"""
    texto = blocks.CharBlock(max_length=100, label="Texto do link")
    url = blocks.URLBlock(label="URL")



class FooterSectionBlock(blocks.StructBlock):
    """Block para uma seção do footer com título e links"""
    titulo = blocks.CharBlock(max_length=200, label="Título da seção")
    links = blocks.StreamBlock([
        ('link', LinkBlockVariavel()),
    ], label="Links da seção")
    
    class Meta:
        icon = 'list-ul'
        label = 'Seção do Footer'


@register_snippet
class FooterGenericoSnippet(ClusterableModel):
    """
    Footer genérico reutilizável para páginas do site.
    """

    class Meta:
        verbose_name = "Footer Genérico"
        verbose_name_plural = "Footers Genéricos"

    nome = models.CharField(
        max_length=255,
        help_text="Nome identificador do footer"
    )

    # Configurações visuais
    cor_fundo = models.CharField(
        max_length=7,
        default="#525258",
        help_text="Cor do fundo (ex: #525258)"
    )
    
    cor_texto = models.CharField(
        max_length=7,
        default="#ffffff",
        help_text="Cor dos textos (ex: #ffffff)"
    )

    # Logo e texto
    logo = StreamField([
        ("logo", ImageChooserBlock()),
    ], 
    max_num=1,
    blank=True, 
    use_json_field=True,
    help_text="Logo do footer"
    )
    
    texto_logo = models.TextField(
        blank=True,
        verbose_name="Texto do logo",
        help_text="Texto que aparece abaixo da logo"
    )

    # Seções de links
    secoes = StreamField([
        ("secao", FooterSectionBlock()),
    ], 
    blank=True, 
    use_json_field=True,
    help_text="Seções com títulos e links do footer"
    )

    panels = [
        FieldPanel("nome"),
        FieldPanel("cor_fundo"),
        FieldPanel("cor_texto"),
        FieldPanel("logo"),
        FieldPanel("texto_logo"),
        FieldPanel("secoes"),
    ]

    def __str__(self):
        return self.nome
    
    @property 
    def get_logo(self):
        """Retorna a logo se existir"""
        if self.logo:
            return self.logo[0].value
        return None











# enap_designsystem/models.py
from django.db import models
from django import forms
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel


# ============================================
# PÁGINA MÃE - ÍNDICE DAS CÁPSULAS
# ============================================

class CapsulaIndexPage(Page):
    """
    Página mãe que lista todas as cápsulas com sistema de filtros
    """
    template = "enap_designsystem/pages/capsula_index_page.html"
	
    navbar = models.ForeignKey(
        "EnapNavbarSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
	
    footer = models.ForeignKey(
        "EnapFooterSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    intro = RichTextField(
        blank=True,
        verbose_name="Texto introdutório",
        help_text="Texto que aparece no topo da página de listagem"
    )
    
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
		FieldPanel('navbar'),
		FieldPanel('footer'),
    ]
    
    # Não restringe onde pode ser criada
    subpage_types = ['enap_designsystem.CapsulaPage']  # Só aceita cápsulas como filhas
    max_count = 1  # Só pode ter uma página de índice no site
    
    class Meta:
        verbose_name = "Página Índice de Cápsulas"
        verbose_name_plural = "Páginas Índice de Cápsulas"
    
    def get_context(self, request):
        context = super().get_context(request)
        
        # Todas as cápsulas publicadas (filhas desta página)
        capsulas = CapsulaPage.objects.child_of(self).live().public()
        
        # SOLUÇÃO: Converter para lista e filtrar em Python para SQLite
        capsulas_list = list(capsulas)
        
        # Aplicar filtros da URL
        tipos_def = request.GET.getlist('tipo_deficiencia')
        if tipos_def:
            capsulas_list = [
                c for c in capsulas_list 
                if c.tipos_deficiencia and any(t in c.tipos_deficiencia for t in tipos_def)
            ]
        
        formatos = request.GET.getlist('formato_acao')
        if formatos:
            capsulas_list = [
                c for c in capsulas_list 
                if c.formatos_acao and any(f in c.formatos_acao for f in formatos)
            ]
        
        recursos = request.GET.getlist('tipo_recurso')
        if recursos:
            capsulas_list = [
                c for c in capsulas_list 
                if c.tipos_recurso and any(r in c.tipos_recurso for r in recursos)
            ]
        
        perfis = request.GET.getlist('perfil_profissional')
        if perfis:
            capsulas_list = [
                c for c in capsulas_list 
                if c.perfis_profissionais and any(p in c.perfis_profissionais for p in perfis)
            ]
        
        prioridade = request.GET.get('prioridade')
        if prioridade:
            capsulas_list = [c for c in capsulas_list if c.prioridade == prioridade]
        
        context['capsulas'] = capsulas_list
        context['total_resultados'] = len(capsulas_list)
        
        # Passar as choices para o template
        context['opcoes_filtros'] = {
            'tipos_deficiencia': CapsulaPage.TIPOS_DEFICIENCIA_CHOICES,
            'formatos_acao': CapsulaPage.FORMATOS_ACAO_CHOICES,
            'tipos_recurso': CapsulaPage.TIPOS_RECURSO_CHOICES,
            'perfis_profissionais': CapsulaPage.PERFIS_PROFISSIONAIS_CHOICES,
        }
        
        # Filtros ativos
        context['filtros_ativos'] = {
            'tipo_deficiencia': tipos_def,
            'formato_acao': formatos,
            'tipo_recurso': recursos,
            'perfil_profissional': perfis,
            'prioridade': prioridade,
        }
        
        # Calcular contadores
        context['contadores'] = self._calcular_contadores(capsulas)
        
        return context
    
    def _calcular_contadores(self, queryset):
        """Calcula quantas cápsulas têm cada tag - versão compatível com SQLite"""
        contadores = {
            'tipos_deficiencia': {},
            'formatos_acao': {},
            'tipos_recurso': {},
            'perfis_profissionais': {},
        }
        
        # Converter queryset para lista
        capsulas_list = list(queryset)
        
        # Tipos de Deficiência
        for value, label in CapsulaPage.TIPOS_DEFICIENCIA_CHOICES:
            count = sum(1 for c in capsulas_list if c.tipos_deficiencia and value in c.tipos_deficiencia)
            contadores['tipos_deficiencia'][value] = count
        
        # Formatos de Ação
        for value, label in CapsulaPage.FORMATOS_ACAO_CHOICES:
            count = sum(1 for c in capsulas_list if c.formatos_acao and value in c.formatos_acao)
            contadores['formatos_acao'][value] = count
        
        # Tipos de Recurso
        for value, label in CapsulaPage.TIPOS_RECURSO_CHOICES:
            count = sum(1 for c in capsulas_list if c.tipos_recurso and value in c.tipos_recurso)
            contadores['tipos_recurso'][value] = count
        
        # Perfis Profissionais
        for value, label in CapsulaPage.PERFIS_PROFISSIONAIS_CHOICES:
            count = sum(1 for c in capsulas_list if c.perfis_profissionais and value in c.perfis_profissionais)
            contadores['perfis_profissionais'][value] = count
        
        return contadores


# ============================================
# PÁGINA FILHA - CÁPSULA INDIVIDUAL
# ==================from django.db import models
from django import forms


class CapsulaPage(Page):
    """
    Página individual de cada cápsula de acessibilidade
    """
	
    navbar = models.ForeignKey(
        "EnapNavbarSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
	
    footer = models.ForeignKey(
        "EnapFooterSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
	

    template = "enap_designsystem/pages/capsula_page.html"
    
    # ==========================================
    # CHOICES FIXAS PARA OS FILTROS
    # ==========================================
    
    TIPOS_DEFICIENCIA_CHOICES = [
        ('visual', 'Visual'),
        ('auditiva', 'Auditiva'),
        ('motora', 'Motora'),
        ('cognitiva', 'Cognitiva'),
    ]
    
    FORMATOS_ACAO_CHOICES = [
        ('distancia_sincrono', 'A distância síncrono'),
        ('distancia_assincrono', 'A distância assíncrono'),
        ('presencial', 'Presencial'),
        ('semipresencial', 'Semipresencial'),
    ]
    
    TIPOS_RECURSO_CHOICES = [
        ('imagem', 'Imagem'),
        ('video', 'Vídeo'),
        ('tabela', 'Tabela'),
        ('grafico', 'Gráfico'),
        ('botao', 'Botão'),
        ('texto', 'Texto'),
        ('audio', 'Áudio'),
        ('hiperlink', 'Hiperlink'),
        ('videoconferencia', 'Videoconferência'),
    ]
    
    PERFIS_PROFISSIONAIS_CHOICES = [
        ('designer_instrucional', 'Designer instrucional'),
        ('designer_grafico', 'Designer gráfico'),
        ('implementador_web', 'Implementador web'),
        ('editor_video', 'Editor de vídeo'),
        ('docente', 'Docente'),
        ('curador_conteudo', 'Curador de conteúdo'),
        ('conteudista', 'Conteudista'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('obrigatorio', 'Obrigatório'),
        ('recomendado', 'Recomendado'),
    ]
    
    # ==========================================
    # CAMPOS DE CLASSIFICAÇÃO (FILTROS)
    # ==========================================
    
    tipos_deficiencia = models.JSONField(
        blank=True,
        default=list,
        verbose_name="Tipos de Deficiência",
        help_text="Selecione um ou mais tipos"
    )
    
    formatos_acao = models.JSONField(
        blank=True,
        default=list,
        verbose_name="Formatos de Ação",
        help_text="Selecione um ou mais formatos"
    )
    
    tipos_recurso = models.JSONField(
        blank=True,
        default=list,
        verbose_name="Tipos de Recurso",
        help_text="Selecione um ou mais tipos"
    )
    
    perfis_profissionais = models.JSONField(
        blank=True,
        default=list,
        verbose_name="Perfis Profissionais",
        help_text="Selecione um ou mais perfis"
    )
    
    prioridade = models.CharField(
        max_length=20,
        choices=PRIORIDADE_CHOICES,
        default='recomendado',
        verbose_name="Prioridade"
    )
    
    # ==========================================
    # CONTEÚDO DA CÁPSULA
    # ==========================================
    
    resumo_card = models.TextField(
        max_length=300,
        blank=True,
        verbose_name="Resumo para o card",
        help_text="Texto curto para exibir na listagem (máx. 300 caracteres)"
    )
    
    # ==========================================
    # 1. O QUE É? - COM IMAGEM (StreamField)
    # ==========================================
    
    o_que_e_imagem = StreamField(
        [
            ('image', ImageChooserBlock(required=False, label="Imagem principal"))
        ],
        blank=True,
        use_json_field=True,
        max_num=1,
        verbose_name="Imagem",
        help_text="Imagem ilustrativa da seção 'O que é?'"
    )
    
    o_que_e_resumo = RichTextField(
        verbose_name="O que é? (Resumo)",
        help_text="Texto curto exibido inicialmente",
        features=['bold', 'italic', 'link']
    )
    
    o_que_e_detalhado = RichTextField(
        blank=True,
        verbose_name="O que é? (Detalhado)",
        help_text="Texto completo - aparece ao clicar em 'Leia mais'",
        features=['h3', 'h4', 'bold', 'italic', 'link', 'ol', 'ul']
    )
    
    # 2. Por que é importante?
    por_que_importante_resumo = RichTextField(
        verbose_name="Por que é importante? (Resumo)",
        help_text="Texto curto exibido inicialmente",
        features=['bold', 'italic', 'link']
    )
    
    por_que_importante_detalhado = RichTextField(
        blank=True,
        verbose_name="Por que é importante? (Detalhado)",
        help_text="Texto completo - aparece ao clicar em 'Leia mais'",
        features=['h3', 'h4', 'bold', 'italic', 'link', 'ol', 'ul']
    )
    
    # ==========================================
    # 3. QUANDO UTILIZAR? - STREAMFIELD DE CARDS
    # ==========================================
    
    quando_utilizar_resumo = RichTextField(
        verbose_name="Quando utilizar? (Resumo)",
        help_text="Texto curto exibido inicialmente",
        features=['bold', 'italic', 'link']
    )
    
    quando_utilizar_cards = StreamField(
        [
            ("enap_cardgrid", EnapCardGridBlock([
                ("card", EnapCardInfo()),
            ]))
        ],
        blank=True,
        use_json_field=True,
        verbose_name="Cards de cenários",
        help_text="Adicione cards explicando diferentes cenários de uso"
    )
    
    # ==========================================
    # 4. COMO APLICAR - COM IMAGEM (StreamField)
    # ==========================================
    
    como_aplicar_imagem = StreamField(
        [
            ('image', ImageChooserBlock(required=False, label="Imagem do passo a passo"))
        ],
        blank=True,
        use_json_field=True,
        max_num=1,
        verbose_name="Imagem",
        help_text="Imagem ilustrativa de como aplicar"
    )
    
    como_aplicar_resumo = RichTextField(
        verbose_name="Como aplicar (Resumo)",
        help_text="Texto curto exibido inicialmente",
        features=['bold', 'italic', 'link']
    )
    
    como_aplicar_detalhado = RichTextField(
        blank=True,
        verbose_name="Como aplicar (Detalhado)",
        help_text="Texto completo - aparece ao clicar em 'Leia mais'",
        features=['h3', 'h4', 'bold', 'italic', 'link', 'ol', 'ul', 'code']
    )
    
    # ==========================================
    # 5. MÉTODO DE VERIFICAÇÃO - STREAMFIELD DE CARDS
    # ==========================================
    
    metodo_verificacao_resumo = RichTextField(
        verbose_name="Método de verificação (Resumo)",
        help_text="Texto curto exibido inicialmente",
        features=['bold', 'italic', 'link']
    )
    
    metodo_verificacao_cards = StreamField(
        [
            ("enap_cardgrid", EnapCardGridBlock([
                ("card", CardBlock()),
            ]))
        ],
        blank=True,
        use_json_field=True,
        verbose_name="Cards de métodos",
        help_text="Adicione cards com diferentes métodos de verificação"
    )
    
    # 6. Exemplos
    exemplos_resumo = RichTextField(
        verbose_name="Exemplos (Resumo)",
        help_text="Texto curto exibido inicialmente",
        features=['bold', 'italic', 'link']
    )
    
    exemplos_detalhado = RichTextField(
        blank=True,
        verbose_name="Exemplos (Detalhado)",
        help_text="Texto completo - aparece ao clicar em 'Leia mais'",
        features=['h3', 'h4', 'bold', 'italic', 'link', 'ol', 'ul', 'code', 'image']
    )
    
    # 7. O que não fazer?
    o_que_nao_fazer_resumo = RichTextField(
        verbose_name="O que não fazer? (Resumo)",
        help_text="Texto curto exibido inicialmente",
        features=['bold', 'italic', 'link']
    )
    
    o_que_nao_fazer_detalhado = RichTextField(
        blank=True,
        verbose_name="O que não fazer? (Detalhado)",
        help_text="Texto completo - aparece ao clicar em 'Leia mais'",
        features=['h3', 'h4', 'bold', 'italic', 'link', 'ol', 'ul']
    )
    
    # 8. Normas de referência
    normas_referencia = RichTextField(
        blank=True,
        verbose_name="Normas de referência",
        help_text="Lista de normas técnicas principais (WCAG, NBR, etc.)",
        features=['h3', 'h4', 'bold', 'italic', 'link', 'ol', 'ul']
    )
    
    # Metadados
    destaque_home = models.BooleanField(
        default=False,
        verbose_name="Destacar na Home",
        help_text="Marque para exibir esta cápsula na página inicial"
    )
    
    data_atualizacao = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de atualização",
        help_text="Data da última revisão do conteúdo"
    )
    
    # ==========================================
    # PAINÉIS DO WAGTAIL ADMIN
    # ==========================================
    
    content_panels = Page.content_panels + [
        
        MultiFieldPanel([
			FieldPanel('navbar'),
			FieldPanel('footer'),
            FieldPanel('resumo_card'),
            FieldPanel('prioridade'),
            FieldPanel('destaque_home'),
            FieldPanel('data_atualizacao'),
        ], heading="📋 Informações Gerais", classname="collapsible"),
        
        MultiFieldPanel([
            FieldPanel('tipos_deficiencia', widget=forms.CheckboxSelectMultiple(choices=TIPOS_DEFICIENCIA_CHOICES)),
            FieldPanel('formatos_acao', widget=forms.CheckboxSelectMultiple(choices=FORMATOS_ACAO_CHOICES)),
            FieldPanel('tipos_recurso', widget=forms.CheckboxSelectMultiple(choices=TIPOS_RECURSO_CHOICES)),
            FieldPanel('perfis_profissionais', widget=forms.CheckboxSelectMultiple(choices=PERFIS_PROFISSIONAIS_CHOICES)),
        ], heading="🔖 Classificação (Tags para Filtros)", classname="collapsible"),
        
        MultiFieldPanel([
            FieldPanel('o_que_e_imagem'),
            FieldPanel('o_que_e_resumo'),
            FieldPanel('o_que_e_detalhado'),
        ], heading="1️⃣ O que é?", classname="collapsible collapsed"),
        
        MultiFieldPanel([
            FieldPanel('por_que_importante_resumo'),
            FieldPanel('por_que_importante_detalhado'),
        ], heading="2️⃣ Por que é importante?", classname="collapsible collapsed"),
        
        MultiFieldPanel([
            FieldPanel('quando_utilizar_resumo'),
            FieldPanel('quando_utilizar_cards'),
        ], heading="3️⃣ Quando utilizar?", classname="collapsible collapsed"),
        
        MultiFieldPanel([
            FieldPanel('como_aplicar_imagem'),
            FieldPanel('como_aplicar_resumo'),
            FieldPanel('como_aplicar_detalhado'),
        ], heading="4️⃣ Como aplicar", classname="collapsible collapsed"),
        
        MultiFieldPanel([
            FieldPanel('metodo_verificacao_resumo'),
            FieldPanel('metodo_verificacao_cards'),
        ], heading="5️⃣ Método de verificação", classname="collapsible collapsed"),
        
        MultiFieldPanel([
            FieldPanel('exemplos_resumo'),
            FieldPanel('exemplos_detalhado'),
        ], heading="6️⃣ Exemplos", classname="collapsible collapsed"),
        
        MultiFieldPanel([
            FieldPanel('o_que_nao_fazer_resumo'),
            FieldPanel('o_que_nao_fazer_detalhado'),
        ], heading="7️⃣ O que não fazer?", classname="collapsible collapsed"),
        
        MultiFieldPanel([
            FieldPanel('normas_referencia'),
        ], heading="8️⃣ Normas de referência", classname="collapsible collapsed"),
    ]
    
    # Configuração de hierarquia
    parent_page_types = ['enap_designsystem.CapsulaIndexPage']
    subpage_types = []
    
    class Meta:
        verbose_name = "Cápsula de Acessibilidade"
        verbose_name_plural = "Cápsulas de Acessibilidade"
    
    # ==========================================
    # MÉTODOS HELPERS
    # ==========================================
    
    def get_context(self, request):
        context = super().get_context(request)
        
        # Buscar cápsulas relacionadas (mesmos tipos de deficiência)
        capsulas_relacionadas = CapsulaPage.objects.live().public().exclude(id=self.id)
        
        if self.tipos_deficiencia:
            # SOLUÇÃO: Buscar manualmente em Python ao invés de query no banco
            # Para SQLite, fazemos a filtragem após recuperar os dados
            todas_capsulas = list(capsulas_relacionadas)
            capsulas_filtradas = []
            
            for capsula in todas_capsulas:
                # Verifica se há interseção entre os tipos de deficiência
                if capsula.tipos_deficiencia:
                    tipos_em_comum = set(self.tipos_deficiencia) & set(capsula.tipos_deficiencia)
                    if tipos_em_comum:
                        capsulas_filtradas.append(capsula)
            
            capsulas_relacionadas = capsulas_filtradas[:3]
        else:
            capsulas_relacionadas = list(capsulas_relacionadas)[:3]
        
        context['capsulas_relacionadas'] = capsulas_relacionadas
        
        return context
	









from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

# enap_designsystem/models.py

class QuizRotaPage(Page):
    """
    Página principal do Quiz de Rotas Personalizadas
    """
    template = "enap_designsystem/pages/quiz_rota_page.html"
	
    navbar = models.ForeignKey(
        "EnapNavbarSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
	
    footer = models.ForeignKey(
        "EnapFooterSnippet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    
    introducao = RichTextField(
        verbose_name="Texto introdutório",
        help_text="Explica como funciona o direcionamento personalizado"
    )
    
    texto_resultado = RichTextField(
        blank=True,
        verbose_name="Texto de apresentação do resultado",
        help_text="Aparece na página de resultado antes das cápsulas"
    )
    
    content_panels = Page.content_panels + [
        FieldPanel('introducao'),
        FieldPanel('texto_resultado'),
		FieldPanel('navbar'),
		FieldPanel('footer'),
    ]
    
    def serve(self, request):
        """Override para gerenciar requisições de resultado"""
        
        # Se tiver parâmetros de resposta na URL, salvar na sessão
        if request.GET.get('perfil') or request.GET.get('recurso') or request.GET.get('formato'):
            self.salvar_respostas_url(request)
        
        # Se for requisição de resultado
        if request.GET.get('resultado') == '1':
            return self.servir_resultado(request)
        
        # Renderização normal do quiz
        return super().serve(request)
    
    def salvar_respostas_url(self, request):
        """Salva respostas vindas da URL na sessão"""
        respostas = {}
        
        # Perfil profissional
        if request.GET.get('perfil'):
            perfil_valor = request.GET.get('perfil')
            perfil_texto = request.GET.get('perfil_texto', perfil_valor)
            respostas['perfil_profissional'] = {
                'valor': perfil_valor,
                'texto': perfil_texto
            }
        
        # Tipo de recurso
        if request.GET.get('recurso'):
            recurso_valor = request.GET.get('recurso')
            recurso_texto = request.GET.get('recurso_texto', recurso_valor)
            respostas['tipo_recurso'] = {
                'valor': recurso_valor,
                'texto': recurso_texto
            }
        
        # Formato de ação
        if request.GET.get('formato'):
            formato_valor = request.GET.get('formato')
            formato_texto = request.GET.get('formato_texto', formato_valor)
            respostas['formato_acao'] = {
                'valor': formato_valor,
                'texto': formato_texto
            }
        
        # Salvar na sessão
        request.session['quiz_respostas'] = respostas
    
    def servir_resultado(self, request):
        """Renderiza página de resultado com cápsulas filtradas"""
        from django.shortcuts import render, redirect
        
        # Recuperar respostas da sessão
        respostas = request.session.get('quiz_respostas', {})
        
        if not respostas:
            return redirect(self.url)
        
        # Buscar cápsulas baseadas nas respostas
        capsulas = self.filtrar_capsulas(respostas)
        
        context = self.get_context(request)
        context.update({
            'e_resultado': True,
            'respostas': respostas,
            'capsulas_recomendadas': capsulas,
            'total_capsulas': len(capsulas),
        })
        
        return render(request, self.get_template(request), context)
    
    def filtrar_capsulas(self, respostas):
        """Filtra cápsulas baseado nas respostas do quiz"""
        from enap_designsystem.models import CapsulaPage
        
        # Começar com todas as cápsulas
        capsulas = list(CapsulaPage.objects.live().public())
        
        # Perfil Profissional
        if 'perfil_profissional' in respostas:
            perfil = respostas['perfil_profissional']['valor']
            capsulas = [
                c for c in capsulas 
                if c.perfis_profissionais and perfil in c.perfis_profissionais
            ]
        
        # Tipo de Recurso
        if 'tipo_recurso' in respostas:
            recurso = respostas['tipo_recurso']['valor']
            capsulas = [
                c for c in capsulas 
                if c.tipos_recurso and recurso in c.tipos_recurso
            ]
        
        # Formato de Ação
        if 'formato_acao' in respostas:
            formato = respostas['formato_acao']['valor']
            capsulas = [
                c for c in capsulas 
                if c.formatos_acao and formato in c.formatos_acao
            ]
        
        # Ordenar por prioridade (obrigatório primeiro)
        capsulas.sort(key=lambda c: (c.prioridade != 'obrigatorio', c.title))
        
        return capsulas
    
    subpage_types = []
    
    class Meta:
        verbose_name = "Quiz de Rotas"
        verbose_name_plural = "Quiz de Rotas"