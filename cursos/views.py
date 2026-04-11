import os
import json
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST

from django.utils.html import escape

from .models import Course, Modulo, Turma, Enrollment, User, Lesson, Attachment, UserLessonProgress, BlocoVideo
from .forms import CourseForm, StudentCreationForm, TurmaForm, EnrollmentForm, LessonForm

# --- MIXIN DE SEGURANÇA ---
class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

# --- VIEWS DE CURSO ---
class CourseListView(ListView):
    model = Course
    template_name = 'cursos/lista_cursos.html'
    context_object_name = 'cursos'
    def get_queryset(self):
        qs = Course.objects.filter(is_active=True).order_by('-created_at')
        if not self.request.user.is_staff:
            qs = qs.filter(turmas__students=self.request.user).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import HistoricoVideo
        history_records = HistoricoVideo.objects.filter(user=self.request.user).select_related('lesson', 'lesson__modulo__course').order_by('-data_visualizacao')
        unique_lessons = []
        seen = set()
        for record in history_records:
            if record.lesson_id not in seen:
                seen.add(record.lesson_id)
                unique_lessons.append(record)
            if len(unique_lessons) == 4:
                break
        context['historico'] = unique_lessons
        return context

class CourseCreateView(StaffRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'cursos/criar_curso.html'
    success_url = reverse_lazy('lista_cursos')

class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'cursos/detalhe_curso.html'
    context_object_name = 'curso'

    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True)
        if not self.request.user.is_staff:
            qs = qs.filter(turmas__students=self.request.user).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        modulos = list(self.object.modulos.prefetch_related(
            'lessons__attachments',
            'lessons__blocos'
        ))
        
        from .models import UserLessonProgress, UserBlocoProgress
        
        # Array plano para resgatar progressos das Aulas
        aulas = []
        for mod in modulos:
            aulas.extend(mod.lessons.all())
            
        progressos_aula = UserLessonProgress.objects.filter(
            user=self.request.user, lesson__in=aulas
        )
        prog_aula_map = {p.lesson_id: p for p in progressos_aula}

        # Array plano para resgatar progressos dos Blocos
        blocos = []
        for aula in aulas:
            blocos.extend(aula.blocos.all())

        progressos_bloco = UserBlocoProgress.objects.filter(
            user=self.request.user, bloco__in=blocos
        )
        prog_bloco_map = {p.bloco_id: p for p in progressos_bloco}

        # Injetando anotações na Aula e 'is_completed' dinamicamente nos blocos!
        for mod in modulos:
            for aula in mod.lessons.all():
                p_aula = prog_aula_map.get(aula.id)
                aula.user_notes = p_aula.notes if p_aula and p_aula.notes else ""
                
                # Check blocos
                all_completed = True
                blocos_of_lesson = list(aula.blocos.all())
                for bloco in blocos_of_lesson:
                    p_bloco = prog_bloco_map.get(bloco.id)
                    bloco.is_completed = p_bloco.is_completed if p_bloco else False
                    bloco.saved_time = p_bloco.video_time if p_bloco else 0.0
                    if not bloco.is_completed:
                        all_completed = False
                
                # Uma aula só está completa se TODOS os blocos estiverem completos
                aula.is_completed = all_completed and len(blocos_of_lesson) > 0

        context['modulos'] = modulos
        return context

@staff_member_required
def api_get_modulos(request, course_id):
    modulos = list(Modulo.objects.filter(course_id=course_id).order_by('order').values('id', 'title', 'order'))
    return JsonResponse({'modulos': modulos})

# --- VIEWS DE AULA ---
class LessonListView(StaffRequiredMixin, ListView):
    model = Lesson
    template_name = 'cursos/lista_aulas.html'
    context_object_name = 'aulas'

    def get_queryset(self):
        return super().get_queryset().select_related('modulo', 'modulo__course').prefetch_related('blocos').order_by('modulo__course__title', 'modulo__order', 'order')

class LessonCreateView(StaffRequiredMixin, CreateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'cursos/criar_aula.html'

    def form_valid(self, form):
        aula = form.save()
        arquivos = self.request.FILES.getlist('arquivos_extras')
        allowed_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt', '.zip', '.rar', '.jpg', '.jpeg', '.png']
        max_file_size = 500 * 1024 * 1024  # 500MB
        for f in arquivos:
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in allowed_extensions:
                form.add_error(None, f'Extensão de arquivo não permitida: {f.name}')
                if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'error': f'Extensão não permitida: {f.name}'}, status=400)
                return self.form_invalid(form)
            if f.size > max_file_size:
                form.add_error(None, f'Arquivo muito grande: {f.name} (máximo 500MB)')
                if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'error': f'Arquivo gigante: {f.name}'}, status=400)
                return self.form_invalid(form)
            Attachment.objects.create(lesson=aula, title=f.name, file=f)
            
        course_pk = aula.modulo.course.pk if aula.modulo else 1
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.urls import reverse
            return JsonResponse({'status': 'success', 'lesson_id': aula.id, 'redirect_url': reverse('detalhe_curso', kwargs={'pk': course_pk})})
            
        messages.success(self.request, "Aula criada com sucesso!")
        return redirect('detalhe_curso', pk=course_pk)

class LessonUpdateView(StaffRequiredMixin, UpdateView):
    model = Lesson
    form_class = LessonForm
    template_name = 'cursos/criar_aula.html'

    def get_initial(self):
        initial = super().get_initial()
        if self.object.modulo:
            initial['curso_selecionador'] = self.object.modulo.course.pk
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blocos'] = self.object.blocos.all()
        return context

    def form_valid(self, form):
        aula = form.save()
        arquivos = self.request.FILES.getlist('arquivos_extras')
        allowed_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt', '.zip', '.rar', '.jpg', '.jpeg', '.png']
        max_file_size = 500 * 1024 * 1024  # 500MB
        for f in arquivos:
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in allowed_extensions:
                form.add_error(None, f'Extensão de arquivo não permitida: {f.name}')
                if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'error': f'Extensão não permitida: {f.name}'}, status=400)
                return self.form_invalid(form)
            if f.size > max_file_size:
                form.add_error(None, f'Arquivo muito grande: {f.name} (máximo 500MB)')
                if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'error': f'Arquivo gigante: {f.name}'}, status=400)
                return self.form_invalid(form)
            Attachment.objects.create(lesson=aula, title=f.name, file=f)
                    
        deleted_blocos_str = self.request.POST.get('deleted_blocos', '')
        if deleted_blocos_str:
            for did in deleted_blocos_str.split(','):
                if did.isdigit():
                     BlocoVideo.objects.filter(id=did, lesson=aula).delete()

        course_pk = aula.modulo.course.pk if aula.modulo else 1
        
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.urls import reverse
            return JsonResponse({'status': 'success', 'lesson_id': aula.id, 'redirect_url': reverse('detalhe_curso', kwargs={'pk': course_pk})})
            
        messages.success(self.request, "Aula atualizada com sucesso!")
        return redirect('detalhe_curso', pk=course_pk)

@staff_member_required
@require_POST
def api_upload_bloco(request):
    lesson_id = request.POST.get('lesson_id')
    bloco_id = request.POST.get('bloco_id')
    title = request.POST.get('title')
    order = request.POST.get('order', 0)
    video = request.FILES.get('video')
    
    aula = get_object_or_404(Lesson, id=lesson_id)
    
    title = title or f"Vídeo {int(order)+1}"
    
    if bloco_id:
        try:
            bloco = BlocoVideo.objects.get(id=bloco_id, lesson=aula)
            bloco.title = title
            bloco.order = int(order)
            if video:
                bloco.video = video
            bloco.save()
            return JsonResponse({'status': 'success'})
        except BlocoVideo.DoesNotExist:
            pass
            
    if video:
        BlocoVideo.objects.create(lesson=aula, title=title, video=video, order=int(order))
        return JsonResponse({'status': 'success'})
        
    return JsonResponse({'status': 'success'})

@staff_member_required
@require_POST
def delete_lesson_view(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    senha_digitada = request.POST.get('password', '')
    
    if request.user.check_password(senha_digitada):
        title = lesson.title
        lesson.delete()
        messages.success(request, f"A aula '{title}' foi excluída com sucesso.")
    else:
        messages.error(request, "Senha incorreta. A exclusão foi cancelada.")
        
    return redirect('lista_aulas')

from django.views.generic import DeleteView
from django.utils.decorators import method_decorator
from .forms import ModuloForm

@method_decorator(staff_member_required, name='dispatch')
class ModuloListView(StaffRequiredMixin, ListView):
    model = Modulo
    template_name = 'cursos/lista_modulos.html'
    context_object_name = 'modulos'

    def get_queryset(self):
        return super().get_queryset().select_related('course').order_by('course__title', 'order')

@method_decorator(staff_member_required, name='dispatch')
class ModuloCreateView(StaffRequiredMixin, CreateView):
    model = Modulo
    form_class = ModuloForm
    template_name = 'cursos/criar_modulo.html'
    success_url = reverse_lazy('lista_modulos')
    
    def form_valid(self, form):
        messages.success(self.request, "Módulo criado com sucesso!")
        return super().form_valid(form)

@method_decorator(staff_member_required, name='dispatch')
class ModuloUpdateView(StaffRequiredMixin, UpdateView):
    model = Modulo
    form_class = ModuloForm
    template_name = 'cursos/criar_modulo.html'
    success_url = reverse_lazy('lista_modulos')
    
    def form_valid(self, form):
        messages.success(self.request, "Módulo atualizado com sucesso!")
        return super().form_valid(form)

@method_decorator(staff_member_required, name='dispatch')
class ModuloDeleteView(StaffRequiredMixin, DeleteView):
    model = Modulo
    success_url = reverse_lazy('lista_modulos')
    template_name = 'cursos/deletar_modulo.html'
    
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(request, f"Módulo '{obj.title}' deletado com sucesso!")
        return super().delete(request, *args, **kwargs)


# --- VIEWS DE GESTÃO (USUÁRIOS, TURMAS, MATRÍCULAS) ---
class UserCreateView(StaffRequiredMixin, CreateView):
    model = User
    form_class = StudentCreationForm
    template_name = 'cursos/criar_usuario.html'
    success_url = reverse_lazy('criar_usuario')
    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True
        user.save()
        return super().form_valid(form)

class UserListView(StaffRequiredMixin, ListView):
    model = User
    template_name = 'cursos/lista_usuarios.html'
    context_object_name = 'usuarios'
    def get_queryset(self):
        return User.objects.filter(is_active=True).order_by('first_name')

class TurmaCreateView(StaffRequiredMixin, CreateView):
    model = Turma
    form_class = TurmaForm
    template_name = 'cursos/criar_turma.html'
    success_url = reverse_lazy('criar_turma')

class TurmaListView(StaffRequiredMixin, ListView):
    model = Turma
    template_name = 'cursos/lista_turmas.html'
    context_object_name = 'turmas'

class EnrollmentCreateView(StaffRequiredMixin, CreateView):
    model = Enrollment
    form_class = EnrollmentForm
    template_name = 'cursos/matricular_aluno.html'
    success_url = reverse_lazy('matricular_aluno')

class EnrollmentListView(StaffRequiredMixin, ListView):
    model = Enrollment
    template_name = 'cursos/lista_matriculas.html'
    context_object_name = 'matriculas'
    ordering = ['-created_at']

class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'cursos/perfil.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['perfil'] = self.request.user
        return context    

# --- API (JAVASCRIPT) ---
from django.views.decorators.http import require_POST

@login_required
@require_POST
def update_progress(request, lesson_id):
    try:
        data = json.loads(request.body)
        
        if data.get('action') == 'history':
            from .models import HistoricoVideo
            HistoricoVideo.objects.create(user=request.user, lesson_id=lesson_id)
            return JsonResponse({'status': 'history_saved'})

        if data.get('action') == 'bloco_progress':
            from .models import UserBlocoProgress
            bloco_id = data.get('bloco_id')
            p_bloco, created = UserBlocoProgress.objects.get_or_create(
                user=request.user, bloco_id=bloco_id
            )
            if 'video_time' in data:
                p_bloco.video_time = data['video_time']
            if 'is_completed' in data:
                p_bloco.is_completed = data['is_completed']
            p_bloco.save()
            return JsonResponse({'status': 'bloco_saved'})

        progresso, created = UserLessonProgress.objects.get_or_create(
            user=request.user, lesson_id=lesson_id
        )
        if 'notes' in data:
            new_notes = escape(data['notes'])
            if progresso.notes != new_notes:
                # Salva o novo valor e o histórico (caso tenha algo)
                progresso.notes = new_notes
                from .models import UserNotesHistory
                if new_notes.strip():
                    UserNotesHistory.objects.create(
                        user=request.user, lesson_id=lesson_id, notes=new_notes
                    )
        if 'video_time' in data:
            progresso.video_time = data['video_time']
        if 'liked' in data:
            progresso.liked = data['liked']
        progresso.save()
        return JsonResponse({'status': 'success'})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email']
    template_name = 'cursos/editar_perfil.html'
    success_url = reverse_lazy('perfil')
    success_message = "Seus dados foram atualizados com sucesso!"

    def get_object(self):
        return self.request.user

class MyPasswordChangeView(LoginRequiredMixin, SuccessMessageMixin, PasswordChangeView):
    template_name = 'cursos/alterar_senha.html'
    success_url = reverse_lazy('perfil')
    success_message = "Sua senha foi alterada com sucesso!"