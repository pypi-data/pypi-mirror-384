# ===============================================
# wagtail_hooks.py - VERSÃO FINAL CORRIGIDA
# ===============================================

from wagtail import hooks
from django.utils.html import format_html
from django.templatetags.static import static
from enap_designsystem.blocks import ENAPNoticia
from django.urls import reverse, path
from django.shortcuts import render, get_object_or_404
from django.db.models import Count
import csv
from django.http import HttpResponse, Http404, FileResponse
from wagtail.admin.menu import MenuItem
from .blocks.form import FormularioSubmission, FormularioPage
from django.conf import settings
import os
from wagtail import hooks
from django.contrib.contenttypes.models import ContentType




@hooks.register('insert_global_admin_js')
def global_admin_js():
    return format_html(
        '<script src="{}"></script><script src="{}"></script>',
        static('js/main_layout.js'),
        static('js/mid_layout.js')
    )

@hooks.register("before_create_page")
def set_default_author_on_create(request, parent_page, page_class):
    if page_class == ENAPNoticia:
        def set_author(instance):
            instance.author = request.user
        return set_author

@hooks.register('insert_global_admin_js')
def add_export_button():
    return format_html(
        """
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            if (window.location.href.includes('/admin/snippets/enap_designsystem/respostaformulario/')) {{
                const header = document.querySelector('.content-wrapper h1, .content-wrapper h2');
                if (header) {{
                    const exportBtn = document.createElement('a');
                    exportBtn.href = '/admin/exportar-respostas/';
                    exportBtn.className = 'button button-small button-secondary';
                    exportBtn.style.marginLeft = '10px';
                    exportBtn.innerHTML = '📊 Exportar CSV';
                    exportBtn.target = '_blank';
                    header.appendChild(exportBtn);
                }}
            }}
        }});
        </script>
        """
    )

# ===============================================
# VIEWS DE DOWNLOAD DE ARQUIVOS - CORRIGIDAS
# ===============================================
def download_form_file(request, page_id, submission_id, field_name):
    """Download de arquivo do FormularioSubmission tradicional - CORRIGIDA"""
    try:
        print(f"🚀 INICIANDO DOWNLOAD:")
        print(f"   submission_id: {submission_id}")
        print(f"   field_name: {field_name}")
        print(f"   page_id: {page_id}")
        
        submission = get_object_or_404(FormularioSubmission, id=submission_id)
        print(f"✅ Submissão encontrada: {submission.id}")
        print(f"📄 Form data: {submission.form_data}")
        
        if not (request.user.is_staff or request.user.is_superuser):
            print("❌ ERRO: Usuário sem permissão")
            raise Http404("Sem permissão")
        
        print("🔍 Chamando find_file_path_traditional...")
        file_path = find_file_path_traditional(submission, field_name, page_id)
        print(f"📂 Resultado: {file_path}")
        
        if not file_path:
            print("❌ ERRO: Arquivo não encontrado")
            
            folder_path = os.path.join(settings.MEDIA_ROOT, 'form_submissions', str(submission_id))
            print(f"🔍 Verificando pasta: {folder_path}")
            
            if os.path.exists(folder_path):
                files = os.listdir(folder_path)
                print(f"📁 Arquivos encontrados: {files}")
            else:
                print(f"❌ Pasta não existe")
                # Verificar outras pastas
                form_submissions_root = os.path.join(settings.MEDIA_ROOT, 'form_submissions')
                if os.path.exists(form_submissions_root):
                    all_folders = [f for f in os.listdir(form_submissions_root) if os.path.isdir(os.path.join(form_submissions_root, f))]
                    print(f"📁 Pastas disponíveis: {all_folders}")
            
            raise Http404("Arquivo não encontrado")
        
        # Nome original do arquivo
        form_data = submission.form_data or {}
        field_data = form_data.get(field_name, {})
        original_filename = field_data.get('filename', os.path.basename(file_path)) if isinstance(field_data, dict) else os.path.basename(file_path)
        
        print(f"📎 Nome original: {original_filename}")
        print(f"🎯 Retornando arquivo: {file_path}")
        
        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=original_filename
        )
        
    except Exception as e:
        print(f"💥 ERRO COMPLETO: {e}")
        import traceback
        print(f"🔥 TRACEBACK: {traceback.format_exc()}")
        raise Http404(f"Erro ao baixar arquivo: {e}")


def verificar_arquivos_tradicionais():
    """Função para verificar onde estão os arquivos dos formulários tradicionais"""
    from django.db.models import Q
    
    print("🔍 VERIFICANDO ARQUIVOS DE FORMULÁRIOS TRADICIONAIS")
    print("="*60)
    
    # Buscar submissões que têm arquivos
    submissions_with_files = FormularioSubmission.objects.filter(
        form_data__isnull=False
    ).exclude(form_data={})
    
    print(f"📊 Total de submissões: {submissions_with_files.count()}")
    
    arquivos_encontrados = 0
    arquivos_perdidos = 0
    
    for submission in submissions_with_files:
        print(f"\n📄 Submissão ID: {submission.id} - Página: {submission.page.title}")
        
        for field_name, field_data in submission.form_data.items():
            if 'file_upload_field' in field_name:
                print(f"   📎 Campo de arquivo: {field_name}")
                print(f"   📊 Dados: {field_data}")
                
                # Tentar encontrar arquivo
                file_path = find_file_path_traditional(submission, field_name)
                if file_path:
                    print(f"   ✅ Arquivo encontrado: {file_path}")
                    arquivos_encontrados += 1
                else:
                    print(f"   ❌ Arquivo PERDIDO")
                    arquivos_perdidos += 1
    
    print(f"\n📈 RESUMO:")
    print(f"   ✅ Arquivos encontrados: {arquivos_encontrados}")
    print(f"   ❌ Arquivos perdidos: {arquivos_perdidos}")
    
    return {
        'encontrados': arquivos_encontrados,
        'perdidos': arquivos_perdidos
    }





def migrar_arquivos_para_documentos():
    """Migra arquivos existentes para a pasta documentos/"""
    import shutil
    from django.core.files.storage import default_storage
    
    print("🚚 MIGRANDO ARQUIVOS PARA /documentos/")
    print("="*40)
    
    migrados = 0
    erros = 0
    
    # Verificar se pasta documentos existe
    documentos_path = os.path.join(settings.MEDIA_ROOT, 'documentos')
    if not os.path.exists(documentos_path):
        os.makedirs(documentos_path)
        print(f"📁 Criada pasta: {documentos_path}")
    
    submissions_with_files = FormularioSubmission.objects.filter(
        form_data__isnull=False
    ).exclude(form_data={})
    
    for submission in submissions_with_files:
        for field_name, field_data in submission.form_data.items():
            if 'file_upload_field' in field_name and isinstance(field_data, dict):
                filename = field_data.get('filename')
                if filename:
                    # Procurar arquivo no local atual
                    current_path = find_file_path_traditional(submission, field_name)
                    if current_path and 'documentos' not in current_path:
                        try:
                            # Destino em documentos/
                            new_path = os.path.join(documentos_path, filename)
                            
                            # Se já existe, adicionar timestamp
                            if os.path.exists(new_path):
                                from datetime import datetime
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                name, ext = os.path.splitext(filename)
                                new_filename = f"{name}_{timestamp}{ext}"
                                new_path = os.path.join(documentos_path, new_filename)
                            
                            # Copiar arquivo
                            shutil.copy2(current_path, new_path)
                            print(f"✅ Migrado: {filename}")
                            migrados += 1
                            
                        except Exception as e:
                            print(f"❌ Erro ao migrar {filename}: {e}")
                            erros += 1
    
    print(f"\n📈 MIGRAÇÃO CONCLUÍDA:")
    print(f"   ✅ Arquivos migrados: {migrados}")
    print(f"   ❌ Erros: {erros}")










def download_dynamic_file(request, submission_id, field_name):
    """Download de arquivo do FormularioDinamicoSubmission - CORRIGIDO"""
    try:
        from .models import FormularioDinamicoSubmission
        submission = get_object_or_404(FormularioDinamicoSubmission, id=submission_id)
        
        # Verificar permissão
        if not (request.user.is_staff or request.user.is_superuser):
            raise Http404("Sem permissão")
        
        # ✅ PROCURAR ARQUIVO USANDO A LÓGICA CORRETA
        file_path = find_file_path_dynamic(submission, field_name)
        if not file_path:
            raise Http404("Arquivo não encontrado")
        
        # Pegar nome original do arquivo
        form_data = submission.form_data or {}
        field_data = form_data.get(field_name, {})
        
        if isinstance(field_data, dict) and 'filename' in field_data:
            original_filename = field_data['filename']
        else:
            # Tentar pegar do files_data
            files_data = getattr(submission, 'files_data', {})
            file_metadata = files_data.get(field_name, {})
            original_filename = file_metadata.get('original_name', os.path.basename(file_path))
        
        print(f"📥 Download dinâmico iniciado: {original_filename} de {file_path}")
        
        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=original_filename
        )
        
    except ImportError:
        print("❌ FormularioDinamicoSubmission não encontrado")
        raise Http404("Modelo não encontrado")
    except Exception as e:
        print(f"❌ Erro no download dinâmico: {e}")
        raise Http404("Erro ao baixar arquivo")
    


# ===============================================
# CORREÇÃO PARA DOWNLOAD DE ARQUIVOS - FormularioPage
# ===============================================
def find_file_path_traditional(submission, field_name, page_id):
    """Encontra caminho do arquivo baseado no conteúdo do form_data"""
    import mimetypes

    print(f"🔍 Procurando arquivo: page_id={page_id}, submission_id={submission.id}, field={field_name}")
    
    form_data = submission.form_data or {}

    if field_name in form_data:
        field_data = form_data[field_name]

        print(f"📄 Field data: {field_data}")

        if isinstance(field_data, dict):
            original_filename = field_data.get('filename')
            expected_size = field_data.get('size')
            print("Tamanho esperado do arquivo: ", expected_size)
            # content_type = field_data.get('content_type')

            if not original_filename:
                return None

            file_extension = os.path.splitext(original_filename)[1]  # ex: ".png"
            
            form_submissions_root = os.path.join(settings.MEDIA_ROOT, 'form_submissions', str(page_id), str(submission.id))
            
            print(f"🔍 Buscando arquivos com extensão {file_extension}...")

            # Busca recursiva em toda a pasta form_submissions
            for root, dirs, files in os.walk(form_submissions_root):
                for file in files:
                    if file.lower().endswith(file_extension.lower()):
                        file_path = os.path.join(root, file)
                        
                        try:
                            file_size = os.path.getsize(file_path)
                            print("Tamanho do arquivo encontrado: ", file_size)

                            # Comparar tamanho e extensão
                            if expected_size and file_size == expected_size:
                                print(f"✅ Arquivo compatível encontrado: {file_path}")
                                return file_path
                        except Exception as e:
                            print(f"⚠️ Erro ao verificar arquivo: {file_path}, erro: {e}")
                            continue
            
            print("❌ Nenhum arquivo compatível encontrado.")

    print(f"❌ Arquivo não encontrado para field: {field_name}")
    return None


def find_file_path_dynamic(submission, field_name):
    """Encontra caminho do arquivo para FormularioDinamicoSubmission
    ALTERADA PARA PROCURAR EM /documentos/"""
    
    # Determinar page_id baseado no tipo de submissão
    if hasattr(submission, 'page'):
        page_id = submission.page.id
    else:
        page_id = submission.object_id
    
    # Obter filename
    form_data = submission.form_data or {}
    field_data = form_data.get(field_name, {})
    
    filename = None
    if isinstance(field_data, dict):
        filename = field_data.get('filename')
    elif isinstance(field_data, str):
        filename = field_data
    
    if not filename:
        return None
    
    # Caminhos para buscar (nova estrutura primeiro)
    possible_paths = [
        # 1. Nova estrutura vinculada
        os.path.join(settings.MEDIA_ROOT, 'formularios', f'page_{page_id}', f'submission_{submission.id}', filename),
        
        # 2. Fallback para estruturas antigas
        os.path.join(settings.MEDIA_ROOT, 'documentos', filename),
        os.path.join(settings.MEDIA_ROOT, 'form_submissions', str(submission.id), filename),
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.path.isfile(path):
            return path
    
    return None

# ===============================================
# FUNÇÃO PARA FORMATAR VALORES COM LINKS
# ===============================================

def format_field_value_for_csv(field_name, value, page_id, submission=None, request=None):
    """Formata valores para CSV com links de download quando possível"""
    
    if isinstance(value, list):
        return ', '.join(str(v) for v in value if v)
    
    elif isinstance(value, dict) and 'filename' in value:
        filename = value.get('filename', '')
        size = value.get('size', 0)
        
        # Tentar criar link de download
        download_url = None
        if submission and request:
            try:
                # Determinar o tipo de submissão
                if hasattr(submission, 'page'):
                    # FormularioSubmission (tradicional)
                    download_url = request.build_absolute_uri(
                        reverse('download_form_file', kwargs={
                            'submission_id': submission.id,
                            'field_name': field_name,
                            'page_id': page_id
                        })
                    )
                else:
                    # FormularioDinamicoSubmission
                    download_url = request.build_absolute_uri(
                        reverse('download_dynamic_file', kwargs={
                            'submission_id': submission.id,
                            'field_name': field_name,
                            'page_id': page_id
                        })
                    )
            except Exception as e:
                print(f"⚠️ Erro ao criar URL de download: {e}")
        
        # Formatar resposta
        if size:
            size_mb = round(size / (1024 * 1024), 2)
            size_info = f" ({size_mb} MB)"
        else:
            size_info = ""
        
        if download_url:
            return f"{filename}{size_info} - DOWNLOAD: {download_url}"
        else:
            return f"ARQUIVO: {filename}{size_info}"
    
    else:
        return str(value) if value else ''

# ===============================================
# VIEWS DE EXPORTAÇÃO CSV
# ===============================================

def csv_export_view_atualizada(request):
    """Página unificada para escolher qual formulário exportar"""
    from django.shortcuts import render
    from django.db.models import Count
    
    formularios_data = []
    
    print("🔍 Carregando formulários para exportação...")
    
    # Formulários tradicionais (FormularioPage)
    try:
        formularios_existentes = FormularioPage.objects.live()
        for form in formularios_existentes:
            count = FormularioSubmission.objects.filter(page=form).count()
            formularios_data.append({
                'tipo': 'FormularioPage',
                'form': form,
                'count': count,
                'last_submission': FormularioSubmission.objects.filter(page=form).first(),
                'download_url': f'/admin/export-csv/{form.id}/'
            })
            print(f"   📄 FormularioPage: {form.title} ({count} respostas)")
    except Exception as e:
        print(f"⚠️ Erro ao carregar FormularioPage: {e}")
    
    # Formulários dinâmicos
    try:
        from .models import FormularioDinamicoSubmission
        
        dinamicos_stats = FormularioDinamicoSubmission.objects.values(
            'object_id', 'page_title'
        ).annotate(count=Count('id')).order_by('-count')
        
        print(f"📊 Encontrados {len(dinamicos_stats)} formulários dinâmicos")
        
        for stat in dinamicos_stats:
            ultima_submissao = FormularioDinamicoSubmission.objects.filter(
                object_id=stat['object_id']
            ).first()
            
            formularios_data.append({
                'tipo': 'FormularioDinamico',
                'form': {
                    'id': stat['object_id'],
                    'title': f"📝 {stat['page_title']} (Dinâmico)",
                    'slug': f"dinamico-{stat['object_id']}"
                },
                'count': stat['count'],
                'last_submission': ultima_submissao,
                'download_url': f'/admin/export-dinamico-csv/{stat["object_id"]}/'
            })
            print(f"   📝 FormularioDinâmico: {stat['page_title']} ({stat['count']} respostas)")
            
    except ImportError:
        print("FormularioDinamicoSubmission não encontrado")
    except Exception as e:
        print(f"Erro com FormularioDinamico: {e}")
    
    if not formularios_data:
        formularios_data.append({
            'tipo': 'Info',
            'form': {
                'id': 0,
                'title': 'ℹ️ Nenhuma submissão encontrada.',
                'slug': 'info'
            },
            'count': 0,
            'last_submission': None,
            'download_url': '#'
        })
    
    print(f"📋 Total de formulários: {len(formularios_data)}")
    
    return render(request, 'admin/csv_export.html', {
        'formularios': formularios_data,
    })

def download_csv(request, page_id):
    """Download CSV para FormularioPage com links de arquivo"""
    page = get_object_or_404(FormularioPage, id=page_id)
    submissions = FormularioSubmission.objects.filter(page=page).order_by('-submit_time')
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="submissoes_{page.slug}_{page.id}.csv"'
    response.write('\ufeff')
    
    writer = csv.writer(response)
    
    if not submissions.exists():
        writer.writerow(['Nenhuma submissão encontrada'])
        return response
    
    print(f"🚀 Gerando CSV para FormularioPage: {page.title} ({submissions.count()} submissões)")
    
    # Coletar campos únicos
    all_fields = set()
    for submission in submissions:
        if submission.form_data:
            all_fields.update(submission.form_data.keys())
    
    # Usar funções de limpeza se disponíveis
    try:
        from .views import clean_field_name, organize_csv_fields
        ordered_fields = organize_csv_fields(list(all_fields))
        headers = ['Data/Hora', 'IP do Usuário']
        headers.extend([clean_field_name(field) for field in ordered_fields])
    except ImportError:
        ordered_fields = sorted(list(all_fields))
        headers = ['Data/Hora', 'IP do Usuário'] + ordered_fields
    
    writer.writerow(headers)
    
    # Dados com links de arquivos
    for submission in submissions:
        row = [
            submission.submit_time.strftime('%d/%m/%Y %H:%M:%S'),
            submission.user_ip or 'N/A',
        ]
        
        for field in ordered_fields:
            value = submission.form_data.get(field, '') if submission.form_data else ''
            formatted_value = format_field_value_for_csv(field, value, submission, request)
            row.append(formatted_value)
        
        writer.writerow(row)
    
    print(f"✅ CSV tradicional gerado com {submissions.count()} linhas")
    return response

def download_csv_dinamico(request, page_id):
    """Download CSV para formulários dinâmicos com links de arquivo"""
    try:
        from .models import FormularioDinamicoSubmission
        
        submissoes = FormularioDinamicoSubmission.objects.filter(
            object_id=page_id
        ).order_by('-submit_time')
        
        if not submissoes.exists():
            return HttpResponse('Nenhuma submissão encontrada', status=404)
        
        first_submission = submissoes.first()
        page_title = first_submission.page_title or f'Página {page_id}'
        
        print(f"🚀 Gerando CSV dinâmico para: {page_title} ({submissoes.count()} submissões)")
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="dinamico_{page_title}_{page_id}.csv"'
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        # Coletar campos únicos
        all_fields = set()
        for submissao in submissoes:
            if submissao.form_data:
                all_fields.update(submissao.form_data.keys())
        
        # Organizar campos
        try:
            from .views import clean_field_name, organize_csv_fields
            ordered_fields = organize_csv_fields(list(all_fields))
            headers = ['Data/Hora', 'Nome', 'Email', 'Telefone', 'IP']
            headers.extend([clean_field_name(field) for field in ordered_fields])
        except ImportError:
            ordered_fields = sorted(list(all_fields))
            headers = ['Data/Hora', 'Nome', 'Email', 'Telefone', 'IP'] + ordered_fields
        
        writer.writerow(headers)
        
        # Dados com links de arquivos
        for submissao in submissoes:
            row = [
                submissao.submit_time.strftime('%d/%m/%Y %H:%M:%S'),
                submissao.user_name or '',
                submissao.user_email or '',
                submissao.user_phone or '',
                submissao.user_ip or '',
            ]
            
            for field in ordered_fields:
                value = submissao.form_data.get(field, '') if submissao.form_data else ''
                formatted_value = format_field_value_for_csv(field, value, submissao, request)
                row.append(formatted_value)
            
            writer.writerow(row)
        
        print(f"✅ CSV dinâmico gerado com {submissoes.count()} linhas")
        return response
        
    except ImportError:
        return HttpResponse('FormularioDinamicoSubmission não encontrado', status=404)
    except Exception as e:
        print(f"❌ Erro no CSV dinâmico: {e}")
        return HttpResponse(f'Erro: {str(e)}', status=500)

# ===============================================
# VIEWS ORIGINAIS (COMPATIBILIDADE)
# ===============================================

def csv_export_view(request):
    """Função original para FormularioPage - manter compatibilidade"""
    formularios = FormularioPage.objects.live()
    if not request.user.is_superuser:
        formularios = formularios.filter(owner=request.user)
    
    formularios_data = []
    for form in formularios:
        count = FormularioSubmission.objects.filter(page=form).count()
        formularios_data.append({
            'form': form,
            'count': count,
            'last_submission': FormularioSubmission.objects.filter(page=form).first()
        })
    
    return render(request, 'admin/csv_export.html', {
        'formularios': formularios_data,
    })

# ===============================================
# MENUS
# ===============================================

@hooks.register('register_admin_menu_item')
def register_export_menu_item():
    return MenuItem(
        '📊 Exportar Respostas', 
        reverse('csv_export_updated'),
        icon_name='download',
        order=1000
    )

@hooks.register('register_admin_menu_item')
def register_meta_tags_menu():
    return MenuItem(
        '🏷️ Meta Tags', 
        reverse('meta_tags_manager'),
        classname='icon icon-cog', 
        order=800
    )

# ===============================================
# URLS CONSOLIDADAS
# ===============================================

@hooks.register('register_admin_urls')
def register_admin_urls():
    """Registra TODAS as URLs do admin"""
    from .views import meta_tags_manager, preview_meta_changes, apply_meta_tags
    
    return [
        # Meta tags
        path('meta-tags/', meta_tags_manager, name='meta_tags_manager'),
        path('meta-tags/preview/', preview_meta_changes, name='meta_tags_preview'),
        path('meta-tags/apply/', apply_meta_tags, name='meta_tags_apply'),
        
        # Exportação unificada
        path('exportar-respostas/', csv_export_view_atualizada, name='csv_export_updated'),
        
        # Downloads CSV
        path('export-csv/<int:page_id>/', download_csv_with_enap_labels_v4, name='download_csv'),
        path('export-dinamico-csv/<int:page_id>/', download_csv_dinamico_with_enap_labels_v4, name='download_csv_dinamico'),
        
        # URLs para download de arquivos individuais
        path('download-file/<int:page_id>/<int:submission_id>/<str:field_name>/', download_form_file, name='download_form_file'),
        path('download-dynamic-file/<int:submission_id>/<str:field_name>/', download_dynamic_file, name='download_dynamic_file'),
        
        # Compatibilidade
        path('export-csv/', csv_export_view, name='wagtail_csv_export'),
    ]






def salvar_arquivo_estrategia_personalizada(uploaded_file, field_name, page_id, estrategia='simples'):
    """Salva arquivo usando estratégia específica"""
    from django.core.files.storage import default_storage
    from datetime import datetime
    import uuid
    
    estrategias = {
        'simples': f'documentos/{uploaded_file.name}',
        'timestamp': f'documentos/{datetime.now().strftime("%Y%m%d_%H%M%S")}_{uploaded_file.name}',
        'uuid': f'documentos/{str(uuid.uuid4())[:8]}_{uploaded_file.name}',
        'por_data': f'documentos/{datetime.now().strftime("%Y/%m")}/{uploaded_file.name}',
        'por_tipo': f'documentos/{uploaded_file.name.split(".")[-1].lower()}/{uploaded_file.name}',
        'por_pagina': f'documentos/page_{page_id}/{uploaded_file.name}'
    }
    
    file_path = estrategias.get(estrategia, estrategias['simples'])
    saved_path = default_storage.save(file_path, uploaded_file)
    
    print(f"📎 Arquivo salvo usando estratégia '{estrategia}': {saved_path}")
    return saved_path



def get_file_save_path_options(uploaded_file, field_name, page_id=None):
    """Diferentes opções de como organizar os arquivos em /documentos/"""
    
    from datetime import datetime
    import uuid
    
    # Opção 1: Direto em documentos/
    option1 = f'documentos/{uploaded_file.name}'
    
    
    return {
        'simples': option1,
    }


# ===============================================
# SOLUÇÃO FINAL - LABELS DOS FORMULÁRIOS ENAP
# ===============================================


def extract_labels_from_enap_form_steps_v4(page):
    """
    Extrai labels criando mapeamento EXATO por UUID completo
    VERSÃO 4 - DEFINITIVA - Mapeia cada UUID para seu label específico
    """
    uuid_to_label = {}  # Mapeamento direto UUID → Label
    field_order = []
    
    try:
        print(f"🔍 Extraindo labels ENAP v4 para: {page.title}")
        
        if not hasattr(page, 'form_steps') or not page.form_steps:
            print("   ❌ Página não tem form_steps")
            return uuid_to_label, field_order
        
        field_counter = 0
        
        # Iterar pelos steps
        for step_index, step in enumerate(page.form_steps):
            print(f"   📋 Processando step {step_index}: {step.block_type}")
            
            if step.block_type == 'form_step' and 'fields' in step.value:
                fields = step.value['fields']
                print(f"   📊 Encontrados {len(fields)} campos no step")
                
                # Iterar pelos campos na ordem EXATA
                for field_index, field in enumerate(fields):
                    try:
                        field_type = field.block_type
                        field_value = field.value
                        field_uuid = str(field.id)  # UUID do campo
                        
                        # Extrair label
                        label = field_value.get('label', '')
                        
                        if label:
                            # Mapeamento EXATO: UUID completo → Label
                            uuid_to_label[field_uuid] = label
                            
                            # Info do campo para ordenação
                            field_info = {
                                'position': field_counter,
                                'type': field_type,
                                'label': label,
                                'uuid': field_uuid,
                                'step': step_index,
                                'field_index': field_index
                            }
                            field_order.append(field_info)
                            
                            print(f"   ✅ {field_type}: '{label}'")
                            
                            # Debug info detalhada
                            for attr in ['placeholder', 'help_text', 'required']:
                                value = field_value.get(attr)
                                if value:
                                    icon = {'placeholder': '📝', 'help_text': '💡', 'required': '⚠️'}[attr]
                                    print(f"      {icon} {attr.title()}: {value}")
                            
                            field_counter += 1
                        
                    except Exception as e:
                        print(f"   ⚠️ Erro ao processar campo {field_index}: {e}")
        
        print(f"📋 Total de labels extraídos: {len(uuid_to_label)}")
        return uuid_to_label, field_order
        
    except Exception as e:
        print(f"❌ Erro ao extrair labels v4: {e}")
        import traceback
        print(f"🔥 Traceback: {traceback.format_exc()}")
        return uuid_to_label, field_order


def map_submission_fields_to_labels_v4(submission_fields, uuid_to_label, field_order):
    """
    Mapeia campos das submissões para labels usando UUID EXATO
    VERSÃO 4 - DEFINITIVA - Cada campo vai para SEU label correto
    """
    field_mapping = {}
    
    print(f"🔄 Mapeando campos das submissões para labels:")
    
    # Para cada campo da submissão, encontrar seu label EXATO
    for field_name in sorted(submission_fields):
        label_found = None
        mapping_strategy = "unknown"
        
        # Extrair UUID do nome do campo
        # Formato: tipo_field_uuid-completo
        parts = field_name.split('_')
        if len(parts) >= 3:
            # UUID está nas últimas partes (formato: xxxx-xxxx-xxxx-xxxx-xxxx)
            potential_uuid_parts = []
            for i in range(len(parts) - 1, -1, -1):
                if '-' in parts[i]:  # Parte do UUID
                    potential_uuid_parts.insert(0, parts[i])
                elif len(potential_uuid_parts) > 0:
                    break
            
            if potential_uuid_parts:
                potential_uuid = '_'.join(potential_uuid_parts)
                
                # Verificar se este UUID existe no mapeamento
                if potential_uuid in uuid_to_label:
                    label_found = uuid_to_label[potential_uuid]
                    mapping_strategy = "uuid_exact"
                else:
                    # Tentar sem underscores (formato: xxxx-xxxx-xxxx-xxxx-xxxx direto)
                    potential_uuid_clean = potential_uuid_parts[-1] if potential_uuid_parts else None
                    if potential_uuid_clean and potential_uuid_clean in uuid_to_label:
                        label_found = uuid_to_label[potential_uuid_clean]
                        mapping_strategy = "uuid_clean"
        
        # Se não encontrou por UUID, usar busca por fragmento
        if not label_found:
            for uuid, label in uuid_to_label.items():
                # Verificar se alguma parte do UUID está no field_name
                uuid_parts = uuid.split('-')
                for part in uuid_parts:
                    if len(part) >= 6 and part in field_name:  # Fragmento de pelo menos 6 chars
                        label_found = label
                        mapping_strategy = "uuid_fragment"
                        break
                if label_found:
                    break
        
        # Fallback: usar posição na ordem (se ainda há campos disponíveis)
        if not label_found:
            field_index = len(field_mapping)  # Posição atual
            if field_index < len(field_order):
                label_found = field_order[field_index]['label']
                mapping_strategy = "position_fallback"
            else:
                # Último recurso: nome limpo
                label_found = clean_field_name_simple(field_name)
                mapping_strategy = "name_clean"
        
        field_mapping[field_name] = label_found
        print(f"   ✅ {field_name} → '{label_found}' ({mapping_strategy})")
    
    print(f"📋 Mapeamento das submissões para labels:")
    return field_mapping


def clean_field_name_simple(field_name):
    """
    Limpeza simples do nome do campo para fallback
    """
    import re
    
    # Remover UUID
    clean = re.sub(r'_[a-f0-9-]{36}$', '', field_name)
    clean = re.sub(r'_[a-f0-9-]+$', '', clean)
    
    # Remover _field
    clean = clean.replace('_field', '')
    
    # Converter para legível
    words = clean.split('_')
    formatted = ' '.join(word.capitalize() for word in words if word)
    
    # Correções básicas
    corrections = {
        'Text': 'Texto',
        'Number': 'Número', 
        'File Upload': 'Arquivo',
        'Nome Completo': 'Nome Completo'
    }
    
    for old, new in corrections.items():
        formatted = formatted.replace(old, new)
    
    return formatted or 'Campo'


def download_csv_with_enap_labels_v4(request, page_id):
    """
    Download CSV com mapeamento DEFINITIVO v4
    """
    page = get_object_or_404(FormularioPage, id=page_id)
    submissions = FormularioSubmission.objects.filter(page=page).order_by('-submit_time')
    
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="submissoes_{page.slug}_{page.id}.csv"'
    response.write('\ufeff')
    
    writer = csv.writer(response)
    
    if not submissions.exists():
        writer.writerow(['Nenhuma submissão encontrada'])
        return response
    
    print(f"🚀 Gerando CSV com labels ENAP para: {page.title}")
    
    # 1. Extrair labels v4 (mapeamento UUID → Label)
    uuid_to_label, field_order = extract_labels_from_enap_form_steps_v4(page)
    
    # 2. Coletar campos das submissões
    all_fields = set()
    for submission in submissions:
        if submission.form_data:
            all_fields.update(submission.form_data.keys())
    
    # Ordenar campos mantendo ordem lógica
    ordered_fields = sorted(list(all_fields))
    
    # 3. Mapear campos para labels v4 (EXATO)
    field_mapping = map_submission_fields_to_labels_v4(ordered_fields, uuid_to_label, field_order)
    
    # 4. Criar headers
    headers = ['Data/Hora', 'IP do Usuário']
    
    print(f"📋 HEADERS FINAIS DO CSV:")
    for i, field in enumerate(ordered_fields):
        display_name = field_mapping[field]
        headers.append(display_name)
        print(f"   🏷️ {display_name}")
    
    writer.writerow(headers)
    
    # 5. Escrever dados
    for submission in submissions:
        row = [
            submission.submit_time.strftime('%d/%m/%Y %H:%M:%S'),
            submission.user_ip or 'N/A',
        ]
        
        for field in ordered_fields:
            value = submission.form_data.get(field, '') if submission.form_data else ''
            formatted_value = format_field_value_for_csv(field, value, page_id, submission, request)
            row.append(formatted_value)
        
        writer.writerow(row)
    
    print(f"✅ CSV ENAP gerado com {submissions.count()} submissões!")
    return response


def download_csv_dinamico_with_enap_labels_v4(request, page_id):
    """
    Download CSV dinâmico com mapeamento DEFINITIVO v4
    """
    try:
        from .models import FormularioDinamicoSubmission
        
        submissoes = FormularioDinamicoSubmission.objects.filter(
            object_id=page_id
        ).order_by('-submit_time')
        
        if not submissoes.exists():
            return HttpResponse('Nenhuma submissão encontrada', status=404)
        
        first_submission = submissoes.first()
        page_title = first_submission.page_title or f'Página {page_id}'
        page = first_submission.page
        
        print(f"🚀 Gerando CSV dinâmico com labels ENAP para: {page_title}")
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="dinamico_{page_title}_{page_id}.csv"'
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        # Extrair labels se a página existir
        uuid_to_label, field_order = {}, []
        if page:
            uuid_to_label, field_order = extract_labels_from_enap_form_steps_v4(page)
        
        # Coletar campos
        all_fields = set()
        for submissao in submissoes:
            if submissao.form_data:
                all_fields.update(submissao.form_data.keys())
        
        ordered_fields = sorted(list(all_fields))
        
        # Mapear campos v4
        field_mapping = map_submission_fields_to_labels_v4(ordered_fields, uuid_to_label, field_order)
        
        # Headers
        headers = ['Data/Hora', 'Nome', 'Email', 'Telefone', 'IP']
        
        print(f"📋 HEADERS DINÂMICOS:")
        for i, field in enumerate(ordered_fields):
            display_name = field_mapping[field]
            headers.append(display_name)
            print(f"   🏷️ {display_name}")
        
        writer.writerow(headers)
        
        # Dados
        for submissao in submissoes:
            row = [
                submissao.submit_time.strftime('%d/%m/%Y %H:%M:%S'),
                submissao.user_name or '',
                submissao.user_email or '',
                submissao.user_phone or '',
                submissao.user_ip or '',
            ]
            
            for field in ordered_fields:
                value = submissao.form_data.get(field, '') if submissao.form_data else ''
                formatted_value = format_field_value_for_csv(field, value, submissao, request)
                row.append(formatted_value)
            
            writer.writerow(row)
        
        print(f"✅ CSV dinâmico ENAP gerado com {submissoes.count()} linhas")
        return response
        
    except ImportError:
        return HttpResponse('FormularioDinamicoSubmission não encontrado', status=404)
    except Exception as e:
        print(f"❌ Erro no CSV dinâmico: {e}")
        return HttpResponse(f'Erro: {str(e)}', status=500)



def test_enap_label_extraction(page_id):
    """
    Testa a extração de labels ENAP
    """
    try:
        from enap_designsystem.blocks.form import FormularioPage
        page = FormularioPage.objects.get(id=page_id)
        
        print(f"🧪 TESTE DE EXTRAÇÃO ENAP LABELS - {page.title}")
        print("="*60)
        
        # Extrair labels
        labels = extract_labels_from_enap_form_steps(page)
        
        # Testar com submissões
        submissions = FormularioSubmission.objects.filter(page=page)
        if submissions.exists():
            first_submission = submissions.first()
            if first_submission.form_data:
                submission_fields = list(first_submission.form_data.keys())
                
                print(f"\n📊 MAPEAMENTO FINAL:")
                field_mapping = map_submission_fields_to_labels(submission_fields, labels)
                
                print(f"\n🎯 RESULTADO ESPERADO NO CSV:")
                for field, label in field_mapping.items():
                    print(f"   📝 Coluna: '{label}'")
        
        return labels
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return {}

"""
IMPLEMENTAÇÃO FINAL:

1. Substitua as URLs por:
path('export-csv/<int:page_id>/', download_csv_with_enap_labels, name='download_csv'),
path('export-dinamico-csv/<int:page_id>/', download_csv_dinamico_with_enap_labels, name='download_csv_dinamico'),

2. Teste antes:
from yourapp.wagtail_hooks import test_enap_label_extraction
test_enap_label_extraction(55)

RESULTADO ESPERADO NO CSV:
- Data/Hora
- IP do Usuário
- Isso é um nome  ← FUNCIONANDO! 🎉
- Nome Completo
- Anexar arquivo  
- Isso é
"""






@hooks.register('construct_page_listing_buttons')
def hide_add_child_button(buttons, page, page_perms, context=None):
    """
    Remove botões de adicionar página se o usuário não tem permissão
    """
    if context and 'request' in context:
        user = context['request'].user
        if not user.is_superuser:
            from .models import GroupPageTypePermission
            allowed_types = GroupPageTypePermission.get_allowed_page_types_for_user(user)
            if not allowed_types:
                buttons[:] = [btn for btn in buttons if 'add-child' not in btn.get('classname', '')]
    return buttons

@hooks.register('construct_page_chooser_queryset')
def limit_page_chooser_queryset(pages, request):
    """
    Limita quais páginas aparecem no page chooser
    """
    if request.user.is_superuser:
        return pages
    
    from .models import GroupPageTypePermission
    allowed_types = GroupPageTypePermission.get_allowed_page_types_for_user(request.user)
    
    if allowed_types:
        allowed_content_types = []
        for page_type in allowed_types:
            try:
                ct = ContentType.objects.get_for_model(page_type)
                allowed_content_types.append(ct.id)
            except:
                pass
        
        if allowed_content_types:
            return pages.filter(content_type_id__in=allowed_content_types)
    
    return pages.none()

@hooks.register('before_create_page')
def check_page_creation_permission(request, parent_page, page_class):
    """
    Verifica permissão antes de criar página
    """
    if request.user.is_superuser:
        return
    
    from .models import GroupPageTypePermission
    allowed_types = GroupPageTypePermission.get_allowed_page_types_for_user(request.user)
    
    if allowed_types and page_class not in allowed_types:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied(f"Você não tem permissão para criar páginas do tipo {page_class.__name__}")

@hooks.register('before_edit_page')  
def check_page_edit_permission(request, page):
    """
    Verifica permissão antes de editar página
    """
    if request.user.is_superuser:
        return
    
    from .models import GroupPageTypePermission
    allowed_types = GroupPageTypePermission.get_allowed_page_types_for_user(request.user)
    page_type = type(page)
    
    if allowed_types and page_type not in allowed_types:
        from django.core.exceptions import PermissionDenied  
        raise PermissionDenied(f"Você não tem permissão para editar páginas do tipo {page_type.__name__}")

@hooks.register('construct_main_menu')
def hide_snippets_from_menu(request, menu_items):
    """
    Opcional: Esconder o menu de snippets para usuários não-admin
    """
    if not request.user.is_superuser:
        menu_items[:] = [item for item in menu_items if item.name != 'snippets']










# wagtail_hooks.py - Versão mínima: só menu + CSV

from wagtail import hooks
from django.http import HttpResponse
import csv


# Página de estatísticas simples
def dashboard_votacao_view(request):
    """Página simples com estatísticas"""
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()
    
    try:
        from .models import VotoRegistrado, CategoriaVotacao, ProjetoVotacao
        from django.db.models import Count
        
        total_votos = VotoRegistrado.objects.count()
        total_categorias = CategoriaVotacao.objects.filter(ativo=True).count() 
        total_projetos = ProjetoVotacao.objects.filter(ativo=True).count()
        
        # Ranking geral
        ranking_geral = (VotoRegistrado.objects
                         .values('projeto__titulo', 'projeto__nome_equipe', 'projeto__categoria__nome')
                         .annotate(votos=Count('id'))
                         .order_by('-votos')[:10])
        
        # Mais votado por categoria
        categorias = CategoriaVotacao.objects.filter(ativo=True).order_by('ordem')
        mais_votados_categoria = {}
        
        for categoria in categorias:
            mais_votado = (VotoRegistrado.objects
                          .filter(projeto__categoria=categoria)
                          .values('projeto__titulo', 'projeto__nome_equipe')
                          .annotate(votos=Count('id'))
                          .order_by('-votos')
                          .first())
            if mais_votado:
                mais_votados_categoria[categoria] = mais_votado
        
        html = f"""
        <html>
        <head>
            <title>Dashboard Votação</title>
            <link rel="stylesheet" href="/static/wagtailadmin/css/core.css">
            <style>
                body {{ margin: 20px; font-family: Arial, sans-serif; }}
                .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
                .stat {{ background: #024248; color: white; padding: 20px; border-radius: 8px; text-align: center; flex: 1; }}
                .stat-number {{ font-size: 28px; font-weight: bold; }}
                .ranking {{ background: white; border: 1px solid #ddd; border-radius: 8px; margin: 20px 0; }}
                .ranking-item {{ padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; }}
                .categoria-card {{ background: white; border: 1px solid #ddd; border-radius: 8px; margin: 15px 0; }}
                .categoria-header {{ background: #007D7A; color: white; padding: 15px; font-weight: bold; }}
                .categoria-content {{ padding: 20px; }}
                .btn {{ background: #007D7A; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px; }}
                .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }}
            </style>
        </head>
        <body>
            <h1 style="color: #024248;">Dashboard de Votação</h1>
            <a href="/admin/" class="btn">← Voltar ao Admin</a>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">{total_votos}</div>
                    <div>Total Votos</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{total_projetos}</div>
                    <div>Projetos</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{total_categorias}</div>
                    <div>Categorias</div>
                </div>
            </div>
            
            <div class="grid">
                <div>
                    <h2>Mais Votados por Categoria</h2>
        """
        
        # Seção de mais votados por categoria
        if mais_votados_categoria:
            for categoria, projeto in mais_votados_categoria.items():
                html += f"""
                <div class="categoria-card">
                    <div class="categoria-header">
                        {categoria.nome}
                    </div>
                    <div class="categoria-content">
                        <strong style="font-size: 18px;">{projeto['projeto__titulo']}</strong>
                        <br>
                        <small style="color: #666;">{projeto['projeto__nome_equipe']}</small>
                        <div style="margin-top: 10px;">
                            <span style="background: #024248; color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold;">
                                {projeto['votos']} votos
                            </span>
                        </div>
                    </div>
                </div>
                """
        else:
            html += "<p style='text-align: center; color: #999;'>Nenhum voto por categoria ainda</p>"
        
        html += """
                </div>
                <div>
                    <h2>Ranking Geral</h2>
                    <div class="ranking">
        """
        
        # Ranking geral
        if ranking_geral:
            for i, item in enumerate(ranking_geral, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}º"
                html += f"""
                <div class="ranking-item">
                    <div>
                        <strong>{medal}</strong>
                        <strong>{item['projeto__titulo']}</strong>
                        <br>
                        <small>{item['projeto__nome_equipe']} • {item['projeto__categoria__nome']}</small>
                    </div>
                    <div style="background: #024248; color: white; padding: 5px 15px; border-radius: 15px;">
                        {item['votos']}
                    </div>
                </div>
                """
        else:
            html += "<p style='padding: 40px; text-align: center;'>Nenhum voto registrado</p>"
        
        html += """
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="/admin/exportar-votos/" class="btn">Exportar Todos os Votos (CSV)</a>
                <a href="/admin/exportar-ranking/" class="btn">Exportar Ranking (CSV)</a>
            </div>
        </body>
        </html>
        """
        
        return HttpResponse(html)
        
    except Exception as e:
        return HttpResponse(f"<h1>Erro</h1><p>{e}</p><a href='/admin/'>Voltar</a>")


# Exportar todos os votos
def exportar_votos(request):
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()
    
    try:
        from .models import VotoRegistrado
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="todos_votos.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Data/Hora', 'Projeto', 'Categoria', 'Equipe', 'IP'])
        
        votos = VotoRegistrado.objects.select_related('projeto', 'projeto__categoria').order_by('-timestamp')
        
        for voto in votos:
            writer.writerow([
                str(voto.id),
                voto.timestamp.strftime('%d/%m/%Y %H:%M:%S'),
                voto.projeto.titulo,
                voto.projeto.categoria.nome,
                voto.projeto.nome_equipe,
                voto.ip_address
            ])
        
        return response
        
    except Exception as e:
        return HttpResponse(f"Erro: {e}")


# Exportar ranking
def exportar_ranking(request):
    if not request.user.is_staff:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()
    
    try:
        from .models import VotoRegistrado, CategoriaVotacao
        from django.db.models import Count
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="ranking_votacao.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Categoria', 'Posição', 'Projeto', 'Equipe', 'Total Votos'])
        
        # Por categoria
        categorias = CategoriaVotacao.objects.filter(ativo=True).order_by('ordem')
        
        for categoria in categorias:
            ranking = (VotoRegistrado.objects
                      .filter(projeto__categoria=categoria)
                      .values('projeto__titulo', 'projeto__nome_equipe')
                      .annotate(votos=Count('id'))
                      .order_by('-votos'))
            
            for i, item in enumerate(ranking, 1):
                writer.writerow([
                    categoria.nome,
                    i,
                    item['projeto__titulo'],
                    item['projeto__nome_equipe'],
                    item['votos']
                ])
        
        return response
        
    except Exception as e:
        return HttpResponse(f"Erro: {e}")


# Menu lateral - só isso
@hooks.register('construct_main_menu')
def menu_dashboard_votacao(request, menu_items):
    from wagtail.admin.menu import MenuItem
    
    if request.user.is_staff:
        menu_items.append(MenuItem(
            'Dashboard Votação',
            '/admin/dashboard-votacao/',
            icon_name='view',
            order=450
        ))


# URLs
@hooks.register('register_admin_urls')
def register_urls():
    from django.urls import path
    return [
        path('dashboard-votacao/', dashboard_votacao_view, name='dashboard_votacao'),
        path('exportar-votos/', exportar_votos, name='exportar_votos'),
        path('exportar-ranking/', exportar_ranking, name='exportar_ranking'),
    ]




# wagtail_hooks.py - Crie este arquivo na raiz do seu app

from django.urls import path, reverse
from django.utils.html import format_html
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.template import Template, Context
import json

from wagtail import hooks
from wagtail.admin import widgets
from wagtail.admin.menu import MenuItem

# Suas views movidas para hooks
def formulario_scoring_view(request, page_id):
    """Configura pontuação dos campos"""
    from .models import FormularioPage, FormFieldScoring
    
    page = get_object_or_404(FormularioPage, pk=page_id)
    
    if not getattr(page, 'enable_scoring', False):
        messages.error(request, "Sistema de pontuação não está ativado.")
        return redirect('wagtailadmin_pages:edit', page_id)
    
    if request.method == 'POST':
        try:
            scoring_data = json.loads(request.POST.get('scoring_data', '{}'))
            
            for field_id, field_scoring in scoring_data.items():
                page.save_field_scoring(field_id, field_scoring)
            
            messages.success(request, "Pontuações salvas com sucesso!")
            return redirect('formulario_scoring_admin', page_id)
        
        except Exception as e:
            messages.error(request, f"Erro ao salvar: {str(e)}")
    
    scorable_fields = page.extract_scorable_fields()
    
    existing_scorings = {}
    for scoring in FormFieldScoring.objects.filter(formulario_page=page):
        existing_scorings[scoring.field_id] = scoring.scoring_data
    
    # Template inline
    template_content = """
    {% extends "wagtailadmin/base.html" %}
    {% load wagtailadmin_tags %}
    
    {% block titletag %}Configurar Pontuação - {{ page.title }}{% endblock %}
    
    {% block content %}
    <div class="nice-padding">
        <header class="tab-merged">
            <h1>🏆 Configurar Pontuação: {{ page.title }}</h1>
            <p>Configure quantos pontos cada resposta vale. Os usuários não verão as pontuações.</p>
        </header>
        
        {% if messages %}
        <ul class="messages">
            {% for message in messages %}
            <li class="message {{ message.tags }}">{{ message }}</li>
            {% endfor %}
        </ul>
        {% endif %}
        
        <form method="post" id="scoring-form">
            {% csrf_token %}
            <input type="hidden" name="scoring_data" id="scoring-data-input">
            
            {% for field in scorable_fields %}
            <div class="field-section" style="background: #f9f9f9; border: 1px solid #e1e5e9; padding: 20px; margin: 20px 0; border-radius: 6px;">
                <h3>📝 {{ field.field_label }}</h3>
                <div style="margin-bottom: 15px; font-size: 13px; color: #666;">
                    <strong>Tipo:</strong> {{ field.field_type }} | 
                    <strong>Etapa:</strong> {{ field.step_number }}
                </div>
                
                <div class="scoring-options">
                    {% for option in field.options %}
                    <div style="margin: 12px 0; display: flex; align-items: center; gap: 15px; background: white; padding: 10px; border-radius: 4px;">
                        <label style="min-width: 250px; font-weight: normal;">"{{ option }}"</label>
                        <input type="number" 
                               class="scoring-input" 
                               data-field="{{ field.field_id }}" 
                               data-option="{{ option }}"
                               placeholder="0" 
                               step="0.1"
                               style="width: 80px; text-align: center; padding: 5px; border: 1px solid #ccc; border-radius: 4px;">
                        <span style="font-size: 12px; color: #666;">pontos</span>
                    </div>
                    {% endfor %}
                    
                    {% if field.field_type == 'checkbox_multiple_field' %}
                    <div style="margin-top: 20px; padding: 15px; background: #fff3cd; border-radius: 4px;">
                        <label style="font-weight: bold;">
                            ⚙️ Método de cálculo para múltiplas seleções:
                        </label>
                        <select class="calculation-method" data-field="{{ field.field_id }}" style="margin-left: 10px; padding: 4px;">
                            <option value="sum">Somar todos os pontos</option>
                            <option value="max">Usar apenas o maior valor</option>
                            <option value="average">Calcular média dos valores</option>
                        </select>
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
            
            {% if not scorable_fields %}
            <div style="text-align: center; padding: 40px; color: #666;">
                <h3>📝 Nenhum campo encontrado</h3>
                <p>Adicione campos dropdown, rádio ou checkbox múltiplo ao formulário.</p>
            </div>
            {% endif %}
            
            <div style="margin-top: 30px;">
                <button type="submit" class="button button-primary">Salvar Pontuações</button>
                <a href="{% url 'formulario_results_admin' page.pk %}" class="button">Ver Resultados</a>
                <a href="{% url 'wagtailadmin_pages:edit' page.pk %}" class="button">Voltar ao Formulário</a>
            </div>
        </form>
    </div>
    
    <script>
    const existingScorings = {{ existing_scorings_json|safe }};
    
    // Carregar valores existentes
    for (const [fieldId, scoring] of Object.entries(existingScorings)) {
        const optionScores = scoring.option_scores || {};
        
        for (const [option, score] of Object.entries(optionScores)) {
            const input = document.querySelector(`input[data-field="${fieldId}"][data-option="${option}"]`);
            if (input) input.value = score;
        }
        
        const methodSelect = document.querySelector(`select[data-field="${fieldId}"]`);
        if (methodSelect && scoring.calculation_method) {
            methodSelect.value = scoring.calculation_method;
        }
    }
    
    // Envio do formulário
    document.getElementById('scoring-form').addEventListener('submit', function(e) {
        const scoringData = {};
        
        document.querySelectorAll('.field-section').forEach(section => {
            const inputs = section.querySelectorAll('.scoring-input');
            if (inputs.length === 0) return;
            
            const fieldId = inputs[0].dataset.field;
            const optionScores = {};
            
            inputs.forEach(input => {
                const option = input.dataset.option;
                const score = parseFloat(input.value) || 0;
                optionScores[option] = score;
            });
            
            scoringData[fieldId] = { option_scores: optionScores };
            
            const methodSelect = section.querySelector('.calculation-method');
            if (methodSelect) {
                scoringData[fieldId].calculation_method = methodSelect.value;
            }
        });
        
        document.getElementById('scoring-data-input').value = JSON.stringify(scoringData);
    });
    </script>
    
    {% endblock %}
    """
    
    template = Template(template_content)
    context = Context({
        'page': page,
        'scorable_fields': scorable_fields,
        'existing_scorings': existing_scorings,
        'existing_scorings_json': json.dumps(existing_scorings),
        'messages': messages.get_messages(request),
    })
    
    return HttpResponse(template.render(context))


def formulario_results_view(request, page_id):
    """Mostra resultados com pontuação"""
    from .models import FormularioPage, FormularioSubmissionScored
    
    page = get_object_or_404(FormularioPage, pk=page_id)
    submissions = page.formulariosubmission_set.all().order_by('-submit_time')
    
    scored_submissions = []
    total_scores = []
    
    for submission in submissions:
        score, details = page.calculate_submission_score(submission)
        
        scored_sub, created = FormularioSubmissionScored.objects.get_or_create(
            original_submission=submission,
            defaults={'total_score': score, 'score_details': details}
        )
        
        if not created and scored_sub.total_score != score:
            scored_sub.total_score = score
            scored_sub.score_details = details
            scored_sub.save()
        
        scored_submissions.append({
            'submission': submission,
            'score': score,
            'details': details
        })
        
        if score > 0:
            total_scores.append(score)
    
    stats = {
        'total': len(submissions),
        'average': sum(total_scores) / len(total_scores) if total_scores else 0,
        'max_score': max(total_scores) if total_scores else 0,
        'min_score': min(total_scores) if total_scores else 0,
    }
    
    # Template inline para resultados
    template_content = """
    {% extends "wagtailadmin/base.html" %}
    {% load wagtailadmin_tags %}
    
    {% block titletag %}Resultados com Pontuação - {{ page.title }}{% endblock %}
    
    {% block content %}
    <div class="nice-padding">
        <header class="tab-merged">
            <h1>📊 Resultados: {{ page.title }}</h1>
        </header>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0;">
            <div style="background: #e8f4fd; padding: 20px; border-radius: 6px; text-align: center;">
                <div style="font-size: 24px; font-weight: bold; color: #0066cc;">{{ stats.total }}</div>
                <div style="color: #666;">Total de Submissões</div>
            </div>
            <div style="background: #e8f5e8; padding: 20px; border-radius: 6px; text-align: center;">
                <div style="font-size: 24px; font-weight: bold; color: #28a745;">{{ stats.average|floatformat:1 }}</div>
                <div style="color: #666;">Pontuação Média</div>
            </div>
            <div style="background: #fff3cd; padding: 20px; border-radius: 6px; text-align: center;">
                <div style="font-size: 24px; font-weight: bold; color: #856404;">{{ stats.max_score }}</div>
                <div style="color: #666;">Maior Pontuação</div>
            </div>
            <div style="background: #f8d7da; padding: 20px; border-radius: 6px; text-align: center;">
                <div style="font-size: 24px; font-weight: bold; color: #721c24;">{{ stats.min_score }}</div>
                <div style="color: #666;">Menor Pontuação</div>
            </div>
        </div>
        
        <div style="margin: 20px 0;">
            <a href="{% url 'formulario_scoring_admin' page.pk %}" class="button button-primary">Configurar Pontuação</a>
            <a href="{% url 'wagtailadmin_pages:edit' page.pk %}" class="button">Editar Formulário</a>
        </div>
        
        <table class="listing">
            <thead>
                <tr>
                    <th>Data/Hora</th>
                    <th>Pontuação</th>
                    <th>IP</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
                {% for item in scored_submissions %}
                <tr>
                    <td>{{ item.submission.submit_time|date:"d/m/Y H:i" }}</td>
                    <td><strong style="color: #0066cc;">{{ item.score|floatformat:1 }} pts</strong></td>
                    <td>{{ item.submission.user_ip|default:"-" }}</td>
                    <td>
                        <button onclick="showDetails({{ item.submission.pk }}, {{ item.score }}, {{ item.details|safe }})" 
                                class="button button-small">
                            Ver Detalhes
                        </button>
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="4" style="text-align: center; padding: 40px; color: #666;">
                        Nenhuma submissão encontrada
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <!-- Modal para detalhes -->
    <div id="detailsModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000;">
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 8px; max-width: 600px; max-height: 80vh; overflow-y: auto;">
            <h3>Detalhes da Pontuação</h3>
            <div id="modalContent"></div>
            <button onclick="closeModal()" class="button">Fechar</button>
        </div>
    </div>
    
    <script>
    function showDetails(submissionId, totalScore, details) {
        const modal = document.getElementById('detailsModal');
        const content = document.getElementById('modalContent');
        
        let html = `<div style="margin-bottom: 20px;">
            <strong>Pontuação Total: ${totalScore.toFixed(1)} pontos</strong>
        </div>`;
        
        if (details && details.length > 0) {
            html += '<h4>Detalhamento:</h4>';
            details.forEach(detail => {
                html += `
                    <div style="border: 1px solid #eee; padding: 15px; margin: 10px 0; border-radius: 4px;">
                        <strong>${detail.field_label}</strong><br>
                        <span style="color: #666;">Resposta: "${detail.user_response}"</span><br>
                        <span style="color: #0066cc; font-weight: bold;">Pontos: ${detail.field_score}</span>
                    </div>
                `;
            });
        } else {
            html += '<p style="color: #666;">Nenhum detalhe disponível.</p>';
        }
        
        content.innerHTML = html;
        modal.style.display = 'block';
    }
    
    function closeModal() {
        document.getElementById('detailsModal').style.display = 'none';
    }
    
    document.getElementById('detailsModal').addEventListener('click', function(e) {
        if (e.target === this) closeModal();
    });
    </script>
    
    {% endblock %}
    """
    
    template = Template(template_content)
    context = Context({
        'page': page,
        'scored_submissions': scored_submissions,
        'stats': stats,
    })
    
    return HttpResponse(template.render(context))


# Hook para registrar URLs no admin
@hooks.register('register_admin_urls')
def register_scoring_urls():
    return [
        path('formulario/<int:page_id>/pontuacao/', formulario_scoring_view, name='formulario_scoring_admin'),
        path('formulario/<int:page_id>/resultados/', formulario_results_view, name='formulario_results_admin'),
    ]


# Hook para adicionar botões na página de edição
@hooks.register('register_page_action_menu_item')
def add_scoring_menu_item(page):
    # Só mostrar para FormularioPage
    if hasattr(page, 'form_steps') and getattr(page, 'enable_scoring', False):
        return widgets.PageActionMenuItem(
            'Configurar Pontuação',
            reverse('formulario_scoring_admin', args=[page.pk]),
            priority=10
        )


@hooks.register('register_page_action_menu_item')
def add_results_menu_item(page):
    # Só mostrar para FormularioPage
    if hasattr(page, 'form_steps') and getattr(page, 'enable_scoring', False):
        return widgets.PageActionMenuItem(
            'Ver Resultados',
            reverse('formulario_results_admin', args=[page.pk]),
            priority=11
        )

