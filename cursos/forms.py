from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Course, User, Turma, Enrollment, Lesson, Attachment


class StudentCreationForm(UserCreationForm):
    class Meta:
        model = User
        # Removemos 'username' da lista de campos visíveis
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sobrenome'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seu@email.com'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        # O Django ainda exige um username internamente, 
        # então vamos salvar o e-mail como username automaticamente.
        user.username = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'image', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título do Curso'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descrição do Curso'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TurmaForm(forms.ModelForm):
    class Meta:
        model = Turma
        fields = ['name', 'description', 'courses']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da Turma'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição da Turma'}),
            'courses': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['user', 'turma']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'turma': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(is_active=True)
        self.fields['turma'].queryset = Turma.objects.all()


# ---------------------------------------------------------
# CORREÇÃO PARA MÚLTIPLOS ARQUIVOS (AULAS)
# ---------------------------------------------------------

import os
from django.core.exceptions import ValidationError

def validar_apenas_documentos(value):
    extensoes_proibidas = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv']
    ext = os.path.splitext(value.name)[1].lower()
    if ext in extensoes_proibidas:
        raise ValidationError(f'Arquivos de vídeo ({ext}) não são permitidos como materiais de apoio.')

# 1. A autorização para enviar múltiplos arquivos no HTML
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

# 2. A SOLUÇÃO: Campo customizado que aceita listas sem dar erro de validação
class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        if data:
            for f in data:
                if not isinstance(f, str):
                    validar_apenas_documentos(f)
        return data

# 3. O formulário usando a nossa nova regra
class LessonForm(forms.ModelForm):
    curso_selecionador = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        label="1. Selecione o Curso",
        widget=forms.Select(attrs={'class': 'form-select mb-3 shadow-none', 'id': 'courseSelect'}),
    )
    arquivos_extras = MultipleFileField(
        widget=MultipleFileInput(attrs={'multiple': True, 'class': 'form-control shadow-none', 'accept': '.pdf,.zip,.rar,.docx'}),
        required=False,
        label='Materiais de Apoio (Opcional, selecione PDFs/ZIPs)'
    )

    class Meta:
        model = Lesson
        fields = ['curso_selecionador', 'modulo', 'title', 'order', 'is_free']
        labels = {
            'modulo': '2. Selecione o Módulo',
            'title': 'Título da Aula',
            'order': 'Ordem',
            'is_free': 'Aula Gratuita (Demonstração)',
        }
        labels = {
            'modulo': 'Qual a Matéria (Módulo)?',
            'title': 'Tema Específico da Aula',
            'order': 'Ordem da Aula',
        }
        widgets = {
            'modulo': forms.Select(attrs={'class': 'form-select mb-3 shadow-none', 'id': 'moduloSelect'}),
            'title': forms.TextInput(attrs={'class': 'form-control form-control-lg mb-3 shadow-none', 'placeholder': 'Ex: AULA I - Princípios Fundamentais'}),
            'order': forms.NumberInput(attrs={'class': 'form-control mb-3 shadow-none'}),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-check-input fs-4'}),
        }

class BlocoVideoForm(forms.ModelForm):
    class Meta:
        from .models import BlocoVideo
        model = BlocoVideo
        fields = ['lesson', 'title', 'video', 'order']
        widgets = {
            'lesson': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Parte 1'}),
            'video': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ModuloForm(forms.ModelForm):
    class Meta:
        from .models import Modulo
        model = Modulo
        fields = ['course', 'title', 'order']
        labels = {
            'course': 'Curso Pertencente',
            'title': 'Nome da Matéria / Disciplina',
            'order': 'Ordem (numeral)',
        }
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select shadow-none'}),
            'title': forms.TextInput(attrs={'class': 'form-control shadow-none', 'placeholder': 'Ex: Direito Civil, Informática...'}),
            'order': forms.NumberInput(attrs={'class': 'form-control shadow-none', 'min': 0}),
        }