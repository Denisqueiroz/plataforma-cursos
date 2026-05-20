import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.utils.text import slugify

# BIBLIOTECA VISUAL: Importa as ferramentas que desenham as barras, a velocidade e o tempo restante no terminal
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

# SEUS MODELOS: Importa as tabelas do banco de dados do seu SaaS de Cursos
from cursos.models import Course, Modulo, Lesson, BlocoVideo, Attachment

class Command(BaseCommand):
    help = 'Varre as pastas e realiza a importação vinculando os vídeos a um curso existente por ID.'

    def add_arguments(self, parser):
        # ARGUMENTO 1: Captura o número do ID do curso (Ex: 1) digitado no terminal
        parser.add_argument('curso_id', type=int, help='ID do curso existente no banco de dados')
        # ARGUMENTO 2: Captura o texto do caminho da pasta do HD (Ex: "/media/meu_hd/Curso_Camila")
        parser.add_argument('caminho_origem', type=str, help='Caminho completo da pasta do curso')

    def handle(self, *args, **options):
        # Pega os valores que você digitou e guarda em variáveis fáceis de usar
        curso_id = options['curso_id']
        caminho_origem = options['caminho_origem']

        # SEGURANÇA: Confere se a pasta que você digitou realmente existe no HD do Linux
        if not os.path.exists(caminho_origem):
            self.stdout.write(self.style.ERROR(f'O caminho mapeado não foi encontrado: {caminho_origem}'))
            return

        # SEGURANÇA DO BANCO: Tenta achar o Curso pelo ID digitado. Se não achar, o script para de forma amigável
        try:
            curso = Course.objects.get(id=curso_id)
        except Course.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Não foi encontrado nenhum curso com o ID: {curso_id}'))
            return
        
        # Exibe na tela qual é o curso real que ele localizou no banco
        self.stdout.write(self.style.SUCCESS(f'📚 Vinculando ao Curso Existente: {curso.title} (ID: {curso.id})'))

        # ==============================================================================
        # PASSO 1: MAPEAMENTO PRÉVIO (Varrer e Contar para a Barra Geral saber o 100%)
        # ==============================================================================
        total_arquivos_curso = 0  # Contador simples para somar todos os .mp4 e .pdf do curso todo
        lista_tarefas = []        # Uma lista na memória que vai guardar o "mapa" de cada arquivo achado

        # Nível 1: Entra e lista as pastas de matérias (Módulos) ordenadas alfabeticamente
        for index_mod, modulo_nome in enumerate(sorted(os.listdir(caminho_origem)), start=1):
            caminho_modulo = os.path.join(caminho_origem, modulo_nome)
            if not os.path.isdir(caminho_modulo): continue # Se não for pasta, ignora e vai pro próximo

            # Nível 2: Entra e lista as subpastas de aulas (Ex: Aula-01, Aula-02)
            for aula_nome in sorted(os.listdir(caminho_modulo)):
                caminho_aula = os.path.join(caminho_modulo, aula_nome)
                if not os.path.isdir(caminho_aula): continue # Se não for pasta, ignora e vai pro próximo

                # Nível 3: Entra na pasta da aula e lê os arquivos de vídeo ou PDF soltos lá dentro
                arquivos = os.listdir(caminho_aula)
                for arq in sorted(arquivos):
                    # Só conta e aceita se o arquivo terminar com a extensão .mp4 ou .pdf
                    if arq.lower().endswith('.mp4') or arq.lower().endswith('.pdf'):
                        total_arquivos_curso += 1 # Aumenta 1 na contagem total
                        
                        # Guarda todas as pistas de onde esse arquivo está para ser usado no Passo 3
                        lista_tarefas.append({
                            'modulo_nome': modulo_nome,
                            'index_mod': index_mod,
                            'aula_nome': aula_nome,
                            'caminho_aula': caminho_aula,
                            'arquivo': arq
                        })

        # Alerta se você rodar o comando em uma pasta que não tem vídeos organizados dentro
        if total_arquivos_curso == 0:
            self.stdout.write(self.style.WARNING("Nenhum arquivo de vídeo ou PDF encontrado para importar."))
            return

        # ==============================================================================
        # PASSO 2: CONFIGURAR AS DUAS BARRAS DE PROGRESSO SIMULTÂNEAS
        # ==============================================================================
        # O bloco 'with' ativa a biblioteca RICH e desenha as colunas visuais no console
        with Progress(
            SpinnerColumn(), # Desenha o ícone animado de "carregando"
            TextColumn("[progress.description]{task.description}"), # Mostra o texto descritivo da linha
            BarColumn(bar_width=40), # Desenha a barra física preenchendo com "===>"
            DownloadColumn(),        # Exibe os megabytes (Ex: 45MB / 150MB)
            TransferSpeedColumn(),   # Exibe a velocidade em tempo real (Ex: 15.4 MB/s)
            TimeRemainingColumn(),   # Exibe a estimativa de tempo que falta (Ex: ETA 00:12)
        ) as progress:

            # BARRA 1: Progresso Geral (Baseado no total de arquivos que contamos no Passo 1)
            tarefa_geral = progress.add_task(
                description="[bold cyan]Progresso Total do Curso[/]", 
                total=total_arquivos_curso
            )

            # BARRA 2: Arquivo Individual (Inicia oculta e calcula dinamicamente em BYTES)
            tarefa_arquivo = progress.add_task(
                description="[bold yellow]Aguardando arquivo...   [/]", 
                total=100, 
                visible=False # Fica invisível até que um vídeo pesado comece a subir
            )

            # Dicionário de controle de memória para organizar a numeração dos blocos de vídeo de cada aula
            controle_blocos_aula = {}

            # ==============================================================================
            # PASSO 3: LAÇO PRINCIPAL DE IMPORTAÇÃO (Salvar de verdade no banco e no HD)
            # ==============================================================================
            for tarefa in lista_tarefas:
                
                # BANCO DE DADOS (Módulo): Se a matéria não existir no curso, cria. Se já existir, apenas localiza
                modulo, _ = Modulo.objects.get_or_create(
                    course=curso, # Vincula diretamente ao seu curso fixo (Ex: ID 1)
                    title=tarefa['modulo_nome'].upper(), # Salva o nome da matéria sempre em MAIÚSCULO
                    defaults={'order': tarefa['index_mod']} # Define a ordem de exibição da matéria
                )

                # TRATAMENTO DO NOME DA AULA: Tenta extrair o número do final do nome da pasta (Ex: "Aula-03" vira 3)
                try:
                    ordem_aula = int(tarefa['aula_nome'].split('-')[-1])
                except ValueError:
                    ordem_aula = 0 # Se a pasta não tiver número separado por hífen, define a ordem como zero

                # Limpa o título da aula tirando hifens e deixando em maiúsculo (Ex: "Aula-01" vira "AULA 01")
                titulo_aula_limpo = tarefa['aula_nome'].replace('-', ' ').upper()
                
                # BANCO DE DADOS (Aula): Localiza ou cria a aula atrelada ao módulo atual
                aula, _ = Lesson.objects.get_or_create(
                    modulo=modulo, 
                    title=titulo_aula_limpo,
                    defaults={'order': ordem_aula}
                )

                # CONTROLE DOS BLOCOS: Se for o primeiro arquivo que mexemos nessa aula, descobre qual número de bloco está livre
                if aula.id not in controle_blocos_aula:
                    proximo_bloco = BlocoVideo.objects.filter(lesson=aula).count() + 1
                    controle_blocos_aula[aula.id] = proximo_bloco

                # Captura o caminho físico exato do arquivo e lê o tamanho dele em Bytes no disco
                caminho_completo = os.path.join(tarefa['caminho_aula'], tarefa['arquivo'])
                tamanho_bytes = os.path.getsize(caminho_completo)

                # --- CLASSE INTERCEPTADORA "ESPIÃ" ---
                # Essa classe herda o gerenciador de arquivos do Django. Ela serve para interceptar a cópia:
                # Toda vez que o Django lê um pedaço do vídeo para salvar na pasta final, o método 'read'
                # avisa a barra de progresso individual inferior ('tarefa_arquivo') para andar os bytes correspondentes.
                class ProgressFile(File):
                    def __init__(self, file, progress_instance, task_id):
                        super().__init__(file)
                        self._progress = progress_instance
                        self._task_id = task_id
                    def read(self, *args, **kwargs):
                        data = super().read(*args, **kwargs)
                        # Faz a barra do vídeo andar a quantidade exata de dados que acabou de ser copiada
                        self._progress.update(self._task_id, advance=len(data))
                        return data

                # ----------------------------------------------------------------------
                # CASO SEJA UM ARQUIVO DE VÍDEO (.mp4)
                # ----------------------------------------------------------------------
                if tarefa['arquivo'].lower().endswith('.mp4'):
                    indice_bloco = controle_blocos_aula[aula.id]
                    titulo_bloco = f"Bloco {indice_bloco}"

                    # Evita reprocessar ou duplicar vídeos que já foram enviados com sucesso antes
                    if not BlocoVideo.objects.filter(lesson=aula, order=indice_bloco).exists():
                        # Torna a barra inferior visível, zera ela e define o tamanho real do vídeo atual em Bytes
                        progress.update(tarefa_arquivo, description=f"[green]Enviando {tarefa['arquivo'][:20]}...[/]", total=tamanho_bytes, completed=0, visible=True)
                        
                        # Abre o arquivo de vídeo original do seu HD externo em modo de leitura binária ('rb')
                        with open(caminho_completo, 'rb') as vf:
                            novo_bloco = BlocoVideo(lesson=aula, title=titulo_bloco, order=indice_bloco)
                            # Salva o arquivo passando pela nossa classe ProgressFile para fazer a barra se mover na tela
                            novo_bloco.video.save(tarefa['arquivo'], ProgressFile(vf, progress, tarefa_arquivo), save=True)
                    
                    # Soma +1 para o próximo vídeo que for achado dentro dessa mesma aula virar o "Bloco 2"
                    controle_blocos_aula[aula.id] += 1

                # ----------------------------------------------------------------------
                # CASO SEJA UM ARQUIVO DE TEXTO (.pdf)
                # ----------------------------------------------------------------------
                elif tarefa['arquivo'].lower().endswith('.pdf'):
                    # Formata o título do anexo tirando a extensão e limpando hifens
                    titulo_anexo = tarefa['arquivo'].replace('.pdf', '').replace('-', ' ').strip().upper()

                    # Evita reprocessar ou duplicar anexos que já foram enviados antes
                    if not Attachment.objects.filter(lesson=aula, title=titulo_anexo).exists():
                        # Torna a barra inferior visível e adaptada para a cor magenta indicando envio de PDF
                        progress.update(tarefa_arquivo, description=f"[magenta]Enviando {tarefa['arquivo'][:20]}...[/]", total=tamanho_bytes, completed=0, visible=True)
                        
                        # Abre o arquivo PDF em modo de leitura binária ('rb')
                        with open(caminho_completo, 'rb') as pf:
                            novo_anexo = Attachment(lesson=aula, title=titulo_anexo)
                            # Salva o anexo alimentando a barra visual
                            novo_anexo.file.save(tarefa['arquivo'], ProgressFile(pf, progress, tarefa_arquivo), save=True)

                # Limpeza: Esconde a barra inferior do arquivo individual porque ele já terminou de subir
                progress.update(tarefa_arquivo, visible=False)
                # Avança 1 quadradinho na barra superior de Progresso Geral do Curso Completo
                progress.update(tarefa_geral, advance=1)

        # Imprime a mensagem de sucesso com cor verde nativa do Django fora do bloco de animações
        self.stdout.write(self.style.SUCCESS('\n🚀 --- Automação Concluída com Sucesso! ---'))