from django.db import models
from django import forms
from wagtail.admin.forms import WagtailAdminPageForm
from .security import validate_safe_characters, validate_email_field
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.utils.html import strip_tags
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.blocks import StreamBlock, StructBlock, CharBlock, RichTextBlock, URLBlock
import requests
from django.utils import timezone
from django.core.files.storage import default_storage
import os
import uuid
from django.conf import settings
import re
import json
import logging 
from wagtail.blocks import StreamBlock, StructBlock, CharBlock
from ..utils.services import SimpleEmailService
logger = logging.getLogger(__name__) 


from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.blocks import StreamBlock, StructBlock, CharBlock, RichTextBlock, URLBlock




class SafeFormMixin:
    """
    Aplica validação de caracteres em todos os campos
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_character_validation()
    
    def apply_character_validation(self):
        """
        Aplica validação baseada no tipo de campo
        """
        for field_name, field in self.fields.items():
            if isinstance(field, forms.EmailField):
                # Para emails, permitir @ e .
                field.validators.append(validate_email_field)
            elif isinstance(field, (forms.CharField, forms.TextField)):
                # Para texto comum, validação padrão
                field.validators.append(validate_safe_characters)

class FormularioPageForm(SafeFormMixin, WagtailAdminPageForm):
    pass





class TextFieldBlock(blocks.StructBlock):
    """Campo de texto simples"""
    label = blocks.CharBlock(label="Rótulo", max_length=255)
    placeholder = blocks.CharBlock(label="Placeholder", required=False)
    help_text = blocks.CharBlock(label="Texto de ajuda", required=False)
    required = blocks.BooleanBlock(label="Obrigatório", required=False)
    
    class Meta:
        icon = "edit"
        label = "📝 Texto"


class EmailFieldBlock(blocks.StructBlock):
    """Campo de email"""
    label = blocks.CharBlock(label="Rótulo", default="Email")
    placeholder = blocks.CharBlock(label="Placeholder", default="seuemail@exemplo.com", required=False)
    required = blocks.BooleanBlock(label="Obrigatório", default=True)
    
    class Meta:
        icon = "mail"
        label = "📧 Email"


class CPFFieldBlock(blocks.StructBlock):
    """Campo de CPF (9 dígitos)"""
    label = blocks.CharBlock(label="Rótulo", default="CPF")
    help_text = blocks.CharBlock(label="Texto de ajuda", default="Digite", required=False)
    required = blocks.BooleanBlock(label="Obrigatório", default=True)
    
    class Meta:
        icon = "user"
        label = "🆔 CPF"



class CNPJFieldBlock(blocks.StructBlock):
    """Campo de CNPJ (14 dígitos)"""
    label = blocks.CharBlock(label="Rótulo", default="CNPJ")
    help_text = blocks.CharBlock(
        label="Texto de ajuda", 
        default="Digite apenas os 14 dígitos", 
        required=False
    )
    required = blocks.BooleanBlock(label="Obrigatório", default=True)
    
    class Meta:
        icon = "user"
        label = "🏢 CNPJ (14 dígitos)"


class PhoneFieldBlock(blocks.StructBlock):
    """Campo de celular"""
    label = blocks.CharBlock(label="Rótulo", default="Celular")
    help_text = blocks.CharBlock(label="Texto de ajuda", required=False)
    required = blocks.BooleanBlock(label="Obrigatório", default=True)
    include_whatsapp = blocks.BooleanBlock(label="Perguntar se é WhatsApp", required=False)
    
    class Meta:
        icon = "mobile-alt"
        label = "📱 Celular"


class TextAreaFieldBlock(blocks.StructBlock):
    """Campo de texto longo"""
    label = blocks.CharBlock(label="Rótulo", max_length=255)
    placeholder = blocks.CharBlock(label="Placeholder", required=False)
    help_text = blocks.CharBlock(label="Texto de ajuda", required=False)
    required = blocks.BooleanBlock(label="Obrigatório", required=False)
    rows = blocks.IntegerBlock(label="Número de linhas", default=4, min_value=2, max_value=10)
    
    class Meta:
        icon = "edit"
        label = "📄 Texto Longo"


class NumberFieldBlock(blocks.StructBlock):
    """Campo numérico"""
    label = blocks.CharBlock(label="Rótulo", max_length=255)
    help_text = blocks.CharBlock(label="Texto de ajuda", required=False)
    required = blocks.BooleanBlock(label="Obrigatório", required=False)
    min_value = blocks.IntegerBlock(label="Valor mínimo", required=False)
    max_value = blocks.IntegerBlock(label="Valor máximo", required=False)
    
    class Meta:
        icon = "order"
        label = "🔢 Número"


class DateFieldBlock(blocks.StructBlock):
    """Campo de data"""
    label = blocks.CharBlock(label="Rótulo", max_length=255)
    help_text = blocks.CharBlock(label="Texto de ajuda", required=False)
    required = blocks.BooleanBlock(label="Obrigatório", required=False)
    
    class Meta:
        icon = "date"
        label = "📅 Data"








class EstadoCidadeFieldBlock(blocks.StructBlock):
    """Sistema completo Estado + Cidade em uma única classe"""
    
    # Configurações do Estado
    estado_label = blocks.CharBlock(
        label="Rótulo do Campo Estado", 
        default="Estado",
        help_text="Ex: Estado, UF, Unidade Federativa"
    )
    estado_help_text = blocks.CharBlock(
        label="Texto de Ajuda - Estado", 
        required=False
    )
    estado_required = blocks.BooleanBlock(
        label="Estado Obrigatório", 
        default=True
    )
    
    # Configurações da Cidade
    cidade_label = blocks.CharBlock(
        label="Rótulo do Campo Cidade", 
        default="Cidade",
        help_text="Ex: Cidade, Município"
    )
    cidade_help_text = blocks.CharBlock(
        label="Texto de Ajuda - Cidade", 
        required=False
    )
    cidade_required = blocks.BooleanBlock(
        label="Cidade Obrigatória", 
        default=True
    )
    
    # Configurações de Layout
    layout = blocks.ChoiceBlock(
        label="Layout dos Campos",
        choices=[
            ('vertical', '📋 Vertical (Estado acima, Cidade abaixo)'),
            ('horizontal', '↔️ Horizontal (Estado e Cidade lado a lado)'),
        ],
        default='vertical'
    )
    
    show_state_code = blocks.BooleanBlock(
        label="Mostrar Sigla do Estado",
        default=True,
        help_text="Ex: São Paulo (SP) ou apenas São Paulo"
    )
    
    class Meta:
        icon = "location"
        label = "🏛️🏙️ Estado + Cidade"
        help_text = "Sistema completo de Estado e Cidade brasileiros"
    




class DropdownFieldBlock(blocks.StructBlock):
    """Lista suspensa"""
    label = blocks.CharBlock(label="Pergunta", max_length=255)
    help_text = blocks.CharBlock(label="Texto de ajuda", required=False)
    required = blocks.BooleanBlock(label="Obrigatório", required=False)
    options = blocks.ListBlock(
        blocks.CharBlock(label="Opção", max_length=255),
        label="Opções",
        help_text="Adicione as opções. Clique no + para mais."
    )
    
    class Meta:
        icon = "list-ul"
        label = "📋 Lista Suspensa"


class RadioFieldBlock(blocks.StructBlock):
    """Botões de rádio"""
    label = blocks.CharBlock(label="Pergunta", max_length=255)
    help_text = blocks.CharBlock(label="Texto de ajuda", required=False)
    required = blocks.BooleanBlock(label="Obrigatório", required=False)
    options = blocks.ListBlock(
        blocks.CharBlock(label="Opção", max_length=255),
        label="Opções"
    )
    layout = blocks.ChoiceBlock(
        label="Layout",
        choices=[
            ('vertical', 'Vertical'),
            ('horizontal', 'Horizontal'),
        ],
        default='vertical'
    )
    
    class Meta:
        icon = "radio-empty"
        label = "🔘 Botões de Rádio"


class CheckboxFieldBlock(blocks.StructBlock):
    """Checkbox único"""
    label = blocks.CharBlock(label="Título do campo", required=True)
    help_text = blocks.CharBlock(label="Texto de ajuda", required=False)
    required = blocks.BooleanBlock(label="Obrigatório", required=False)
    
    class Meta:
        icon = "tick-inverse"
        label = "☑️ Checkbox"


class CheckboxMultipleFieldBlock(blocks.StructBlock):
    """Múltiplos checkboxes"""
    label = blocks.CharBlock(label="Pergunta", max_length=255)
    help_text = blocks.CharBlock(label="Texto de ajuda", required=False)
    required = blocks.BooleanBlock(label="Obrigatório", required=False)
    options = blocks.ListBlock(
        blocks.CharBlock(label="Opção", max_length=255),
        label="Opções"
    )
    min_selections = blocks.IntegerBlock(
        label="Mínimo de seleções", 
        default=1, 
        min_value=0,
        help_text="Quantas opções o usuário deve selecionar no mínimo"
    )
    
    class Meta:
        icon = "list-ol"
        label = "☑️ Múltiplos Checkboxes"


class FileUploadFieldBlock(blocks.StructBlock):
    """Upload de arquivo"""
    label = blocks.CharBlock(
        label="Rótulo", 
        max_length=255,
        default="Anexar arquivo"
    )
    help_text = blocks.CharBlock(
        label="Texto de ajuda", 
        required=False,
        help_text="Instruções adicionais para o usuário"
    )
    required = blocks.BooleanBlock(
        label="Obrigatório", 
        required=False,
        default=False
    )
    
    # Tipos de arquivo permitidos
    allowed_types = blocks.MultipleChoiceBlock(
        label="Tipos permitidos",
        choices=[
            ('pdf', 'PDF (.pdf)'),
            ('doc', 'Word (.doc, .docx)'),
            ('image', 'Imagens (.jpg, .png, .gif, .jpeg)'),
            ('excel', 'Excel (.xls, .xlsx)'),
            ('text', 'Texto (.txt)'),
            ('csv', 'CSV (.csv)'),
        ],
        default=['pdf', 'doc', 'image'],  # Valores padrão
        help_text="Selecione os tipos de arquivo permitidos"
    )
    
    # Tamanho máximo
    max_size_mb = blocks.IntegerBlock(
        label="Tamanho máximo (MB)", 
        default=5, 
        min_value=1, 
        max_value=100,  # Aumentei o limite máximo
        help_text="Tamanho máximo permitido por arquivo"
    )
    
    # Permitir múltiplos arquivos
    multiple_files = blocks.BooleanBlock(
        label="Permitir múltiplos arquivos",
        required=False,
        default=False,
        help_text="Permitir que o usuário selecione vários arquivos"
    )
    
    # Número máximo de arquivos (só se multiple_files = True)
    max_files = blocks.IntegerBlock(
        label="Máximo de arquivos",
        default=3,
        min_value=1,
        max_value=10,
        required=False,
        help_text="Número máximo de arquivos permitidos (só se múltiplos arquivos estiver ativado)"
    )
    
    class Meta:
        icon = "upload"
        label = "📎 Upload de Arquivo"


class RatingFieldBlock(blocks.StructBlock):
    """Avaliação com estrelas"""
    label = blocks.CharBlock(label="Pergunta", max_length=255)
    help_text = blocks.CharBlock(label="Texto de ajuda", required=False)
    required = blocks.BooleanBlock(label="Obrigatório", required=False)
    max_rating = blocks.IntegerBlock(
        label="Número máximo de estrelas", 
        default=5, 
        min_value=3, 
        max_value=10
    )
    
    class Meta:
        icon = "pick"
        label = "⭐ Avaliação"


class InfoTextBlock(blocks.StructBlock):
    """Texto informativo com RichText avançado"""
    title = blocks.CharBlock(
        label="Título", 
        max_length=255, 
        required=False,
        help_text="Título opcional para o bloco de informação"
    )
    
    content = blocks.RichTextBlock(
        label="Conteúdo",
        features=[
            'h2', 'h3', 'h4',           
            'bold', 'italic',           
            'ol', 'ul',               
            'link',                     
            'blockquote',              
            'hr',                       
            'code',                   
            'strikethrough',       
            'superscript', 'subscript',
        ],
        help_text="Use formatação rica: negrito, itálico, listas, links, etc."
    )
    
    style = blocks.ChoiceBlock(
        label="Estilo Visual",
        choices=[
            ('info', '💙 Informação (azul)'),
            ('warning', '💛 Aviso (amarelo)'),
            ('success', '💚 Sucesso (verde)'),
            ('danger', '❤️ Importante (vermelho)'),
            ('neutral', '🤍 Neutro (cinza)'),
            ('primary', '💜 Destaque (roxo)'),
        ],
        default='info',
        help_text="Escolha a cor e estilo do bloco"
    )
    
    show_icon = blocks.BooleanBlock(
        label="Mostrar ícone",
        default=True,
        required=False,
        help_text="Exibir ícone correspondente ao estilo"
    )
    
    dismissible = blocks.BooleanBlock(
        label="Pode ser fechado",
        default=False,
        required=False,
        help_text="Permitir que o usuário feche este bloco"
    )
    
    class Meta:
        icon = "help"
        label = "Texto Informativo Rico"


class DividerBlock(blocks.StructBlock):
    """Divisor visual"""
    title = blocks.CharBlock(label="Título do divisor", max_length=255, required=False)
    
    class Meta:
        icon = "horizontalrule"
        label = "➖ Divisor"


class SectionHeaderBlock(blocks.StructBlock):
    """Subtítulo/seção dentro de um step"""
    title = blocks.CharBlock(
        label="Título da Seção",
        max_length=255,
        help_text="Ex: Dados Pessoais, Informações de Contato"
    )
    subtitle = blocks.CharBlock(
        label="Subtítulo da Seção",
        max_length=500,
        required=False,
        help_text="Descrição opcional da seção"
    )
    
    class Meta:
        icon = "title"
        label = "📋 Subtítulo de Seção"


class ConditionalDropdownFieldBlock(blocks.StructBlock):
    """Dropdown condicional - baseado em outro campo"""
    label = blocks.CharBlock(label="Pergunta", max_length=255)
    help_text = blocks.CharBlock(label="Texto de ajuda", required=False)
    required = blocks.BooleanBlock(label="Obrigatório", required=False)
    
    # Campo que controla a condição
    depends_on_field = blocks.CharBlock(
        label="Depende do campo",
        max_length=255,
        help_text="ID do campo que controla esta condição (ex: country_field_123)"
    )
    depends_on_value = blocks.CharBlock(
        label="Valor que ativa este campo",
        max_length=255,
        help_text="Valor que deve ser selecionado para mostrar este campo"
    )
    
    # Opções condicionais
    conditional_options = blocks.StreamBlock([
        ('option_group', blocks.StructBlock([
            ('trigger_value', blocks.CharBlock(
                label="Valor que ativa",
                max_length=255,
                help_text="Ex: brasil"
            )),
            ('options', blocks.ListBlock(
                blocks.CharBlock(label="Opção", max_length=255),
                label="Opções para este valor"
            ))
        ], label="Grupo de Opções"))
    ], label="Opções Condicionais")
    
    class Meta:
        icon = "list-ul"
        label = "🔗 Dropdown Condicional"


class CountryFieldBlock(blocks.StructBlock):
    """Campo específico para país"""
    label = blocks.CharBlock(label="Pergunta", default="País")
    help_text = blocks.CharBlock(label="Texto de ajuda", required=False)
    required = blocks.BooleanBlock(label="Obrigatório", default=True)
    
    # Países disponíveis
    available_countries = blocks.ListBlock(
        blocks.StructBlock([
            ('code', blocks.CharBlock(
                label="Código",
                max_length=10,
                help_text="Ex: brasil, argentina, usa"
            )),
            ('name', blocks.CharBlock(
                label="Nome",
                max_length=100,
                help_text="Ex: Brasil, Argentina, Estados Unidos"
            ))
        ]),
        label="Países Disponíveis",
        default=[
            {'code': 'brasil', 'name': 'Brasil'},
            {'code': 'argentina', 'name': 'Argentina'},
            {'code': 'usa', 'name': 'Estados Unidos'},
        ]
    )
    
    class Meta:
        icon = "globe"
        label = "🌍 País"


class NomeCompletoFieldBlock(blocks.StructBlock):
    """Campo específico para nome completo"""
    label = blocks.CharBlock(label="Rótulo", default="Nome Completo")
    placeholder = blocks.CharBlock(
        label="Placeholder", 
        default="Digite seu nome completo", 
        required=False
    )
    help_text = blocks.CharBlock(
        label="Texto de ajuda", 
        default="Informe seu nome completo como no documento", 
        required=False
    )
    required = blocks.BooleanBlock(label="Obrigatório", default=True)
    min_length = blocks.IntegerBlock(
        label="Tamanho mínimo", 
        default=3, 
        min_value=1, 
        help_text="Número mínimo de caracteres"
    )
    max_length = blocks.IntegerBlock(
        label="Tamanho máximo", 
        default=255, 
        min_value=10, 
        max_value=500,
        help_text="Número máximo de caracteres"
    )
    
    class Meta:
        icon = "user"
        label = "👤 Nome Completo"




BASE_FORM_FIELD_BLOCKS = [
    ('section_header', SectionHeaderBlock()), 
    ('text_field', TextFieldBlock()),
    ('email_field', EmailFieldBlock()),
    ('cpf_field', CPFFieldBlock()),
    ('phone_field', PhoneFieldBlock()),
    ('textarea_field', TextAreaFieldBlock()),
    ('number_field', NumberFieldBlock()),
    ('date_field', DateFieldBlock()),
    ('dropdown_field', DropdownFieldBlock()),
    ('country_field', CountryFieldBlock()),  
    ('radio_field', RadioFieldBlock()),
    ('checkbox_field', CheckboxFieldBlock()),
    ('checkbox_multiple_field', CheckboxMultipleFieldBlock()),
    ('file_upload_field', FileUploadFieldBlock()),
    ('rating_field', RatingFieldBlock()),
    ('info_text', InfoTextBlock()),
    ('divider', DividerBlock()),
]

# 2. DEPOIS: Definir as classes que usam BASE_FORM_FIELD_BLOCKS

class CheckboxMultiRedirectFieldBlock(blocks.StructBlock):
    """Checkbox com múltiplas opções de redirecionamento - Sistema avançado"""
    
    # Pergunta principal
    label = blocks.CharBlock(
        label="Pergunta/Título",
        max_length=255,
        help_text="Ex: Informações sobre dependentes"
    )
    
    help_text = blocks.CharBlock(
        label="Texto de ajuda", 
        required=False,
        help_text="Instrução adicional para o usuário"
    )
    
    required = blocks.BooleanBlock(
        label="Obrigatório", 
        default=True
    )
    
    # Tipo do campo
    field_type = blocks.ChoiceBlock(
        label="Tipo de campo",
        choices=[
            ('checkbox', '☑️ Checkbox único (sim/não)'),
            ('radio', '🔘 Múltiplas opções (radio)'),
            ('dropdown', '📋 Lista suspensa'),
        ],
        default='checkbox',
        help_text="Escolha como o usuário vai responder"
    )
    
    # Opções com redirecionamentos
    redirect_options = blocks.StreamBlock([
        ('option', blocks.StructBlock([
            ('value', blocks.CharBlock(
                label="Texto da opção",
                max_length=255,
                help_text="Ex: 'Sim, tenho filhos', 'Não tenho dependentes', 'Sou menor de idade'"
            )),
            
            ('action', blocks.ChoiceBlock(
                label="Ação quando escolher esta opção",
                choices=[
                    ('continue', '➡️ Continuar normalmente'),
                    ('next_step', '⏩ Pular para próxima etapa'),
                    ('specific_section', '🎯 Ir para seção específica'),
                    ('skip_to_end', '⏭️ Finalizar formulário'),
                    ('show_fields', '👁️ Mostrar campos condicionais'),
                ],
                default='continue'
            )),
            
            ('target_section_title', blocks.CharBlock(
                label="Nome da seção de destino",
                max_length=255,
                required=False,
                help_text="Nome exato do divisor (necessário se escolheu 'Ir para seção específica')"
            )),
            
            ('redirect_message', blocks.RichTextBlock(
                label="Mensagem explicativa",
                required=False,
                features=['bold', 'italic', 'link'],
                help_text="Mensagem mostrada ao usuário antes do redirecionamento"
            )),
            
            ('fields_to_show', blocks.StreamBlock(
                BASE_FORM_FIELD_BLOCKS,  # Agora já está definido acima
                label="Campos condicionais",
                required=False,
                help_text="Campos que aparecem apenas se esta opção for escolhida"
            )),
            
            ('delay_seconds', blocks.IntegerBlock(
                label="Delay antes do redirecionamento (segundos)",
                default=1,
                min_value=0,
                max_value=10,
                required=False,
                help_text="Tempo de espera antes de executar o redirecionamento"
            ))
        ], label="Opção com Redirecionamento"))
    ], 
    label="Opções e Ações",
    help_text="Configure as opções e o que acontece para cada uma",
    min_num=1,
    max_num=500
    )
    
    class Meta:
        icon = "redirect"
        label = "🔀 Checkbox Multi-Redirecionamento"


class ConditionalFieldBlock(blocks.StructBlock):
    """Campo com ramificações condicionais - Super simples!"""
    
    # Pergunta principal
    label = blocks.CharBlock(
        label="Pergunta",
        max_length=255,
        help_text="Ex: Qual país? / Precisa de acessibilidade?"
    )
    
    help_text = blocks.CharBlock(
        label="Texto de ajuda", 
        required=False
    )
    
    required = blocks.BooleanBlock(
        label="Obrigatório", 
        default=True
    )
    
    # Tipo do campo principal
    field_type = blocks.ChoiceBlock(
        label="Tipo do campo",
        choices=[
            ('dropdown', '📋 Lista Suspensa'),
            ('radio', '🔘 Botões de Rádio'),
        ],
        default='dropdown'
    )
    
    # Opções com ramificações
    conditional_options = blocks.StreamBlock([
        ('option', blocks.StructBlock([
            ('value', blocks.CharBlock(
                label="Opção",
                max_length=255,
                help_text="Ex: Brasil, Sim, Empresa"
            )),
            ('action', blocks.ChoiceBlock(
                label="Quando escolher esta opção",
                choices=[
                    ('show_fields', '👁️ Mostrar campos'),
                    ('nothing', '➡️ Não fazer nada (pular)'),
                    ('end_form', '⛔ Encerrar formulário'),
                ],
                default='nothing'
            )),
            ('fields_to_show', blocks.StreamBlock(
                BASE_FORM_FIELD_BLOCKS,  # Agora já está definido acima
                label="Campos que aparecem",
                required=False,
                help_text="Campos que só aparecem se esta opção for escolhida"
            ))
        ], label="Opção com Ação"))
    ], 
    label="Opções e Ramificações",
    help_text="Configure o que acontece para cada opção"
    )
    
    class Meta:
        icon = "list-ul"
        label = "🔗 Campo Condicional"




class SmartNavigationFieldBlock(blocks.StructBlock):
    """Campo que pode redirecionar para qualquer seção do formulário"""
    
    # Pergunta principal
    label = blocks.CharBlock(
        label="Pergunta",
        max_length=255,
        help_text="Ex: Você possui conhecimento na temática do curso?"
    )
    
    help_text = blocks.CharBlock(
        label="Texto de ajuda", 
        required=False
    )
    
    required = blocks.BooleanBlock(
        label="Obrigatório", 
        default=True
    )
    
    # Tipo do campo
    field_type = blocks.ChoiceBlock(
        label="Tipo de campo",
        choices=[
            ('radio', '🔘 Sim/Não (Radio)'),
            ('dropdown', '📋 Lista Suspensa'),
            ('checkbox', '☑️ Checkbox único'),
        ],
        default='radio'
    )
    
    # Opções com navegação
    navigation_options = blocks.StreamBlock([
        ('option', blocks.StructBlock([
            ('value', blocks.CharBlock(
                label="Texto da opção",
                max_length=255,
                help_text="Ex: 'Sim', 'Não', 'Concordo'"
            )),
            
            ('action_type', blocks.ChoiceBlock(
                label="Tipo de ação",
                choices=[
                    ('continue', '➡️ Continuar para próximo campo'),
                    ('jump_to_section', '🎯 Pular para seção específica'),
                    ('finish_form', '✅ Finalizar formulário'),
                    ('show_message_and_finish', '📝 Mostrar mensagem e finalizar'),
                ],
                default='continue'
            )),
            
            ('target_section_name', blocks.CharBlock(
                label="Nome da seção de destino",
                max_length=255,
                required=False,
                help_text="Nome EXATO do divisor de destino (ex: 'DADOS PESSOAIS E PROFISSIONAIS')"
            )),
            
            ('finish_message', blocks.RichTextBlock(
                label="Mensagem de finalização",
                required=False,
                features=['bold', 'italic'],
                help_text="Mensagem mostrada quando formulário é finalizado por esta opção"
            )),
            
            ('custom_thank_you_title', blocks.CharBlock(
                label="Título personalizado de agradecimento",
                max_length=255,
                required=False,
                help_text="Ex: 'A ENAP AGRADECE SUA PARTICIPAÇÃO!'"
            ))
        ], label="Opção de Navegação"))
    ], 
    label="Opções e Navegação",
    help_text="Configure para onde cada resposta leva o usuário",
    min_num=1,
    max_num=100
    )
    
    class Meta:
        icon = "redirect"
        label = "🧭 Campo com Navegação Inteligente"


class SectionDividerBlock(blocks.StructBlock):
    """Divisor que marca seções navegáveis"""
    section_name = blocks.CharBlock(
        label="Nome da Seção",
        max_length=255,
        help_text="Nome único para navegação (ex: 'DADOS PESSOAIS')"
    )
    
    title = blocks.CharBlock(
        label="Título visível",
        max_length=255,
        help_text="Título que aparece para o usuário"
    )
    
    subtitle = blocks.CharBlock(
        label="Subtítulo",
        max_length=500,
        required=False
    )
    
    is_hidden_by_default = blocks.BooleanBlock(
        label="Seção oculta por padrão",
        default=False,
        help_text="Se marcado, só aparece quando navegado para ela"
    )
    
    class Meta:
        icon = "horizontalrule"
        label = "📍 Divisor de Seção Navegável"




FORM_CONDICIONAL = [
    ('checkbox_multi_redirect_field', CheckboxMultiRedirectFieldBlock()),
    ('conditional_field', ConditionalFieldBlock()),
    ('section_divider', SectionDividerBlock()),
    ('smart_navigation_field', SmartNavigationFieldBlock()),
    ('section_header', SectionHeaderBlock()), 
    ('text_field', TextFieldBlock()),
    ('email_field', EmailFieldBlock()),
    ('cpf_field', CPFFieldBlock()),
    ('cnpj_field', CNPJFieldBlock()),
    ('phone_field', PhoneFieldBlock()),
    ('textarea_field', TextAreaFieldBlock()),
    ('number_field', NumberFieldBlock()),
    ('date_field', DateFieldBlock()),
    ('dropdown_field', DropdownFieldBlock()),
    ('estado_cidade_field', EstadoCidadeFieldBlock()),
    ('radio_field', RadioFieldBlock()),
    ('checkbox_field', CheckboxFieldBlock()),
    ('checkbox_multiple_field', CheckboxMultipleFieldBlock()),
    ('file_upload_field', FileUploadFieldBlock()),
    ('rating_field', RatingFieldBlock()),
    ('info_text', InfoTextBlock()),
    ('divider', DividerBlock()),
    ('nome_completo_field', NomeCompletoFieldBlock()),  
]



class ConditionalFieldBlockCondicional(blocks.StructBlock):
    """Campo com ramificações condicionais"""
    
    # Pergunta principal
    label_con = blocks.CharBlock(
        label="Pergunta",
        required=False,
        max_length=255,
        help_text="Ex: Qual país? / Precisa de acessibilidade?"
    )
    
    help_text_con = blocks.CharBlock(
        label="Texto de ajuda", 
        required=False
    )
    
    required_con = blocks.BooleanBlock(
        label="Obrigatório", 
        default=True
    )
    
    # Tipo do campo principal
    field_type_con = blocks.ChoiceBlock(
        label="Tipo do campo",
        choices=[
            ('dropdown', '📋 Lista Suspensa'),
            ('radio', '🔘 Botões de Rádio'),
        ],
        default='dropdown'
    )
    
    # Opções com ramificações
    conditional_options_con = blocks.StreamBlock([
        ('option_con', blocks.StructBlock([
            ('value_con', blocks.CharBlock(
                label="Opção",
                max_length=255,
                help_text="Ex: Brasil, Sim, Empresa"
            )),
            ('action_con', blocks.ChoiceBlock(
                label="Quando escolher esta opção",
                choices=[
                    ('show_fields_con', '👁️ Mostrar campos'),
                    ('nothing_con', '➡️ Não fazer nada (pular)'),
                ],
                default='nothing_con'
            )),
            ('fields_to_show_con', blocks.StreamBlock(
                FORM_CONDICIONAL, 
                label="Campos que aparecem",
                required=False,
                help_text="Campos que só aparecem se esta opção for escolhida"
            ))
        ], label="Opção com Ação"))
    ], 
    label="Opções e Ramificações",
    help_text="Configure o que acontece para cada opção"
    )
    
    class Meta:
        icon = "list-ul"
        label = "🔗 Campo Condicional - Condicional"






FORM_FIELD_BLOCKS = BASE_FORM_FIELD_BLOCKS + [
    ('checkbox_multi_redirect_field', CheckboxMultiRedirectFieldBlock()),
    ('conditional_field', ConditionalFieldBlock()),
    ('conditional_field_condicional', ConditionalFieldBlockCondicional()),
    ('section_divider', SectionDividerBlock()),
    ('smart_navigation_field', SmartNavigationFieldBlock()),
    ('section_header', SectionHeaderBlock()), 
    ('text_field', TextFieldBlock()),
    ('email_field', EmailFieldBlock()),
    ('cpf_field', CPFFieldBlock()),
    ('cnpj_field', CNPJFieldBlock()),
    ('phone_field', PhoneFieldBlock()),
    ('textarea_field', TextAreaFieldBlock()),
    ('number_field', NumberFieldBlock()),
    ('date_field', DateFieldBlock()),
    ('dropdown_field', DropdownFieldBlock()),
    ('estado_cidade_field', EstadoCidadeFieldBlock()),
    ('radio_field', RadioFieldBlock()),
    ('checkbox_field', CheckboxFieldBlock()),
    ('checkbox_multiple_field', CheckboxMultipleFieldBlock()),
    ('file_upload_field', FileUploadFieldBlock()),
    ('rating_field', RatingFieldBlock()),
    ('info_text', InfoTextBlock()),
    ('divider', DividerBlock()),
    ('nome_completo_field', NomeCompletoFieldBlock()),  
]



class FormStepBlock(StructBlock):
    """Bloco para uma etapa do formulário - apenas logo e campos"""
    
    logo = ImageChooserBlock(
        label="Logo/Imagem da Etapa",
        required=False,
        help_text="Imagem que será exibida no cabeçalho desta etapa (opcional)"
    )

    order = CharBlock(
        label="Ordem da Etapa",
        max_length=3,
        help_text="Número para definir a ordem (ex: 1, 2, 3...)",
        default="1"
    )
    
    logo_alt = CharBlock(
        label="Texto Alternativo da Logo",
        max_length=255,
        required=False,
        help_text="Descrição da imagem para acessibilidade"
    )
    
    fields = StreamBlock(
        FORM_FIELD_BLOCKS,
        label="Campos desta Etapa",
        required=False,
        min_num=0,          
        max_num=500,
        help_text="Adicione os campos que aparecerão nesta etapa"
    )
    
    class Meta:
        icon = "form"
        label = "📋 Etapa do Formulário"



class FormFieldScoring(models.Model):
    """Armazena pontuação configurada para cada campo"""
    formulario_page = models.ForeignKey('FormularioPage', on_delete=models.CASCADE, related_name='field_scorings')
    field_id = models.CharField(max_length=255, verbose_name="ID do Campo")
    field_label = models.CharField(max_length=500, verbose_name="Pergunta")
    field_type = models.CharField(max_length=100, verbose_name="Tipo de Campo")
    scoring_data = models.JSONField(verbose_name="Dados de Pontuação", default=dict)
    
    class Meta:
        verbose_name = "Pontuação do Campo"
        verbose_name_plural = "Pontuações dos Campos"
        unique_together = ['formulario_page', 'field_id']
    
    def __str__(self):
        return f"{self.field_label} ({self.field_type})"


#  MODELO para submissões com pontuação
class FormularioSubmissionScored(models.Model):
    """Submissões com pontuação calculada"""
    original_submission = models.OneToOneField(
        'FormularioSubmission', 
        on_delete=models.CASCADE,
        related_name='scoring'
    )
    total_score = models.FloatField(verbose_name="Pontuação Total", default=0)
    score_details = models.JSONField(verbose_name="Detalhes da Pontuação", default=list)
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Pontuação da Submissão"
        verbose_name_plural = "Pontuações das Submissões"
    
    def __str__(self):
        return f"Pontuação: {self.total_score} pts"





class FormularioPage(Page):
    """Página de formulário com steps dinâmicos - Wagtail 7.0"""

    template = "enap_designsystem/form_templates/formulario_page.html"
    
    # Configurações gerais
    intro = RichTextField(
        verbose_name="Introdução",
        blank=True,
        help_text='Texto de introdução do formulário'
    )
    
    # 🚀 STEPS DINÂMICOS
    form_steps = StreamField(
        [('form_step', FormStepBlock())],
        verbose_name="Etapas do Formulário",
        use_json_field=True,
        min_num=1,
        max_num=100,
        help_text="Adicione quantas etapas precisar (mínimo 1, máximo 10)"
    )
    
    # Página de sucesso
    thank_you_text = RichTextField(
        verbose_name="Texto de agradecimento",
        blank=True,
        help_text='Texto exibido após envio do formulário'
    )
    
    # Configurações visuais
    form_title = models.CharField(
        verbose_name="Título do formulário",
        max_length=255,
        default="Formulário de Inscrição"
    )
    form_subtitle = models.CharField(
        verbose_name="Subtítulo",
        max_length=255,
        blank=True
    )
    primary_color = models.CharField(
        verbose_name="Cor primária",
        max_length=7,
        default="#2A5E2C",
        help_text='Código hexadecimal (ex: #2A5E2C)'
    )

    secondary_color = models.CharField(
        verbose_name="Cor de texto",
        max_length=7,
        default="#2A5E2C",
        help_text='Código hexadecimal (ex: #2A5E2C)'
    )

    logo_section = StreamField(
        [('logo', ImageChooserBlock(
            label="Logo",
            help_text="Selecione uma imagem para o logo"
        ))],
        verbose_name="Logo",
        use_json_field=True,
        max_num=100,  # Só permite uma logo
        blank=True,
        help_text="Adicione o logo do formulário"
    )

    background_image_fundo = StreamField(
    [('background_image_stream', ImageChooserBlock(
        label="Imagem de Fundo",
        help_text="Selecione uma imagem de fundo para o formulário"
    ))],
    verbose_name="Imagem de Fundo",
    use_json_field=True,
    max_num=500,
    blank=True,
    help_text="Adicione uma imagem de fundo para o formulário"
    )

    thank_you_image_section = StreamField(
    [('thank_you_image', ImageChooserBlock(
        label="Imagem de Agradecimento",
        help_text="Selecione uma imagem para a tela de agradecimento"
    ))],
    verbose_name="Imagem de Agradecimento",
    use_json_field=True,
    max_num=500,
    blank=True,
    help_text="Adicione uma imagem para a tela de sucesso"
    )

    custom_link = models.CharField(
        verbose_name="Link personalizado",
        max_length=500,
        blank=True,
        help_text="Digite a URL completa (ex: https://exemplo.com)"
    )

    success_button_text = models.CharField(
        verbose_name="Texto do botão",
        max_length=100,
        default="Voltar ao início",
        help_text="Texto que aparece no botão"
    )
    
    # 📧 CONFIGURAÇÕES DE EMAIL MELHORADAS
    send_confirmation_email = models.BooleanField(
        verbose_name="Enviar email de confirmação",
        default=True,
        help_text="Enviar email automático para o usuário"
    )
    confirmation_email_subject = models.CharField(
        verbose_name="Assunto do email",
        max_length=255,
        default="Confirmação de Inscrição"
    )
    email_type = models.CharField(
        verbose_name="Tipo de email",
        max_length=10,
        choices=[
            ('html', 'HTML (template bonito)'),
            ('text', 'Texto simples'),
        ],
        default='html',
        help_text="Formato do email de confirmação"
    )
    admin_email = models.EmailField(
        verbose_name="Email do administrador",
        blank=True,
        help_text="Email para receber notificações (ex: admin@enap.gov.br)"
    )

    enable_scoring = models.BooleanField(
    verbose_name="Ativar Sistema de Pontuação",
    default=False,
    help_text="Ativar para poder configurar pontos (invisível para usuários)"
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('form_title'),
            FieldPanel('form_subtitle'),
            FieldPanel('logo_section'),
        ], "🎬 Tela de Boas-vindas"),
        
        FieldPanel('intro'),

        MultiFieldPanel([
            FieldPanel('enable_scoring'),
        ], "Sistema de Pontuação (Oculto)"),
        
        FieldPanel('form_steps'),
        
        MultiFieldPanel([
            FieldPanel('thank_you_text'),
            FieldPanel('thank_you_image_section'),
            FieldPanel('custom_link'),
            FieldPanel('success_button_text'),
        ], "🎉 Tela de Agradecimento"),
        
        MultiFieldPanel([
            FieldPanel('background_image_fundo'),
            FieldPanel('primary_color'),
            FieldPanel('secondary_color'),
        ], "🎨 Aparência"),
        
        MultiFieldPanel([
            FieldPanel('send_confirmation_email'),
            FieldPanel('email_type'),  # NOVO
            FieldPanel('confirmation_email_subject'),
            FieldPanel('admin_email'),
        ], "📧 Configurações de Email"),
    ]

    def save_form_submission(self, form_data, files_data, request):
        """Salva a submissão no banco de dados com arquivos em subpasta por ID"""
        
        # Primeiro: cria submissão inicial com placeholders
        submission = FormularioSubmission.objects.create(
            page=self,
            form_data=form_data,
            files_data={},  # Preencheremos depois
            uploaded_files={},  # Preencheremos depois
            user_ip=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        saved_files_paths = {}
        files_metadata = {}

        for field_id, uploaded_file in files_data.items():
            try:
                # Gerar nome único
                file_extension = os.path.splitext(uploaded_file.name)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"

                # Adiciona o ID da submissão no caminho
                file_path = f"form_submissions/{self.pk}/{submission.id}/{unique_filename}"

                # Salvar arquivo
                saved_path = default_storage.save(file_path, uploaded_file)
                saved_files_paths[field_id] = saved_path

                # Metadados detalhados
                files_metadata[field_id] = {
                    'original_name': uploaded_file.name,
                    'saved_path': saved_path,
                    'size': uploaded_file.size,
                    'content_type': uploaded_file.content_type,
                    'upload_date': timezone.now().isoformat()
                }

            except Exception as e:
                logger.error(f"Erro ao salvar arquivo {field_id}: {str(e)}")

        # Atualiza a submissão com os dados reais dos arquivos
        submission.files_data = files_metadata
        submission.uploaded_files = saved_files_paths
        submission.save(update_fields=['files_data', 'uploaded_files'])

        return submission

    def get_total_steps(self):
        """Retorna o número total de etapas (incluindo boas-vindas e sucesso)"""
        return len(self.form_steps) + 2  # +2 para boas-vindas e sucesso

    def serve(self, request, *args, **kwargs):
        """Processa o formulário"""
        if request.method == 'POST':
            return self.process_form_submission(request)
        return super().serve(request, *args, **kwargs)

    def process_form_submission(self, request):
        """Processa os dados do formulário"""
        form_data = {}
        files_data = {}  # ← Separar arquivos dos dados
        
        # Coletar dados de todas as etapas
        for step in self.get_all_steps():
            for block in step['fields']:
                field_id = f"{block.block_type}_{block.id}"
                
                # Pular blocos informativos e seções
                if block.block_type in ['info_text', 'divider', 'section_header']:
                    continue
                
                # PROCESSAR UPLOAD DE ARQUIVOS SEPARADAMENTE
                if block.block_type == 'file_upload_field':
                    if field_id in request.FILES:
                        uploaded_file = request.FILES[field_id]
                        
                        # Salvar informações do arquivo (não o arquivo em si) no form_data
                        form_data[field_id] = {
                            'filename': uploaded_file.name,
                            'size': uploaded_file.size,
                            'content_type': uploaded_file.content_type,
                        }
                        
                        # Salvar arquivo real em files_data para processamento
                        files_data[field_id] = uploaded_file
                    continue
                
                # Processar outros tipos de campo
                if block.block_type == 'checkbox_multiple_field':
                    values = request.POST.getlist(field_id)
                    if values:
                        form_data[field_id] = values
                else:
                    value = request.POST.get(field_id, '')
                    if value:
                        form_data[field_id] = value
        
        # Validar dados obrigatórios
        errors = self.validate_form_data(form_data, request)
        if errors:
            context = self.get_context(request)
            context['form_errors'] = errors
            context['form_data'] = form_data
            return render(request, self.get_template(request), context)
        
        # Salvar submissão
        submission = self.save_form_submission(form_data, files_data, request)
        
        # 📧 ENVIAR EMAILS COM SIMPLEEEMAILSERVICE
        email_results = self.send_emails_with_service(form_data, submission)
        
        # Log dos resultados
        logger.info(f"Submissão {submission.id} processada. Emails: {email_results}")

        # Redirecionar com status dos emails
        success_url = f'{request.path}?success=1'
        if email_results.get('user_sent'):
            success_url += '&email_sent=1'
        if email_results.get('admin_sent'):
            success_url += '&admin_notified=1'
            
        return redirect(success_url)

    def send_emails_with_service(self, form_data, submission):
        """Envia emails usando SimpleEmailService"""
        results = {'user_sent': False, 'admin_sent': False}
        
        # Extrair informações do usuário
        user_info = self.extract_user_info(form_data)
        submit_date = submission.submit_time.strftime('%d/%m/%Y às %H:%M')
        
        # 📧 Email de confirmação para usuário
        if self.send_confirmation_email and user_info['email']:
            try:
                results['user_sent'] = SimpleEmailService.send_user_confirmation(
                    user_email=user_info['email'],
                    user_name=user_info['name'],
                    form_title=self.form_title or self.title,
                    form_data=form_data,
                    submission_date=submit_date
                )
                
                if results['user_sent']:
                    logger.info(f"✅ Email de confirmação enviado para {user_info['email']}")
                else:
                    logger.error(f"❌ Falha ao enviar email para {user_info['email']}")
                    
            except Exception as e:
                logger.error(f"❌ Erro no email do usuário: {str(e)}")
        
        # 🔔 Notificação para administrador
        if self.admin_email:
            try:
                results['admin_sent'] = SimpleEmailService.send_admin_notification(
                    admin_email=self.admin_email,
                    user_name=user_info['name'],
                    user_email=user_info['email'] or 'Não informado',
                    form_title=self.form_title or self.title,
                    form_data=form_data,
                    submission_date=submit_date,
                    user_ip=submission.user_ip
                )
                
                if results['admin_sent']:
                    logger.info(f"✅ Notificação admin enviada para {self.admin_email}")
                else:
                    logger.error(f"❌ Falha ao enviar notificação para {self.admin_email}")
                    
            except Exception as e:
                logger.error(f"❌ Erro no email do admin: {str(e)}")
        
        return results

    def extract_user_info(self, form_data):
        """Extrai informações básicas do usuário"""
        user_info = {
            'name': 'Usuário',
            'email': None,
            'phone': None
        }
        
        for step in self.get_all_steps():
            for block in step['fields']:
                field_id = f"{block.block_type}_{block.id}"
                value = form_data.get(field_id, '')
                
                if not value:
                    continue
                
                # Procurar email
                if block.block_type == 'email_field':
                    user_info['email'] = value
                
                # Procurar nome (primeiro campo texto com 'nome' no label)
                elif (block.block_type == 'text_field' and 
                      any(keyword in block.value.get('label', '').lower() 
                          for keyword in ['nome', 'name']) and
                      user_info['name'] == 'Usuário'):  # Só pegar o primeiro nome encontrado
                    user_info['name'] = value.split()[0] if value else 'Usuário'
                
                # Procurar telefone
                elif block.block_type == 'phone_field' and not user_info['phone']:
                    user_info['phone'] = value
        
        return user_info

    def should_process_conditional_field(self, block, form_data, request):
        """Verifica se um campo condicional deve ser processado"""
        if block.block_type == 'city_field':
            country_field_id = block.value.get('country_field_id', '')
            if country_field_id:
                country_value = request.POST.get(country_field_id, '')
                return bool(country_value)
        
        elif block.block_type == 'conditional_dropdown_field':
            depends_on_field = block.value.get('depends_on_field', '')
            depends_on_value = block.value.get('depends_on_value', '')
            if depends_on_field and depends_on_value:
                field_value = request.POST.get(depends_on_field, '')
                return field_value == depends_on_value
        
        return True
    
    def get_section_map(self):
        """Cria mapa de seções para navegação"""
        section_map = {}
        current_section = None
        
        for step in self.get_all_steps():
            for block in step['fields']:
                if block.block_type == 'section_divider':
                    section_name = block.value['section_name']
                    section_map[section_name] = {
                        'step': step['number'],
                        'block_id': block.id,
                        'title': block.value['title'],
                        'hidden_by_default': block.value.get('is_hidden_by_default', False)
                    }
        
        return section_map
    
    def get_navigation_data(self):
        """Coleta dados de navegação de todos os campos inteligentes"""
        navigation_data = {}
        
        for step in self.get_all_steps():
            for block in step['fields']:
                if block.block_type == 'smart_navigation_field':
                    field_id = f"smart_navigation_field_{block.id}"
                    options_data = {}
                    
                    for option in block.value.get('navigation_options', []):
                        options_data[option.value['value']] = {
                            'action_type': option.value['action_type'],
                            'target_section': option.value.get('target_section_name', ''),
                            'finish_message': option.value.get('finish_message', ''),
                            'thank_you_title': option.value.get('custom_thank_you_title', '')
                        }
                    
                    navigation_data[field_id] = options_data
        
        return navigation_data
    
    def get_context(self, request, *args, **kwargs):
        """Adiciona dados de navegação ao contexto"""
        context = super().get_context(request, *args, **kwargs)
        
        # Dados existentes
        context['total_form_steps'] = len(self.form_steps)
        context['all_steps'] = self.get_all_steps()
        
        # Novos dados de navegação
        context['section_map'] = self.get_section_map()
        context['navigation_data'] = self.get_navigation_data()
        context['section_map_json'] = json.dumps(self.get_section_map())
        context['navigation_data_json'] = json.dumps(self.get_navigation_data())
        
        return context


    # def get_estados_cidades_data(self):
    #     """Busca os dados de estados e distritos da API do IBGE"""
    #     estados_cidades = {}

    #     # Lista de estados
    #     estados_uf = ["SP", "RJ", "MG", "ES", "PR", "SC", "RS", "DF", "GO", "MT", "MS", "BA", "SE", "PE", "AL", "PB", "RN", "CE", "PI", "MA", "TO", "PA", "AP", "RR", "AM", "RO", "AC"]
        
    #     for uf in estados_uf:
    #         url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/distritos"
    #         response = requests.get(url)

    #         if response.status_code == 200:
    #             dados = response.json()

    #             # Pega o nome do estado de maneira mais precisa
    #             nome_estado = dados[0]['municipio']['microrregiao']['mesorregiao']['UF']['nome']

    #             # Pega os nomes dos distritos (cidades)
    #             cidades = [distrito['nome'] for distrito in dados]

    #             # Armazena o estado e as cidades
    #             estados_cidades[uf] = {
    #                 'nome': nome_estado,
    #                 'cidades': cidades
    #             }
    #         else:
    #             print(f"Erro ao acessar dados para o estado {uf}")

    #     return estados_cidades

    def get_context(self, request, *args, **kwargs):
        """Adiciona contexto personalizado - VERSÃO FINAL CORRIGIDA"""
        context = super().get_context(request, *args, **kwargs)
        
        # Adicionar informações dos steps
        context['total_form_steps'] = len(self.form_steps)
        context['all_steps'] = self.get_all_steps()
        
        # Dados para campos condicionais
        conditional_data = self.build_conditional_data()
        context['conditional_data_json'] = json.dumps(conditional_data)
        
        # 🆕 DADOS DOS ESTADOS E CIDADES - ESTAVA FALTANDO AQUI!
        #context['estados_cidades'] = self.get_estados_cidades_data()
        
        # 👤 EXTRAIR NOME COMPLETO - SEMPRE DO nome_completo_field
        full_name = 'Usuário'
        
        if request.method == 'POST':
            # Procurar especificamente pelo nome_completo_field
            for key, value in request.POST.items():
                if key.startswith('nome_completo_field_') and value:
                    full_name = value.strip()
                    break  # Encontrou, para de procurar
        
        context['full_name'] = full_name
        
        # Se é uma submissão bem-sucedida
        if request.GET.get('success'):
            context['form_success'] = True
            context['email_sent'] = request.GET.get('email_sent') == '1'
            context['admin_notified'] = request.GET.get('admin_notified') == '1'

        return context



    def validate_form_data(self, form_data, request):
        """Valida os dados do formulário - incluindo campos condicionais"""
        errors = {}
        
        for step in self.get_all_steps():
            for block in step['fields']:
                if block.block_type in ['info_text', 'divider', 'section_header']:
                    continue
                    
                field_id = f"{block.block_type}_{block.id}"
                value = form_data.get(field_id, '')
                
                # Verificar se campo condicional deve ser validado
                if block.block_type in ['city_field', 'conditional_dropdown_field']:
                    if not self.should_process_conditional_field(block, form_data, request):
                        continue
                
                # Verificar campos obrigatórios
                if block.value.get('required', False):
                    if not value or (isinstance(value, list) and not any(value)):
                        errors[field_id] = 'Este campo é obrigatório'
                        continue
                
                # Validações específicas
                if block.block_type == 'email_field' and value:
                    if not self.validate_email(value):
                        errors[field_id] = 'Email inválido'
                
                elif block.block_type == 'cpf_field' and value:
                    if not self.validate_cpf_9_digits(value):
                        errors[field_id] = 'CPF deve ter exatamente 11 dígitos'
                
                elif block.block_type == 'phone_field' and value:
                    if not self.validate_phone(value):
                        errors[field_id] = 'Telefone inválido'
        
        return errors

    def validate_email(self, email):
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def validate_cpf_9_digits(self, cpf):
        """Valida CPF com 11 dígitos"""
        cpf_digits = re.sub(r'[^0-9]', '', cpf)
        return len(cpf_digits) == 11 and cpf_digits.isdigit()

    def validate_phone(self, phone):
        """Valida telefone brasileiro"""
        phone_digits = re.sub(r'[^0-9]', '', phone)
        return len(phone_digits) in [10, 11]

    def get_client_ip(self, request):
        """Obtém IP do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def build_conditional_data(self):
        """Constrói dados para campos condicionais"""
        conditional_data = {}
        
        for step in self.get_all_steps():
            for block in step['fields']:
                field_id = f"{block.block_type}_{block.id}"
                
                if block.block_type == 'city_field':
                    # Dados de cidade por país
                    cities_data = {}
                    for country_cities in block.value.get('cities_by_country', []):
                        country_code = country_cities.value['country_code']
                        cities = country_cities.value['cities']
                        cities_data[country_code] = cities
                    
                    conditional_data[field_id] = {
                        'type': 'city_field',
                        'depends_on': block.value.get('country_field_id', ''),
                        'cities_by_country': cities_data
                    }
                
                elif block.block_type == 'conditional_dropdown_field':
                    # Dados de dropdown condicional
                    options_data = {}
                    for option_group in block.value.get('conditional_options', []):
                        trigger_value = option_group.value['trigger_value']
                        options = option_group.value['options']
                        options_data[trigger_value] = options
                    
                    conditional_data[field_id] = {
                        'type': 'conditional_dropdown',
                        'depends_on': block.value.get('depends_on_field', ''),
                        'depends_on_value': block.value.get('depends_on_value', ''),
                        'options_by_value': options_data
                    }
        
        return conditional_data

    def save_field_scoring(self, field_id, scoring_data):
        '''Salva pontuação para um campo'''
        field_info = None
        
        for field in self.extract_scorable_fields():
            if field['field_id'] == field_id:
                field_info = field
                break
        
        if not field_info:
            return False
        
        scoring, created = FormFieldScoring.objects.get_or_create(
            formulario_page=self,
            field_id=field_id,
            defaults={
                'field_label': field_info['field_label'],
                'field_type': field_info['field_type'],
                'scoring_data': scoring_data
            }
        )
        
        if not created:
            scoring.scoring_data = scoring_data
            scoring.save()
        
        return True

    def calculate_submission_score(self, submission):
        '''Calcula pontuação para uma submissão'''
        if not self.enable_scoring:
            return 0, []
        
        total_score = 0
        score_details = []
        form_data = submission.form_data
        
        field_scorings = FormFieldScoring.objects.filter(formulario_page=self)
        
        for scoring in field_scorings:
            field_id = scoring.field_id
            user_response = form_data.get(field_id)
            
            if not user_response:
                continue
            
            field_score = 0
            
            if scoring.field_type in ['dropdown_field', 'radio_field']:
                option_scores = scoring.scoring_data.get('option_scores', {})
                field_score = option_scores.get(user_response, 0)
            
            elif scoring.field_type == 'checkbox_multiple_field':
                if isinstance(user_response, list):
                    option_scores = scoring.scoring_data.get('option_scores', {})
                    calculation_method = scoring.scoring_data.get('calculation_method', 'sum')
                    
                    scores = [option_scores.get(option, 0) for option in user_response]
                    
                    if calculation_method == 'sum':
                        field_score = sum(scores)
                    elif calculation_method == 'max':
                        field_score = max(scores) if scores else 0
                    elif calculation_method == 'average':
                        field_score = sum(scores) / len(scores) if scores else 0
            
            elif scoring.field_type == 'rating_field':
                try:
                    rating_value = float(user_response)
                    multiplier = scoring.scoring_data.get('multiplier', 1.0)
                    field_score = rating_value * multiplier
                except (ValueError, TypeError):
                    field_score = 0
            
            total_score += field_score
            
            score_details.append({
                'field_label': scoring.field_label,
                'user_response': user_response,
                'field_score': field_score
            })
        
        return total_score, score_details

    def get_scoring_url(self):
        '''URL para configurar pontuação'''
        return reverse('formulario_scoring', args=[self.pk])

    def get_results_url(self):
        '''URL para ver resultados'''
        return reverse('formulario_results', args=[self.pk])
    
    def extract_scorable_fields(self):
        scorable_fields = []
    
        for step_index, step_block in enumerate(self.form_steps):
            step_number = step_index + 1
            
            for block in step_block.value['fields']:
                field_id = f"{block.block_type}_{block.id}"
                
                # Apenas campos que fazem sentido pontuar
                if block.block_type in ['dropdown_field', 'radio_field', 'checkbox_multiple_field', 'rating_field']:
                    field_data = {
                        'field_id': field_id,
                        'field_label': block.value.get('label', 'Campo sem título'),
                        'field_type': block.block_type,
                        'step_number': step_number,
                        'options': block.value.get('options', []),
                        'block_data': block.value
                    }
                    scorable_fields.append(field_data)
        
            return scorable_fields

    def save_field_scoring(self, field_id, scoring_data):
        field_info = None
        
        for field in self.extract_scorable_fields():
            if field['field_id'] == field_id:
                field_info = field
                break
        
        if not field_info:
            return False
        
        scoring, created = FormFieldScoring.objects.get_or_create(
            formulario_page=self,
            field_id=field_id,
            defaults={
                'field_label': field_info['field_label'],
                'field_type': field_info['field_type'],
                'scoring_data': scoring_data
            }
        )
        
        if not created:
            scoring.scoring_data = scoring_data
            scoring.save()
        
        return True

    def calculate_submission_score(self, submission):
        if not self.enable_scoring:
            return 0, []
        
        total_score = 0
        score_details = []
        form_data = submission.form_data
        
        field_scorings = FormFieldScoring.objects.filter(formulario_page=self)
        
        for scoring in field_scorings:
            field_id = scoring.field_id
            user_response = form_data.get(field_id)
            
            if not user_response:
                continue
            
            field_score = 0
            
            if scoring.field_type in ['dropdown_field', 'radio_field']:
                option_scores = scoring.scoring_data.get('option_scores', {})
                field_score = option_scores.get(user_response, 0)
            
            elif scoring.field_type == 'checkbox_multiple_field':
                if isinstance(user_response, list):
                    option_scores = scoring.scoring_data.get('option_scores', {})
                    calculation_method = scoring.scoring_data.get('calculation_method', 'sum')
                    
                    scores = [option_scores.get(option, 0) for option in user_response]
                    
                    if calculation_method == 'sum':
                        field_score = sum(scores)
                    elif calculation_method == 'max':
                        field_score = max(scores) if scores else 0
                    elif calculation_method == 'average':
                        field_score = sum(scores) / len(scores) if scores else 0
            
            elif scoring.field_type == 'rating_field':
                try:
                    rating_value = float(user_response)
                    multiplier = scoring.scoring_data.get('multiplier', 1.0)
                    field_score = rating_value * multiplier
                except (ValueError, TypeError):
                    field_score = 0
            
            total_score += field_score
            
            score_details.append({
                'field_label': scoring.field_label,
                'user_response': user_response,
                'field_score': field_score
            })
        
        return total_score, score_details
    
    # Substituir o método get_all_steps() na classe FormularioPage

    def get_all_steps(self):
        """PROCESSA CAMPOS SEM ANINHAMENTO INFINITO - VERSÃO CORRIGIDA"""
        steps = []
        
        def extract_fields_safely(fields, depth=0, max_depth=3):
            """
            Extrai campos com limite de profundidade para evitar aninhamento infinito
            """
            if depth > max_depth:
                print(f"⚠️ Limite de profundidade atingido no nível {depth}")
                return []
            
            extracted_fields = []
            
            for field_block in fields:
                # Sempre adicionar o campo principal
                extracted_fields.append(field_block)
                
                # Processar campos aninhados apenas se necessário
                if hasattr(field_block, 'value') and isinstance(field_block.value, dict):
                    
                    # Campos condicionais normais
                    if field_block.block_type == 'conditional_field_condicional':
                        conditional_options = field_block.value.get('conditional_options_con', [])
                        for option in conditional_options:
                            if hasattr(option, 'value') and 'fields_to_show_con' in option.value:
                                nested_fields = option.value['fields_to_show_con']
                                # NÃO adicionar aqui - será processado pelo frontend
                                print(f"Campo condicional encontrado com {len(nested_fields)} campos aninhados")
                    
                    # Campos multi-redirect
                    elif field_block.block_type == 'checkbox_multi_redirect_field':
                        redirect_options = field_block.value.get('redirect_options', [])
                        for option in redirect_options:
                            if hasattr(option, 'value') and 'fields_to_show' in option.value:
                                nested_fields = option.value['fields_to_show']
                                # NÃO adicionar aqui - será processado pelo frontend
                                print(f"Campo multi-redirect encontrado com {len(nested_fields)} campos aninhados")
            
            return extracted_fields
        
        
        # Processar cada step
        for index, step_block in enumerate(self.form_steps):
            order = step_block.value.get('order', str(index + 1))
            try:
                order_num = int(order) if order else index + 1
            except (ValueError, TypeError):
                order_num = index + 1
            
            # Extrair campos de forma segura (sem recursão infinita)
            step_fields = extract_fields_safely(step_block.value['fields'])
            
            step_data = {
                'number': index + 1,
                'original_number': index + 1,
                'order': order_num,
                'logo': step_block.value.get('logo'),
                'logo_alt': step_block.value.get('logo_alt', ''),
                'fields': step_fields,  # Apenas campos do nível principal
                'id': step_block.id,
                'sections': []
            }
            
            
            # Organizar em seções
            current_section = None
            for field_block in step_fields:
                if field_block.block_type == 'section_header':
                    current_section = {
                        'title': field_block.value['title'],
                        'subtitle': field_block.value.get('subtitle', ''),
                        'fields': []
                    }
                    step_data['sections'].append(current_section)
                else:
                    if current_section is None:
                        current_section = {
                            'title': '',
                            'subtitle': '',
                            'fields': []
                        }
                        step_data['sections'].append(current_section)
                    current_section['fields'].append(field_block)
            
            steps.append(step_data)
        
        total_fields = sum(len(step['fields']) for step in steps)
        
        return steps


    # TAMBÉM ADICIONAR este método para extrair dados condicionais de forma mais limpa

    def build_conditional_data(self):
        """Constrói dados condicionais de forma mais organizada"""
        conditional_data = {}
        
        for step_index, step_block in enumerate(self.form_steps):
            for field_block in step_block.value['fields']:
                field_id = f"{field_block.block_type}_{field_block.id}"
                
                # Campos condicionais "condicional"
                if field_block.block_type == 'conditional_field_condicional':
                    options_data = {}
                    
                    for option in field_block.value.get('conditional_options_con', []):
                        option_value = option.value['value_con']
                        action = option.value['action_con']
                        
                        if action == 'show_fields_con':
                            # Extrair IDs dos campos que devem aparecer
                            nested_field_ids = []
                            for nested_field in option.value.get('fields_to_show_con', []):
                                nested_id = f"{nested_field.block_type}_{nested_field.id}"
                                nested_field_ids.append(nested_id)
                            
                            options_data[option_value] = {
                                'action': 'show_fields',
                                'field_ids': nested_field_ids
                            }
                        else:
                            options_data[option_value] = {
                                'action': 'nothing'
                            }
                    
                    conditional_data[field_id] = {
                        'type': 'conditional_field_condicional',
                        'options': options_data
                    }
                
                # Campos multi-redirect
                elif field_block.block_type == 'checkbox_multi_redirect_field':
                    options_data = {}
                    
                    for option in field_block.value.get('redirect_options', []):
                        option_value = option.value['value']
                        action = option.value['action']
                        
                        if action == 'show_fields':
                            nested_field_ids = []
                            for nested_field in option.value.get('fields_to_show', []):
                                nested_id = f"{nested_field.block_type}_{nested_field.id}"
                                nested_field_ids.append(nested_id)
                            
                            options_data[option_value] = {
                                'action': 'show_fields',
                                'field_ids': nested_field_ids
                            }
                        else:
                            options_data[option_value] = {
                                'action': action
                            }
                    
                    conditional_data[field_id] = {
                        'type': 'checkbox_multi_redirect_field',
                        'field_type': field_block.value.get('field_type', 'checkbox'),
                        'options': options_data
                    }
        
        return conditional_data


    # SUBSTITUIR também o método get_context para incluir os dados condicionais corretos

    def get_context(self, request, *args, **kwargs):
        """Adiciona contexto personalizado - VERSÃO CORRIGIDA"""
        context = super().get_context(request, *args, **kwargs)
        
        # Informações básicas dos steps
        context['total_form_steps'] = len(self.form_steps)
        context['all_steps'] = self.get_all_steps()
        
        # Dados condicionais organizados
        conditional_data = self.build_conditional_data()
        context['conditional_data_json'] = json.dumps(conditional_data)
        
        # Extrair nome do usuário
        full_name = 'Usuário'
        if request.method == 'POST':
            for key, value in request.POST.items():
                if key.startswith('nome_completo_field_') and value:
                    full_name = value.strip()
                    break
        
        context['full_name'] = full_name
        
        # Status de sucesso
        if request.GET.get('success'):
            context['form_success'] = True
            context['email_sent'] = request.GET.get('email_sent') == '1'
            context['admin_notified'] = request.GET.get('admin_notified') == '1'
        
        return context
    

    def validate_form_data(self, form_data, request):
        """Valida os dados do formulário - VERSÃO COM PROTEÇÃO DE SEGURANÇA"""
        errors = {}
        
        for step in self.get_all_steps():
            for block in step['fields']:
                if block.block_type in ['info_text', 'divider', 'section_header']:
                    continue
                    
                field_id = f"{block.block_type}_{block.id}"
                value = form_data.get(field_id, '')
                
                # Verificar se campo condicional deve ser validado
                if block.block_type in ['city_field', 'conditional_dropdown_field']:
                    if not self.should_process_conditional_field(block, form_data, request):
                        continue
                
                # NOVA VALIDAÇÃO DE SEGURANÇA - APLICAR A TODOS OS CAMPOS DE TEXTO
                if isinstance(value, str) and value.strip():
                    try:
                        if block.block_type == 'email_field':
                            # Para emails, usar validador específico
                            validate_email_field(value)
                        else:
                            # Para outros campos de texto, usar validador geral
                            validate_safe_characters(value)
                    except ValidationError as e:
                        errors[field_id] = str(e.message)
                        continue
                
                # Verificar campos obrigatórios
                if block.value.get('required', False):
                    if not value or (isinstance(value, list) and not any(value)):
                        errors[field_id] = 'Este campo é obrigatório'
                        continue
                
                # Validações específicas existentes
                if block.block_type == 'email_field' and value:
                    if not self.validate_email(value):
                        errors[field_id] = 'Email inválido'
                
                elif block.block_type == 'cpf_field' and value:
                    if not self.validate_cpf_9_digits(value):
                        errors[field_id] = 'CPF deve ter exatamente 11 dígitos'
                
                elif block.block_type == 'phone_field' and value:
                    if not self.validate_phone(value):
                        errors[field_id] = 'Telefone inválido'
        
        return errors

    class Meta:
        verbose_name = "Formulário Dinâmico"
        verbose_name_plural = "Formulários Dinâmicos"


class FormularioSubmission(models.Model):
    """Modelo para armazenar submissões"""
    page = models.ForeignKey(FormularioPage, on_delete=models.CASCADE)
    form_data = models.JSONField(verbose_name="Dados do formulário")
    files_data = models.JSONField(verbose_name="Metadados dos arquivos", default=dict)
    
    uploaded_files = models.JSONField(
        verbose_name="Caminhos dos arquivos salvos", 
        default=dict,
        help_text="Caminhos onde os arquivos foram salvos no sistema"
    )
    
    submit_time = models.DateTimeField(auto_now_add=True)
    user_ip = models.GenericIPAddressField(verbose_name="IP do usuário", null=True, blank=True)
    user_agent = models.TextField(verbose_name="User Agent", blank=True)
        
    class Meta:
        verbose_name = "Submissão do Formulário"
        verbose_name_plural = "Submissões do Formulário"
        ordering = ['-submit_time']

    def __str__(self):
        return f"Submissão - {self.submit_time.strftime('%d/%m/%Y %H:%M')}"

    def get_readable_data(self):
        """Retorna dados em formato legível"""
        readable = {}
        for key, value in self.form_data.items():
            if isinstance(value, list):
                readable[key] = ', '.join(value)
            else:
                readable[key] = value
        return readable





class FeatureBlock(StructBlock):
    """Bloco para funcionalidades"""
    icon = CharBlock(
        label="Ícone FontAwesome",
        max_length=50,
        help_text="Ex: fas fa-layer-group, fas fa-code-branch, etc."
    )
    title = CharBlock(
        label="Título da Funcionalidade",
        max_length=100
    )
    description = RichTextBlock(
        label="Descrição",
        help_text="Descreva a funcionalidade"
    )
    
    class Meta:
        icon = "pick"
        label = "⚡ Funcionalidade"


class StatBlock(StructBlock):
    """Bloco para estatísticas"""
    number = CharBlock(
        label="Número/Estatística",
        max_length=20,
        help_text="Ex: 15k+, 100%, 12, 5s",
        required=False
    )
    description = CharBlock(
        label="Descrição",
        max_length=100,
        help_text="Ex: Inscrições Processadas",
        required=False
    )
    highlight = blocks.BooleanBlock(
        label="Destacar com animação",
        required=False,
        default=False
    )
    
    class Meta:
        icon = "order"
        label = "📊 Estatística"


class CTAButtonBlock(StructBlock):
    """Bloco para botões de Call-to-Action"""
    text = CharBlock(
        label="Texto do Botão",
        max_length=50
    )
    icon = CharBlock(
        label="Ícone FontAwesome",
        max_length=50,
        help_text="Ex: fas fa-sign-in-alt, fas fa-book"
    )
    url = URLBlock(
        label="URL",
        required=False,
        help_text="Deixe vazio para JavaScript personalizado"
    )
    style = blocks.ChoiceBlock(
        label="Estilo do Botão",
        choices=[
            ('primary', 'Primário (preenchido)'),
            ('secondary', 'Secundário (contorno)'),
        ],
        default='primary'
    )
    
    class Meta:
        icon = "link"
        label = "🔗 Botão CTA"


class HomePage(Page):
    """Página inicial do sistema de formulários"""

    template = "enap_designsystem/form_templates/home_page.html"
    
    # Seção Hero
    hero_title = models.CharField(
        verbose_name="Título Principal",
        max_length=200,
        default="Sistema de Formulários Inteligentes"
    )
    
    hero_subtitle = RichTextField(
        verbose_name="Descrição do Hero",
        default="Desenvolvemos uma plataforma avançada para criação de formulários dinâmicos e experiências de inscrição profissionais.",
        help_text="Texto que aparece abaixo do título principal"
    )
    
    hero_buttons = StreamField(
        [('cta_button', CTAButtonBlock())],
        verbose_name="Botões do Hero",
        use_json_field=True,
        min_num=1,
        max_num=300,
        help_text="Botões principais da seção hero"
    )
    
    # Preview do formulário
    form_preview_title = models.CharField(
        verbose_name="Título do Preview",
        max_length=100,
        default="Etapa 2 de 4",
        blank=True
    )
    
    # Seção Features
    features_title = models.CharField(
        verbose_name="Título das Funcionalidades",
        max_length=200,
        default="Funcionalidades desenvolvidas internamente"
    )
    
    features_subtitle = RichTextField(
        verbose_name="Subtítulo das Funcionalidades",
        default="Nossa equipe criou uma solução robusta que atende perfeitamente às demandas da instituição",
        blank=True
    )
    
    features = StreamField(
        [('feature', FeatureBlock())],
        verbose_name="Lista de Funcionalidades",
        use_json_field=True,
        min_num=1,
        max_num=120,
        help_text="Adicione as funcionalidades do sistema"
    )
    
    
    # Seção CTA Final
    cta_title = models.CharField(
        verbose_name="Título do CTA Final",
        max_length=200,
        default="Sistema pronto para uso na instituição"
    )
    
    cta_subtitle = RichTextField(
        verbose_name="Descrição do CTA Final",
        default="Nossa solução interna está disponível para todos os departamentos que precisam criar formulários profissionais e eficientes.",
        blank=True
    )
    
    cta_buttons = StreamField(
        [('cta_button', CTAButtonBlock())],
        verbose_name="Botões do CTA Final",
        use_json_field=True,
        min_num=1,
        max_num=300,
        help_text="Botões da seção final"
    )
    
    # Configurações visuais
    primary_color = models.CharField(
        verbose_name="Cor Primária",
        max_length=7,
        default="#024248",
        help_text="Cor principal em hexadecimal (ex: #024248)"
    )
    
    secondary_color = models.CharField(
        verbose_name="Cor Secundária",
        max_length=7,
        default="#026873",
        help_text="Cor secundária em hexadecimal (ex: #026873)"
    )
    
    logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name='Logo da Instituição'
    )
    
    background_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name='Imagem de Fundo (opcional)'
    )
    
    # Configurações do menu
    show_in_menus_default = True
    
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('hero_title'),
            FieldPanel('hero_subtitle'),
            FieldPanel('hero_buttons'),
        ], "🎬 Seção Hero"),
        
        MultiFieldPanel([
            FieldPanel('form_preview_title'),
        ], "📱 Preview do Formulário"),
        
        MultiFieldPanel([
            FieldPanel('features_title'),
            FieldPanel('features_subtitle'),
            FieldPanel('features'),
        ], "⚡ Funcionalidades"),
        
        MultiFieldPanel([
            FieldPanel('cta_title'),
            FieldPanel('cta_subtitle'),
            FieldPanel('cta_buttons'),
        ], "🚀 CTA Final"),
    ]
    
    settings_panels = Page.settings_panels + [
        MultiFieldPanel([
            FieldPanel('primary_color'),
            FieldPanel('secondary_color'),
            FieldPanel('logo'),
            FieldPanel('background_image'),
        ], "🎨 Aparência"),
    ]
    
    class Meta:
        verbose_name = "Página Formulario Inicial"
        verbose_name_plural = "Páginas Formulario Inicial"
    
    def get_context(self, request):
        """Adiciona contexto personalizado"""
        context = super().get_context(request)
        
        # Adicionar cores CSS
        context['primary_color'] = self.primary_color
        context['secondary_color'] = self.secondary_color
        
        return context
    





class FeatureBlock(StructBlock):
    """Bloco para funcionalidades"""
    icon = CharBlock(
        label="Ícone FontAwesome",
        max_length=50,
        help_text="Ex: fas fa-layer-group, fas fa-code-branch, etc."
    )
    title = CharBlock(
        label="Título da Funcionalidade",
        max_length=100
    )
    description = RichTextBlock(
        label="Descrição",
        help_text="Descreva a funcionalidade"
    )
    
    class Meta:
        icon = "pick"
        label = "⚡ Funcionalidade"


class StatBlock(StructBlock):
    """Bloco para estatísticas"""
    number = CharBlock(
        label="Número/Estatística",
        max_length=20,
        help_text="Ex: 15k+, 100%, 12, 5s",
        required=False
    )
    description = CharBlock(
        label="Descrição",
        max_length=100,
        help_text="Ex: Inscrições Processadas",
        required=False
    )
    highlight = blocks.BooleanBlock(
        label="Destacar com animação",
        required=False,
        default=False
    )
    
    class Meta:
        icon = "order"
        label = "📊 Estatística"


class CTAButtonBlock(StructBlock):
    """Bloco para botões de Call-to-Action"""
    text = CharBlock(
        label="Texto do Botão",
        max_length=50,
        required=False,
    )
    icon = CharBlock(
        label="Ícone FontAwesome",
        max_length=50,
        help_text="Ex: fas fa-sign-in-alt, fas fa-book",
        required=False,
    )
    url = URLBlock(
        label="URL",
        required=False,
        help_text="Deixe vazio para JavaScript personalizado"
    )
    style = blocks.ChoiceBlock(
        label="Estilo do Botão",
        choices=[
            ('primary', 'Primário (preenchido)'),
            ('secondary', 'Secundário (contorno)'),
        ],
        default='primary'
    )
    
    class Meta:
        icon = "link"
        label = "🔗 Botão CTA"




