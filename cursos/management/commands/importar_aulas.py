import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify
# Importando os nomes exatos do seu models.py
from cursos.models import Course, Modulo, Lesson, BlocoVideo, Attachment

class Command(BaseCommand):
    help = 'Importa vídeos e PDFs organizados em pastas para o banco local'

    def add_arguments(self, parser):
        parser.add_argument('caminho_origem', type=str, help='Caminho da pasta CURSO_CAMILA')
        parser.add_argument('curso_id', type=int, help='ID do Course no sistema')

    def handle(self, *args, **options):
        caminho_origem = options['caminho_origem']
        curso_id = options['curso_id']

        try:
            curso = Course.objects.get(id=curso_id)
        except Course.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Curso com ID {curso_id} não encontrado.'))
            return

        # 1. Navega pelas pastas de Módulos (ex: DIREITO ADMINISTRATIVO)
        for modulo_nome in os.listdir(caminho_origem):
            caminho_modulo = os.path.join(caminho_origem, modulo_nome)
            if not os.path.isdir(caminho_modulo): continue

            # Cria o Modulo
            modulo, _ = Modulo.objects.get_or_create(course=curso, title=modulo_nome)
            self.stdout.write(f'Módulo: {modulo_nome}')

            # 2. Navega pelas pastas de Aulas (ex: Aula-01)
            for aula_nome in os.listdir(caminho_modulo):
                caminho_aula = os.path.join(caminho_modulo, aula_nome)
                if not os.path.isdir(caminho_aula): continue

                try:
                    ordem_aula = int(aula_nome.split('-')[-1])
                except:
                    ordem_aula = 0

                aula, _ = Lesson.objects.get_or_create(
                    modulo=modulo, 
                    title=aula_nome.replace('-', ' ').upper(),
                    defaults={'order': ordem_aula}
                )

                # 3. Processa arquivos dentro da aula
                arquivos = os.listdir(caminho_aula)
                
                # Filtra e ordena os vídeos para garantir a sequência Bloco 1, 2, 3...
                lista_videos = sorted([f for f in arquivos if f.endswith('.mp4')])
                
                for indice, arquivo_video in enumerate(lista_videos, start=1):
                    caminho_full = os.path.join(caminho_aula, arquivo_video)
                    
                    nome_limpo = slugify(os.path.splitext(arquivo_video)[0])
                    ext = os.path.splitext(arquivo_video)[1]
                    
                    # Caminho relativo para o banco (segue sua lógica de bloco_video_path)
                    caminho_db = f'videos/c{curso.id}/m{modulo.id}/a{aula.id}/{nome_limpo}{ext}'
                    destino_final = os.path.join(settings.MEDIA_ROOT, caminho_db)
                    
                    os.makedirs(os.path.dirname(destino_final), exist_ok=True)
                    shutil.copy(caminho_full, destino_final)

                    # Cria o BlocoVideo com título amigável "Bloco X"
                    BlocoVideo.objects.get_or_create(
                        lesson=aula, 
                        title=f"Bloco {indice}",
                        defaults={
                            'video': caminho_db,
                            'order': indice
                        }
                    )
                    self.stdout.write(f'   [Vídeo] {arquivo_video} -> Bloco {indice}')

                # 4. Processa PDFs
                for arquivo in arquivos:
                    if arquivo.endswith('.pdf'):
                        caminho_full = os.path.join(caminho_aula, arquivo)
                        nome_limpo = slugify(os.path.splitext(arquivo)[0])
                        ext = os.path.splitext(arquivo)[1]
                        
                        caminho_db = f'anexos/c{curso.id}/m{modulo.id}/a{aula.id}/{nome_limpo}{ext}'
                        destino_final = os.path.join(settings.MEDIA_ROOT, caminho_db)
                        
                        os.makedirs(os.path.dirname(destino_final), exist_ok=True)
                        shutil.copy(caminho_full, destino_final)

                        Attachment.objects.get_or_create(
                            lesson=aula,
                            title=arquivo.replace('.pdf', ''),
                            file=caminho_db
                        )
                        self.stdout.write(f'   [PDF] {arquivo} importado.')

        self.stdout.write(self.style.SUCCESS('--- Importação Concluída com Sucesso! ---'))