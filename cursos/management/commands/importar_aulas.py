import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.utils.text import slugify

# IMPORTAÇÕES DA BIBLIOTECA RICH: Componentes visuais para criar barras de progresso modernas
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

# Importações dos seus modelos do banco de dados do SaaS
from cursos.models import Course, Modulo, Lesson, BlocoVideo, Attachment

class Command(BaseCommand):
    help = 'Varre as pastas e realiza a importação mostrando o progresso do arquivo atual e o geral do curso.'

    def add_arguments(self, parser):
        # Define o único argumento necessário: o caminho da pasta no HD
        parser.add_argument('caminho_origem', type=str, help='Caminho completo da pasta do curso')

    def handle(self, *args, **options):
        caminho_origem = options['caminho_origem']

        # Segurança: Garante que o caminho digitado realmente existe no sistema
        if not os.path.exists(caminho_origem):
            self.stdout.write(self.style.ERROR(f'O caminho mapeado não foi encontrado: {caminho_origem}'))
            return

        # Captura o nome da pasta do curso (ex: "Curso da Camila")
        nome_curso_pasta = os.path.basename(os.path.normpath(caminho_origem))

        # Busca o curso ou cria no banco se não existir
        curso, criado = Course.objects.get_or_create(
            title=nome_curso_pasta,
            defaults={'description': f'Curso importado automaticamente de {nome_curso_pasta}'}
        )
        
        self.stdout.write(self.style.SUCCESS(f'📚 Curso mapeado: {curso.title} (ID: {curso.id})'))

        # ==============================================================================
        # PASSO 1: MAPEAMENTO PRÉVIO (Contagem total para a Barra Geral)
        # ==============================================================================
        # Antes de começar a salvar, precisamos ler todas as pastas para saber o TOTAL exato
        # de arquivos. Sem isso, não teríamos como dizer para a barra geral onde fica o "100%".
        total_arquivos_curso = 0
        lista_tarefas = [] # Armazenará um dicionário estruturado para cada arquivo encontrado

        for index_mod, modulo_nome in enumerate(sorted(os.listdir(caminho_origem)), start=1):
            caminho_modulo = os.path.join(caminho_origem, modulo_nome)
            if not os.path.isdir(caminho_modulo): continue

            for aula_nome in sorted(os.listdir(caminho_modulo)):
                caminho_aula = os.path.join(caminho_modulo, aula_nome)
                if not os.path.isdir(caminho_aula): continue

                arquivos = os.listdir(caminho_aula)
                for arq in sorted(arquivos):
                    # Se for um arquivo válido, incrementa o total e guarda os dados da pasta
                    if arq.lower().endswith('.mp4') or arq.lower().endswith('.pdf'):
                        total_arquivos_curso += 1
                        lista_tarefas.append({
                            'modulo_nome': modulo_nome,
                            'index_mod': index_mod,
                            'aula_nome': aula_nome,
                            'caminho_aula': caminho_aula,
                            'arquivo': arq
                        })

        # Se as pastas estiverem vazias, o script para aqui de forma amigável
        if total_arquivos_curso == 0:
            self.stdout.write(self.style.WARNING("Nenhum arquivo de vídeo ou PDF encontrado para importar."))
            return

        # ==============================================================================
        # PASSO 2: MONTAGEM DO PAINEL VISUAL (Duas Barras de Progresso)
        # ==============================================================================
        # O 'with Progress(...)' abre o gerenciador visual da biblioteca RICH e define
        # quais informações serão desenhadas na tela lado a lado (ícone de carregamento, 
        # barra física, tamanho baixado, velocidade atual e tempo estimado de término).
        with Progress(
            SpinnerColumn(),                                # Ícone animado giratório (loading)
            TextColumn("[progress.description]{task.description}"), # Texto descritivo da tarefa
            BarColumn(bar_width=40),                        # Desenho da barra de progresso física
            DownloadColumn(),                               # Mostra o progresso em dados (ex: 50MB / 200MB)
            TransferSpeedColumn(),                          # Mostra a velocidade real de gravação/rede (ex: 35 MB/s)
            TimeRemainingColumn(),                          # Mostra o tempo restante estimado (ETA: 00:03)
        ) as progress:

            # BARRA CRUCIAL 1: Progresso Geral do Curso (Calculado por quantidade de arquivos)
            tarefa_geral = progress.add_task(
                description="[bold cyan]Progresso Total do Curso[/]", 
                total=total_arquivos_curso
            )

            # BARRA CRUCIAL 2: Arquivo Atual (Calculado dinamicamente em Bytes durante a cópia)
            # Ela inicia oculta (visible=False) e ganha vida toda vez que um arquivo pesado começa a ser lido
            tarefa_arquivo = progress.add_task(
                description="[bold yellow]Aguardando arquivo...   [/]", 
                total=100, 
                visible=False
            )

            # Dicionário na memória para controlar as numerações dos Blocos (evita reiniciar o Bloco no arquivo errado)
            controle_blocos_aula = {}

            # ==============================================================================
            # PASSO 3: LAÇO PRINCIPAL DE IMPORTAÇÃO E ENVIO
            # ==============================================================================
            # Agora percorremos a lista de tarefas que mapeamos lá no Passo 1
            for tarefa in lista_tarefas:
                
                # Busca ou cria o Módulo baseado nos dados da pasta atual
                modulo, _ = Modulo.objects.get_or_create(
                    course=curso, 
                    title=tarefa['modulo_nome'].upper(),
                    defaults={'order': tarefa['index_mod']}
                )

                # Tenta extrair a numeração da aula do final do nome da pasta (ex: "Aula-05" -> 5)
                try:
                    ordem_aula = int(tarefa['aula_nome'].split('-')[-1])
                except ValueError:
                    ordem_aula = 0

                # Formata um título bonito removendo hifens e aplicando letras maiúsculas
                titulo_aula_limpo = tarefa['aula_nome'].replace('-', ' ').upper()
                
                # Busca ou cria a Aula atrelada ao módulo correspondente
                aula, _ = Lesson.objects.get_or_create(
                    modulo=modulo, 
                    title=titulo_aula_limpo,
                    defaults={'order': ordem_aula}
                )

                # Se for a primeira vez que entramos nessa aula, descobre qual o próximo número de Bloco livre
                if aula.id not in controle_blocos_aula:
                    proximo_bloco = BlocoVideo.objects.filter(lesson=aula).count() + 1
                    controle_blocos_aula[aula.id] = proximo_bloco

                caminho_completo = os.path.join(tarefa['caminho_aula'], tarefa['arquivo'])
                tamanho_bytes = os.path.getsize(caminho_completo) # Captura o tamanho exato do arquivo no HD em bytes

                # --- SUB-PASSO INTELIGENTE: INTERCEPTADOR DE BYTES ---
                # Esta classe herda as funções de arquivos do Django ('File'). Ela serve como um espião:
                # Toda vez que o Django ler um pedaço (chunk) do arquivo para salvar no HD/Nuvem, o método 
                # 'read' intercepta o tamanho desse pedaço lido e diz para a barra 'tarefa_arquivo' avançar!
                class ProgressFile(File):
                    def __init__(self, file, progress_instance, task_id):
                        super().__init__(file)
                        self._progress = progress_instance
                        self._task_id = task_id
                    def read(self, *args, **kwargs):
                        data = super().read(*args, **kwargs)
                        # Faz a barra individual do arquivo andar a quantidade exata de bytes que acabou de ler
                        self._progress.update(self._task_id, advance=len(data))
                        return data

                # ----------------------------------------------------------------------
                # TRATAMENTO DE VÍDEOS (.mp4)
                # ----------------------------------------------------------------------
                if tarefa['arquivo'].lower().endswith('.mp4'):
                    indice_bloco = controle_blocos_aula[aula.id]
                    titulo_bloco = f"Bloco {indice_bloco}"

                    # Evita o reprocessamento de vídeos que já foram enviados em execuções anteriores
                    if not BlocoVideo.objects.filter(lesson=aula, order=indice_bloco).exists():
                        # Configura e exibe a barra individual para o tamanho real deste vídeo em Bytes
                        progress.update(tarefa_arquivo, description=f"[green]Enviando {tarefa['arquivo'][:20]}...[/]", total=tamanho_bytes, completed=0, visible=True)
                        
                        # Abre o arquivo de vídeo local em modo binário de leitura ('rb')
                        with open(caminho_completo, 'rb') as vf:
                            novo_bloco = BlocoVideo(lesson=aula, title=titulo_bloco, order=indice_bloco)
                            # Salva o arquivo passando pelo nosso espião ProgressFile para alimentar a barra visual
                            novo_bloco.video.save(tarefa['arquivo'], ProgressFile(vf, progress, tarefa_arquivo), save=True)
                    
                    # Avança o marcador local para o próximo bloco de vídeo da mesma aula
                    controle_blocos_aula[aula.id] += 1

                # ----------------------------------------------------------------------
                # TRATAMENTO DE PDFs (.pdf)
                # ----------------------------------------------------------------------
                elif tarefa['arquivo'].lower().endswith('.pdf'):
                    titulo_anexo = tarefa['arquivo'].replace('.pdf', '').replace('-', ' ').strip().upper()

                    # Evita o reprocessamento de PDFs duplicados
                    if not Attachment.objects.filter(lesson=aula, title=titulo_anexo).exists():
                        # Configura e exibe a barra individual adaptada para o tamanho do PDF
                        progress.update(tarefa_arquivo, description=f"[magenta]Enviando {tarefa['arquivo'][:20]}...[/]", total=tamanho_bytes, completed=0, visible=True)
                        
                        with open(caminho_completo, 'rb') as pf:
                            novo_anexo = Attachment(lesson=aula, title=titulo_anexo)
                            novo_anexo.file.save(tarefa['arquivo'], ProgressFile(pf, progress, tarefa_arquivo), save=True)

                # Oculta a barra individual (já que o arquivo terminou de ser processado)
                progress.update(tarefa_arquivo, visible=False)
                # Faz a barra Geral do Curso avançar 1 passo na contagem total
                progress.update(tarefa_geral, advance=1)

        # Mensagem de sucesso final (renderizada fora do bloco de animações)
        self.stdout.write(self.style.SUCCESS('\n🚀 --- Automação Concluída com Sucesso! ---'))