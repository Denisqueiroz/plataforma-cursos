import os
import shutil
from django.conf import settings
from django.core.files import File
from cursos.models import Course, Modulo, Lesson, BlocoVideo, Attachment

# --- CONFIGURAÇÕES ---
# Pasta onde seus vídeos e PDFs estão agora (o "bagunçado")
BASE_ORIGEM = '/media/meu_hd/Curso_Camila' 

def rodar_automacao():
    # Busca o curso pelo título
    try:
        curso = Course.objects.get(title="ANALISTA (TRIBUNAIS) - 2025")
    except Course.DoesNotExist:
        print("Erro: Curso 'ANALISTA (TRIBUNAIS) - 2025' não encontrado no banco.")
        return

    # 1. Percorre Módulos
    for modulo_dir in sorted(os.listdir(BASE_ORIGEM)):
        modulo, _ = Modulo.objects.get_or_create(title=modulo_dir, course=curso)
        path_modulo = os.path.join(BASE_ORIGEM, modulo_dir)
        
        # 2. Percorre Blocos (Aulas)
        for bloco_dir in sorted(os.listdir(path_modulo)):
            path_bloco = os.path.join(path_modulo, bloco_dir)
            
            # Verifica se a Aula já existe para não duplicar
            aula, criada = Lesson.objects.get_or_create(modulo=modulo, title=bloco_dir)
            
            if not criada:
                print(f"Aula '{bloco_dir}' já cadastrada. Pulando...")
                continue
            
            # 3. Processa Arquivos
            arquivos = sorted(os.listdir(path_bloco))
            video_idx = 1
            
            for arquivo in arquivos:
                full_path = os.path.join(path_bloco, arquivo)
                
                # --- VÍDEOS (MOVER) ---
                if arquivo.lower().endswith(('.mp4', '.mkv')):
                    bloco = BlocoVideo(lesson=aula, title=f"Aula {video_idx:02d}", order=video_idx)
                    nome_novo = f"Aula-{video_idx:02d}.mp4"
                    
                    # Prepara o caminho final usando a lógica do seu model
                    bloco.video.save(nome_novo, File(open(full_path, 'rb')), save=False)
                    caminho_final = bloco.video.path
                    
                    # Cria a pasta de destino se não existir e move o arquivo
                    os.makedirs(os.path.dirname(caminho_final), exist_ok=True)
                    shutil.move(full_path, caminho_final)
                    
                    bloco.save()
                    print(f"Vídeo organizado: {nome_novo}")
                    video_idx += 1
                
                # --- PDFS (MOVER) ---
                elif arquivo.lower().endswith('.pdf'):
                    anexo = Attachment(lesson=aula, title=arquivo)
                    # Prepara caminho
                    anexo.file.save(arquivo, File(open(full_path, 'rb')), save=False)
                    caminho_final = anexo.file.path
                    
                    os.makedirs(os.path.dirname(caminho_final), exist_ok=True)
                    shutil.move(full_path, caminho_final)
                    
                    anexo.save()
                    print(f"PDF organizado: {arquivo}")

if __name__ == "__main__":
    rodar_automacao()