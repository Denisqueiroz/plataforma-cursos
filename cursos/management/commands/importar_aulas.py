import os
from django.conf import settings
from django.core.management.base import BaseCommand
from cursos.models import Course, Modulo, Lesson, BlocoVideo, Attachment

class Command(BaseCommand):
    help = 'Indexa arquivos locais no banco de dados.'

    def add_arguments(self, parser):
        parser.add_argument('curso_id', type=int)
        parser.add_argument('caminho_origem', type=str)

    def handle(self, *args, **options):
        curso = Course.objects.get(id=options['curso_id'])
        caminho_origem = options['caminho_origem']

        # O script percorre as pastas fisicamente presentes no seu Windows
        for modulo_nome in sorted(os.listdir(caminho_origem)):
            caminho_modulo = os.path.join(caminho_origem, modulo_nome)
            if not os.path.isdir(caminho_modulo): continue
            
            modulo, _ = Modulo.objects.get_or_create(course=curso, title=modulo_nome.upper())
            
            for aula_nome in sorted(os.listdir(caminho_modulo)):
                caminho_aula = os.path.join(caminho_modulo, aula_nome)
                if not os.path.isdir(caminho_aula): continue
                
                aula, _ = Lesson.objects.get_or_create(modulo=modulo, title=aula_nome.upper())
                
                for arq in sorted(os.listdir(caminho_aula)):
                    caminho_completo = os.path.join(caminho_aula, arq)
                    
                    # LOGICA IMPORTANTE: 
                    # Se você quer que funcione no Linux depois, salve o caminho 
                    # usando barras normais '/' e sem a letra da unidade (ex: C:)
                    nome_arquivo_relativo = f"Curso_Camila/{modulo_nome}/{aula_nome}/{arq}"
                    
                    if arq.lower().endswith('.mp4'):
                        if not BlocoVideo.objects.filter(lesson=aula, video=nome_arquivo_relativo).exists():
                            BlocoVideo.objects.create(lesson=aula, title=f"Video - {arq}", video=nome_arquivo_relativo)
                            self.stdout.write(f"✅ Indexado: {arq}")
                            
                    elif arq.lower().endswith('.pdf'):
                        if not Attachment.objects.filter(lesson=aula, file=nome_arquivo_relativo).exists():
                            Attachment.objects.create(lesson=aula, title=arq, file=nome_arquivo_relativo)
                            self.stdout.write(f"📄 Indexado: {arq}")

        self.stdout.write(self.style.SUCCESS('🚀 Indexação local concluída!'))