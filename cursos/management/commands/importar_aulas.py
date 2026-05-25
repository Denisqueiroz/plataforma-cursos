import os
import paramiko
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from cursos.models import Course, Modulo, Lesson, BlocoVideo, Attachment
from tqdm import tqdm

load_dotenv()

class Command(BaseCommand):
    help = 'Importa estrutura exata: Pasta -> Modulo | Subpasta -> Bloco | Arquivos -> Aula'

    def sftp_mkdir_p(self, sftp, remote_directory):
        """Cria pastas no servidor, corrigindo barras do Windows e tratando permissões."""
        remote_directory = remote_directory.replace('\\', '/')
        dirs = remote_directory.split('/')
        
        path = ''
        for dir_name in dirs:
            if not dir_name: 
                path = '/'
                continue
                
            path = f"{path}/{dir_name}" if path != '/' else f"/{dir_name}"
            
            try:
                sftp.stat(path)
            except IOError:
                try:
                    sftp.mkdir(path)
                except IOError as e:
                    print(f"\n[ERRO DE PERMISSÃO] O Linux bloqueou a criação da pasta '{path}'. Rode o comando chown no servidor.")
                    raise e

    def handle(self, *args, **options):
        SSH_HOST       = os.getenv('SSH_HOST')
        SSH_PORT       = int(os.getenv('SSH_PORT', '22'))
        SSH_USER       = os.getenv('SSH_USER')
        SSH_PASSWORD   = os.getenv('SSH_PASSWORD')
        SSH_MEDIA_ROOT = os.getenv('SSH_MEDIA_ROOT', '/media/meu_hd/plata_cursos/media')
        ORIGEM         = os.getenv('ORIGEM_VIDEOS', r'D:\Curso da Camila')
        
        # Pasta onde os vídeos brutos estão guardados no servidor
        PASTA_BRUTA_SERVIDOR = "/media/meu_hd/Curso_Camila"

        try:
            curso = Course.objects.get(title='ANALISTA (TRIBUNAIS) - 2025')
        except Course.DoesNotExist:
            self.stdout.write(self.style.ERROR("Curso não encontrado."))
            return

        self.stdout.write("Conectando ao servidor SSH...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sftp = None

        try:
            ssh.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASSWORD, timeout=15)
            sftp = ssh.open_sftp()
            
            modulo_idx = 1
            for modulo_dir in sorted(os.listdir(ORIGEM)):
                if modulo_dir.startswith('.'): continue
                path_modulo = os.path.join(ORIGEM, modulo_dir)
                if not os.path.isdir(path_modulo): continue

                # 1. Cria o Módulo (Ex: DIREITO ADMINISTRATIVO)
                modulo, _ = Modulo.objects.get_or_create(title=modulo_dir, course=curso, defaults={'order': modulo_idx})
                self.stdout.write(self.style.SUCCESS(f"\n[+] Módulo Criado: {modulo_dir}"))
                modulo_idx += 1

                bloco_idx = 1
                for bloco_dir in sorted(os.listdir(path_modulo)):
                    if bloco_dir.startswith('.'): continue
                    path_bloco = os.path.join(path_modulo, bloco_dir)
                    if not os.path.isdir(path_bloco): continue

                    # 2. Converte "Aula-01" para "Bloco-01"
                    titulo_bloco = bloco_dir.replace("Aula", "Bloco") if "Aula" in bloco_dir else bloco_dir
                    aula_lesson, _ = Lesson.objects.get_or_create(modulo=modulo, title=titulo_bloco, defaults={'order': bloco_idx})
                    self.stdout.write(f"  [-] Bloco Criado: {titulo_bloco}")
                    bloco_idx += 1

                    arquivos = sorted(os.listdir(path_bloco))
                    video_idx = 1

                    for arquivo in arquivos:
                        if arquivo.startswith('.'): continue
                        full_path = os.path.join(path_bloco, arquivo)
                        if not os.path.isfile(full_path): continue
                        file_size = os.path.getsize(full_path)

                        # --- PROCESSA VÍDEOS ---
                        if arquivo.lower().endswith(('.mp4', '.mkv')):
                            # 3. Transforma o nome longo em "Aula-01", "Aula-02" (idêntico ao seu print)
                            nome_amigavel = f"Aula-{video_idx:02d}"
                            db_video_path = f"videos/c{curso.id}/m{modulo.id}/a{aula_lesson.id}/{slugify(nome_amigavel)}.mp4"
                            
                            remote_video_path = f"{SSH_MEDIA_ROOT}/{db_video_path}".replace('\\', '/')
                            self.sftp_mkdir_p(sftp, remote_video_path.rsplit('/', 1)[0])

                            precisa_upload = True
                            try:
                                sftp.stat(remote_video_path)
                                precisa_upload = False
                            except IOError:
                                pass 

                            if precisa_upload:
                                # Magia do HD: Move da pasta velha para a nova estruturada instantaneamente
                                old_server_path = f"{PASTA_BRUTA_SERVIDOR}/{modulo_dir}/{bloco_dir}/{arquivo}".replace('\\', '/')
                                try:
                                    sftp.stat(old_server_path)
                                    sftp.rename(old_server_path, remote_video_path)
                                    self.stdout.write(self.style.SUCCESS(f"      [MOVIDO NO HD] {nome_amigavel}.mp4"))
                                    precisa_upload = False
                                except IOError:
                                    pass 

                            if precisa_upload:
                                try:
                                    with tqdm(total=file_size, unit='B', unit_scale=True, desc=f"      Enviando {nome_amigavel}") as pbar:
                                        def cb(t, total): pbar.update(t - pbar.n)
                                        sftp.put(full_path, remote_video_path, callback=cb)
                                except Exception as e:
                                    self.stdout.write(self.style.ERROR(f"      ✗ Erro: {e}"))
                                    video_idx += 1 
                                    continue 

                            BlocoVideo.objects.get_or_create(lesson=aula_lesson, title=nome_amigavel, defaults={'video': db_video_path, 'order': video_idx})
                            video_idx += 1

                        # --- PROCESSA PDFs ---
                        elif arquivo.lower().endswith('.pdf'):
                            name, ext = os.path.splitext(arquivo)
                            db_pdf_path = f"anexos/c{curso.id}/m{modulo.id}/a{aula_lesson.id}/{slugify(name)}{ext}"
                            
                            remote_pdf_path = f"{SSH_MEDIA_ROOT}/{db_pdf_path}".replace('\\', '/')
                            self.sftp_mkdir_p(sftp, remote_pdf_path.rsplit('/', 1)[0])

                            precisa_upload = True
                            try:
                                sftp.stat(remote_pdf_path)
                                precisa_upload = False
                            except IOError:
                                pass

                            if precisa_upload:
                                old_server_pdf_path = f"{PASTA_BRUTA_SERVIDOR}/{modulo_dir}/{bloco_dir}/{arquivo}".replace('\\', '/')
                                try:
                                    sftp.stat(old_server_pdf_path)
                                    sftp.rename(old_server_pdf_path, remote_pdf_path)
                                    self.stdout.write(self.style.SUCCESS(f"      [MOVIDO NO HD] PDF {arquivo}"))
                                    precisa_upload = False
                                except IOError:
                                    pass

                            if precisa_upload:
                                try:
                                    with tqdm(total=file_size, unit='B', unit_scale=True, desc=f"      Enviando PDF") as pbar:
                                        def cb_pdf(t, total): pbar.update(t - pbar.n)
                                        sftp.put(full_path, remote_pdf_path, callback=cb_pdf)
                                except Exception:
                                    continue

                            Attachment.objects.get_or_create(lesson=aula_lesson, title=arquivo, defaults={'file': db_pdf_path})

            self.stdout.write(self.style.SUCCESS('\nImportação concluída! Tudo organizado e tocando perfeitamente.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro geral: {e}"))
        finally:
            if sftp: sftp.close()
            if ssh: ssh.close()