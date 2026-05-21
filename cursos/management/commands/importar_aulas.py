import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files import File
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

from cursos.models import Course, Modulo, Lesson, BlocoVideo, Attachment

class Command(BaseCommand):
    help = 'Varre as pastas e realiza a importação vinculando os vídeos a um curso existente por ID de forma otimizada.'

    def add_arguments(self, parser):
        parser.add_argument('curso_id', type=int, help='ID do curso existente no banco de dados')
        parser.add_argument('caminho_origem', type=str, help='Caminho completo da pasta do curso')

    def handle(self, *args, **options):
        curso_id = options['curso_id']
        caminho_origem = options['caminho_origem']

        if not os.path.exists(caminho_origem):
            self.stdout.write(self.style.ERROR(f'O caminho mapeado não foi encontrado: {caminho_origem}'))
            return

        try:
            curso = Course.objects.get(id=curso_id)
        except Course.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Não foi encontrado nenhum curso com o ID: {curso_id}'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'📚 Vinculando ao Curso Existente: {curso.title} (ID: {curso.id})'))

        # ==============================================================================
        # PASSO 1: MAPEAMENTO PRÉVIO (Rápido em memória)
        # ==============================================================================
        total_arquivos_curso = 0
        lista_tarefas = []

        for index_mod, modulo_nome in enumerate(sorted(os.listdir(caminho_origem)), start=1):
            caminho_modulo = os.path.join(caminho_origem, modulo_nome)
            if not os.path.isdir(caminho_modulo): continue

            for aula_nome in sorted(os.listdir(caminho_modulo)):
                caminho_aula = os.path.join(caminho_modulo, aula_nome)
                if not os.path.isdir(caminho_aula): continue

                arquivos = os.listdir(caminho_aula)
                for arq in sorted(arquivos):
                    if arq.lower().endswith('.mp4') or arq.lower().endswith('.pdf'):
                        total_arquivos_curso += 1
                        lista_tarefas.append({
                            'modulo_nome': modulo_nome,
                            'index_mod': index_mod,
                            'aula_nome': aula_nome,
                            'caminho_aula': caminho_aula,
                            'arquivo': arq
                        })

        if total_arquivos_curso == 0:
            self.stdout.write(self.style.WARNING("Nenhum arquivo de vídeo ou PDF encontrado para importar."))
            return

        # ==============================================================================
        # PASSO 2: CONFIGURAR AS BARRAS DE PROGRESSO
        # ==============================================================================
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        ) as progress:

            tarefa_geral = progress.add_task(
                description="[bold cyan]Progresso Total do Curso[/]", 
                total=total_arquivos_curso
            )

            tarefa_arquivo = progress.add_task(
                description="[bold yellow]Aguardando arquivo...   [/]", 
                total=100, 
                visible=False
            )

            # Memória cache para evitar ficar fazendo .count() no banco a todo momento
            controle_blocos_aula = {}

            # ==============================================================================
            # PASSO 3: LAÇO PRINCIPAL COM COPIA EM BLOCOS (CHUNKS) DE 4MB
            # ==============================================================================
            for tarefa in lista_tarefas:
                
                # MÓDULO: Busca ou cria
                modulo, _ = Modulo.objects.get_or_create(
                    course=curso,
                    title=tarefa['modulo_nome'].upper(),
                    defaults={'order': tarefa['index_mod']}
                )

                # TRATAMENTO DA AULA
                try:
                    ordem_aula = int(tarefa['aula_nome'].split('-')[-1])
                except ValueError:
                    ordem_aula = 0

                titulo_aula_limpo = tarefa['aula_nome'].replace('-', ' ').upper()
                
                aula, _ = Lesson.objects.get_or_create(
                    modulo=modulo, 
                    title=titulo_aula_limpo,
                    defaults={'order': ordem_aula}
                )

                # Inicializa o cache local de blocos se a aula for nova neste ciclo
                if aula.id not in controle_blocos_aula:
                    proximo_bloco = BlocoVideo.objects.filter(lesson=aula).count() + 1
                    controle_blocos_aula[aula.id] = proximo_bloco

                caminho_completo = os.path.join(tarefa['caminho_aula'], tarefa['arquivo'])
                tamanho_bytes = os.path.getsize(caminho_completo)

                # --- NOVA CLASSE ESPIÃ OTIMIZADA ---
                # Agora ela define e respeita blocos de 4MB (4194304 bytes)
                class OptimizedProgressFile(File):
                    def __init__(self, file, progress_instance, task_id):
                        super().__init__(file)
                        self._progress = progress_instance
                        self._task_id = task_id
                        # Força o Django a usar 4MB por leitura em vez do padrão pequeno dele
                        self.chunk_size = 4194304 

                    def read(self, *args, **kwargs):
                        data = super().read(*args, **kwargs)
                        if data:
                            self._progress.update(self._task_id, advance=len(data))
                        return data

                # ----------------------------------------------------------------------
                # PROCESSANDO VÍDEO (.mp4)
                # ----------------------------------------------------------------------
                if tarefa['arquivo'].lower().endswith('.mp4'):
                    indice_bloco = controle_blocos_aula[aula.id]
                    titulo_bloco = f"Bloco {indice_bloco}"

                    if not BlocoVideo.objects.filter(lesson=aula, order=indice_bloco).exists():
                        progress.update(tarefa_arquivo, description=f"[green]Enviando {tarefa['arquivo'][:20]}...[/]", total=tamanho_bytes, completed=0, visible=True)
                        
                        with open(caminho_completo, 'rb') as vf:
                            novo_bloco = BlocoVideo(lesson=aula, title=titulo_bloco, order=indice_bloco)
                            # Passamos a nossa classe com chunk_size injetado
                            novo_bloco.video.save(tarefa['arquivo'], OptimizedProgressFile(vf, progress, tarefa_arquivo), save=True)
                    
                    # Atualiza o contador local na memória (evita bater no banco no próximo bloco da mesma aula)
                    controle_blocos_aula[aula.id] += 1

                # ----------------------------------------------------------------------
                # PROCESSANDO ANEXO (.pdf)
                # ----------------------------------------------------------------------
                elif tarefa['arquivo'].lower().endswith('.pdf'):
                    titulo_anexo = tarefa['arquivo'].replace('.pdf', '').replace('-', ' ').strip().upper()

                    if not Attachment.objects.filter(lesson=aula, title=titulo_anexo).exists():
                        progress.update(tarefa_arquivo, description=f"[magenta]Enviando {tarefa['arquivo'][:20]}...[/]", total=tamanho_bytes, completed=0, visible=True)
                        
                        with open(caminho_completo, 'rb') as pf:
                            novo_anexo = Attachment(lesson=aula, title=titulo_anexo)
                            novo_anexo.file.save(tarefa['arquivo'], OptimizedProgressFile(pf, progress, tarefa_arquivo), save=True)

                progress.update(tarefa_arquivo, visible=False)
                progress.update(tarefa_geral, advance=1)

        self.stdout.write(self.style.SUCCESS('\n🚀 --- Automação Concluída com Sucesso! ---'))