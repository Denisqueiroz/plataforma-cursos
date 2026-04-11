from django.contrib import admin
from .models import Attachment, Lesson, User, Course, Turma, Enrollment

# Registrando nossos modelos no painel de administração
admin.site.register(User)
admin.site.register(Course)
admin.site.register(Turma)
admin.site.register(Enrollment)
admin.site.register(Lesson)      
admin.site.register(Attachment)  