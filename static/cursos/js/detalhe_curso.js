// Scripts para detalhe_curso.html

document.addEventListener("DOMContentLoaded", function() {
    // Inicializar Plyr para todos os vídeos
    const players = Plyr.setup('.aula-video', {
        controls: ['play-large', 'play', 'progress', 'current-time', 'duration', 'mute', 'volume', 'settings', 'fullscreen'],
        settings: ['speed'],
        speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] },
        autoplay: false,
        clickToPlay: true,
        hideControls: true,
        resetOnEnd: false,
        disableContextMenu: false,
        loadSprite: true,
        iconPrefix: 'plyr',
        iconUrl: 'https://cdn.plyr.io/3.7.8/plyr.svg',
        blankVideo: 'https://cdn.plyr.io/static/blank.mp4',
        quality: { default: 576, options: [4320, 2880, 2160, 1440, 1080, 720, 576, 480, 360, 240] },
        loop: { active: false },
        storage: { enabled: true, key: 'plyr' },
        tooltips: { controls: false, seek: true },
        captions: { active: false, language: 'auto', update: false },
        fullscreen: { enabled: true, fallback: true, iosNative: false },
        ratio: '16:9',
        listeners: {
            seek: null,
            play: null,
            pause: null,
            restart: null,
            rewind: null,
            fastForward: null,
            mute: null,
            volume: null,
            captions: null,
            download: null,
            fullscreen: null,
            pip: null,
            airplay: null,
            speed: null,
            quality: null,
            loop: null,
            language: null
        },
        i18n: {
            restart: 'Reiniciar',
            rewind: 'Voltar {seektime}s',
            play: 'Reproduzir',
            pause: 'Pausar',
            fastForward: 'Avançar {seektime}s',
            seek: 'Buscar',
            seekLabel: '{currentTime} de {duration}',
            played: 'Reproduzido',
            buffered: 'Carregado',
            currentTime: 'Tempo atual',
            duration: 'Duração',
            volume: 'Volume',
            mute: 'Mudo',
            unmute: 'Ativar som',
            enableCaptions: 'Ativar legendas',
            disableCaptions: 'Desativar legendas',
            download: 'Download',
            enterFullscreen: 'Tela cheia',
            exitFullscreen: 'Sair da tela cheia',
            frameTitle: 'Player para {title}',
            captions: 'Legendas',
            settings: 'Configurações',
            pip: 'PiP',
            menuBack: 'Voltar ao menu anterior',
            speed: 'Velocidade',
            normal: 'Normal',
            quality: 'Qualidade',
            loop: 'Loop',
            start: 'Começar',
            end: 'Fim',
            all: 'Tudo',
            reset: 'Resetar',
            disabled: 'Desativado',
            enabled: 'Ativado',
            advertisement: 'Anúncio',
            qualityBadge: {
                2160: '4K',
                1440: 'HD',
                1080: 'HD',
                720: 'HD',
                576: 'SD',
                480: 'SD'
            }
        },
        urls: {
            download: null,
            vimeo: {
                sdk: 'https://player.vimeo.com/api/player.js',
                iframe: 'https://player.vimeo.com/video/{0}?{1}',
                api: 'https://vimeo.com/api/oembed.json?url={0}'
            },
            youtube: {
                sdk: 'https://www.youtube.com/iframe_api',
                api: 'https://noembed.com/embed?url=https://www.youtube.com/watch?v={0}'
            },
            googleIMA: {
                sdk: 'https://imasdk.googleapis.com/js/sdkloader/ima3.js'
            }
        },
        keys: {
            google: null
        },
        enabled: true
    });

    // Função para salvar progresso
    function salvarProgresso(lessonId, currentTime) {
        fetch(`/painel/aula/${lessonId}/progresso/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                video_time: currentTime
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Progresso salvo:', data);
        })
        .catch(error => {
            console.error('Erro ao salvar progresso:', error);
        });
    }

    // Adicionar eventos aos players
    players.forEach(player => {
        const videoElement = player.elements.container.querySelector('video');
        const lessonId = videoElement.dataset.lessonId;
        const savedTime = parseFloat(videoElement.dataset.savedTime) || 0;

        // Definir tempo salvo
        if (savedTime > 0) {
            player.currentTime = savedTime;
        }

        // Salvar progresso a cada 5 segundos durante reprodução
        let saveInterval;
        player.on('play', () => {
            saveInterval = setInterval(() => {
                salvarProgresso(lessonId, player.currentTime);
            }, 5000);
        });

        player.on('pause', () => {
            clearInterval(saveInterval);
            salvarProgresso(lessonId, player.currentTime);
        });

        player.on('ended', () => {
            clearInterval(saveInterval);
            salvarProgresso(lessonId, player.currentTime);
        });

        // Salvar ao mudar velocidade ou outras configurações
        player.on('ratechange', () => {
            salvarProgresso(lessonId, player.currentTime);
        });
    });

    // Navegação de abas
    document.querySelectorAll('[data-tab-target]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('[data-tab-target]').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-custom-content').forEach(c => c.classList.add('d-none'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.tabTarget).classList.remove('d-none');
        });
    });

    // Troca de aula
    document.querySelectorAll('.lesson-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const id = item.dataset.lessonId;
            // Pausar todos os vídeos
            players.forEach(p => p.pause());
            document.querySelectorAll('.lesson-pane, .lesson-item, .notes-wrapper').forEach(el => {
                el.classList.add('d-none');
                el.classList.remove('active-lesson');
            });
            document.getElementById(`lesson-pane-${id}`).classList.remove('d-none');
            document.getElementById(`notes-${id}`).classList.remove('d-none');
            item.classList.add('active-lesson');
            item.classList.remove('d-none');
        });
    });

    // Botão próxima aula
    document.querySelectorAll('.btn-next').forEach(btn => {
        btn.addEventListener('click', () => {
            const currentLesson = document.querySelector('.lesson-item.active-lesson');
            const nextLesson = currentLesson.nextElementSibling;
            if (nextLesson && nextLesson.classList.contains('lesson-item')) {
                nextLesson.click();
            }
        });
    });

    // Salvar anotações (se houver lógica adicional)
    document.querySelectorAll('.note-area').forEach(textarea => {
        textarea.addEventListener('input', () => {
            // Lógica para salvar anotações, se necessário
        });
    });
});