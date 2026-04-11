from django.contrib.auth.models import AbstractUser
from django.db import models
import os
from django.utils.text import slugify

# Usuário
class User(AbstractUser):
    pass

# Curso
class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='courses/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# Turma (Antigo Group)
class Turma(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    
    # O Django cria a tabela de ligação (antiga GroupCourse) automaticamente aqui!
    courses = models.ManyToManyField(Course, related_name='turmas')
    
    # Liga com os usuários usando a tabela Enrollment que você já pensou
    students = models.ManyToManyField(User, through='Enrollment', related_name='turmas')

    def __str__(self):
        return self.name

# Matrícula (Usuário -> Turma)
class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # Garante que um usuário não seja matriculado duas vezes na mesma turma
        unique_together = ('user', 'turma')

# Módulo (Vinculado ao Curso)
class Modulo(models.Model):
    course = models.ForeignKey(Course, related_name='modulos', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0, help_text="Ordem do módulo no curso")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

# Aula (Vinculada ao Módulo)
def lesson_video_path(instance, filename):
    pass

def attachment_path(instance, filename):
    try:
        curso_id = instance.lesson.modulo.course.id
        modulo_id = instance.lesson.modulo.id
    except:
        curso_id = "0"
        modulo_id = "0"
    aula_id = instance.lesson.id
    
    name, ext = os.path.splitext(filename)
    clean_name = slugify(name)
    final_filename = f"{clean_name}{ext}"
    return f'anexos/c{curso_id}/m{modulo_id}/a{aula_id}/{final_filename}'

class Lesson(models.Model):
    modulo = models.ForeignKey(Modulo, related_name='lessons', on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0, help_text="Ordem da aula no módulo")
    is_free = models.BooleanField(default=False, help_text="Marque se a aula for gratuita para não-matriculados")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        modulo_title = self.modulo.title if self.modulo else "Sem Módulo"
        return f"{modulo_title} - {self.title}"

# Bloco de Vídeo (Vinculado à Aula)
def bloco_video_path(instance, filename):
    try:
        curso_id = instance.lesson.modulo.course.id
        modulo_id = instance.lesson.modulo.id
    except:
        curso_id = "0"
        modulo_id = "0"
    aula_id = instance.lesson.id
    
    name, ext = os.path.splitext(filename)
    clean_name = slugify(name)
    final_filename = f"{clean_name}{ext}"
    return f'videos/c{curso_id}/m{modulo_id}/a{aula_id}/{final_filename}'

class BlocoVideo(models.Model):
    lesson = models.ForeignKey(Lesson, related_name='blocos', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    video = models.FileField(upload_to=bloco_video_path, max_length=500)
    order = models.PositiveIntegerField(default=0, help_text="Ordem do bloco na aula")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


# Material Complementar (Vinculado à Aula)
class Attachment(models.Model):
    lesson = models.ForeignKey(Lesson, related_name='attachments', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    # Trocamos o texto fixo pela função dinâmica que criamos acima
    file = models.FileField(upload_to=attachment_path, max_length=500)

    def __str__(self):
        return f"Anexo: {self.title} ({self.lesson.title})"   
    
# Tabela para rastrear o progresso e anotações da Aula (geral do aluno)
class UserLessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    liked = models.BooleanField(default=False)
    # Mantendo video_time caso precise, mas futuramente focado em Bloco

    class Meta:
        # Garante que só exista 1 registro de progresso por usuário para cada aula
        unique_together = ('user', 'lesson')

    def __str__(self):
        return f"Progresso de {self.user.username} na aula {self.lesson.title}"

# Progresso focado nos Blocos de Vídeo individualmente
class UserBlocoProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bloco = models.ForeignKey(BlocoVideo, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    video_time = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('user', 'bloco')

    def __str__(self):
        return f"Progresso Bloco {self.bloco.title} - {self.user.username}"

# Tabela para rastrear histórico de anotações (versionamento)
class UserNotesHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Anotação de {self.user.username} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

# Histórico de visualização de aulas assistidas
class HistoricoVideo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='historico')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    data_visualizacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_visualizacao']

    def __str__(self):
        return f"{self.user.username} assistiu {self.lesson.title} em {self.data_visualizacao.strftime('%d/%m/%Y %H:%M')}"