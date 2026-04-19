from django.urls import path
from .views import (
    CourseListView, CourseCreateView, LessonListView, 
    UserCreateView, TurmaCreateView, EnrollmentCreateView,
    UserListView, TurmaListView, EnrollmentListView,
    CourseDetailView, LessonCreateView, LessonUpdateView, 
    UserProfileView, UserUpdateView, MyPasswordChangeView,
    ModuloListView, ModuloCreateView, ModuloUpdateView, ModuloDeleteView,
    CourseListAdminView, CourseUpdateView, confirm_delete_course,
    EnrollUserView, remove_enrollment, TurmaUpdateView, TurmaDeleteView
)
from . import views

urlpatterns = [
    # --- CURSOS ---
    path('', CourseListView.as_view(), name='lista_cursos'),
    path('criar-curso/', CourseCreateView.as_view(), name='criar_curso'),
    path('curso/<int:pk>/', CourseDetailView.as_view(), name='detalhe_curso'),
    
    # --- GESTÃO DE CURSOS (ADMIN) ---
    path('painel/cursos/', CourseListAdminView.as_view(), name='lista_cursos_admin'),
    path('painel/curso/<int:pk>/editar/', CourseUpdateView.as_view(), name='editar_curso'),
    path('painel/curso/<int:pk>/deletar/', confirm_delete_course, name='confirmar_deletar_curso'),
    path('painel/curso/<int:pk>/deletar-confirm/', views.delete_course, name='deletar_curso'),
    
    # --- API ---
    path('api/modulos/<int:course_id>/', views.api_get_modulos, name='api_get_modulos'),
    
    # --- GESTÃO DE AULAS (ADMIN) ---
    path('painel/aulas/', LessonListView.as_view(), name='lista_aulas'),
    path('painel/aula/criar/', LessonCreateView.as_view(), name='criar_aula'),
    path('painel/aula/<int:pk>/editar/', LessonUpdateView.as_view(), name='editar_aula'),
    path('painel/aula/<int:pk>/deletar/', views.delete_lesson_view, name='deletar_aula'),
    path('painel/aula/api/bloco/upload/', views.api_upload_bloco, name='api_upload_bloco'),
    path('painel/aula/<int:lesson_id>/progresso/', views.update_progress, name='update_progress'),

    # --- GESTÃO DE MÓDULOS (ADMIN) ---
    path('painel/modulos/', ModuloListView.as_view(), name='lista_modulos'),
    path('painel/modulo/criar/', ModuloCreateView.as_view(), name='criar_modulo'),
    path('painel/modulo/<int:pk>/editar/', ModuloUpdateView.as_view(), name='editar_modulo'),
    path('painel/modulo/<int:pk>/deletar/', ModuloDeleteView.as_view(), name='deletar_modulo'),

    # --- GESTÃO DE USUÁRIOS E MATRÍCULAS (ADMIN) ---
    path('painel/usuario/criar/', UserCreateView.as_view(), name='criar_usuario'),
    path('painel/usuarios/', UserListView.as_view(), name='lista_usuarios'),
    path('painel/usuario/<int:user_id>/matricular/', EnrollUserView.as_view(), name='matricular_usuario'),
    path('painel/matricula/<int:enrollment_id>/remover/', remove_enrollment, name='remover_matricula'),
    
    # --- GESTÃO DE TURMAS (ADMIN) ---
    path('painel/turmas/', TurmaListView.as_view(), name='lista_turmas'),
    path('painel/turmas/nova/', TurmaCreateView.as_view(), name='criar_turma'),
    path('painel/turmas/<int:pk>/editar/', TurmaUpdateView.as_view(), name='editar_turma'),
    path('painel/turmas/<int:pk>/excluir/', TurmaDeleteView.as_view(), name='deletar_turma'),
    path('painel/turmas/<int:turma_id>/alunos/', views.turma_alunos_view, name='turma_alunos'),
    path('painel/turmas/<int:turma_id>/exportar-emails/', views.export_turma_emails, name='export_turma_emails'),
    
    # --- MATRÍCULAS (ADMIN) ---
    path('painel/matricula/criar/', EnrollmentCreateView.as_view(), name='matricular_aluno'),
    path('painel/matriculas/', EnrollmentListView.as_view(), name='lista_matriculas'),

    # --- PERFIL DO ALUNO (ACESSO COMUM) ---
    path('perfil/', UserProfileView.as_view(), name='perfil'),
    path('perfil/editar/', UserUpdateView.as_view(), name='editar_perfil'),
    path('perfil/senha/', MyPasswordChangeView.as_view(), name='alterar_senha'),
]