from django.core.management.base import BaseCommand
import os
import shutil
from django.core.files import File
from cursos.models import Course, Modulo, Lesson, BlocoVideo, Attachment

class Command(BaseCommand):
    help = 'Importa aulas e vídeos automaticamente'

    def handle(self, *args, **options):
        BASE_ORIGEM = '/media/meu_hd/Curso_Camila'
        
        try:
            curso = Course.objects.get(title="ANALISTA (TRIBUNAIS) - 2025")
        except Course.DoesNotExist:
            self.stdout.write(self.style.ERROR("Erro: Curso não encontrado."))
            return

        for modulo_dir in sorted(os.listdir(BASE_ORIGEM)):
            modulo, _ = Modulo.objects.get_or_create(title=modulo_dir, course=curso)
            path_modulo = os.path.join(BASE_ORIGEM, modulo_dir)
            
            for bloco_dir in sorted(os.listdir(path_modulo)):
                path_bloco = os.path.join(path_modulo, bloco_dir)
                aula, criada = Lesson.objects.get_or_create(modulo=modulo, title=bloco_dir)
                
                if not criada:
                    self.stdout.write(f"Aula '{bloco_dir}' já cadastrada. Pulando...")
                    continue
                
                arquivos = sorted(os.listdir(path_bloco))
                video_idx = 1
                
                for arquivo in arquivos:
                    full_path = os.path.join(path_bloco, arquivo)
                    if arquivo.lower().endswith(('.mp4', '.mkv')):
                        bloco = BlocoVideo(lesson=aula, title=f"Aula {video_idx:02d}", order=video_idx)
                        nome_novo = f"Aula-{video_idx:02d}.mp4"
                        
                        with open(full_path, 'rb') as f:
                            bloco.video.save(nome_novo, File(f), save=False)
                            caminho_final = bloco.video.path
                            os.makedirs(os.path.dirname(caminho_final), exist_ok=True)
                            shutil.move(full_path, caminho_final)
                        bloco.save()
                        self.stdout.write(f"Vídeo organizado: {nome_novo}")
                        video_idx += 1
                    elif arquivo.lower().endswith('.pdf'):
                        anexo = Attachment(lesson=aula, title=arquivo)
                        with open(full_path, 'rb') as f:
                            anexo.file.save(arquivo, File(f), save=False)
                            caminho_final = anexo.file.path
                            os.makedirs(os.path.dirname(caminho_final), exist_ok=True)
                            shutil.move(full_path, caminho_final)
                        anexo.save()
                        self.stdout.write(f"PDF organizado: {arquivo}")
        self.stdout.write(self.style.SUCCESS("Importação concluída!"))
        # Fim do comando de importação (teste)