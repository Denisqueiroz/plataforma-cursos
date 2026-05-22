document.addEventListener("DOMContentLoaded", function () {
    function showToast(msg, bg = "#0d6efd") {
        if (typeof Toastify !== 'undefined') {
            Toastify({
                text: msg, duration: 3000, close: true, gravity: "bottom", position: "right",
                style: { background: bg, borderRadius: "8px", fontFamily: "'Inter', sans-serif" }
            }).showToast();
        } else {
            console.log("TOAST:", msg);
        }
    }

    const masterVideo = document.getElementById('master-video');
    const videoPlaceholder = document.getElementById('video-placeholder');
    let player = null;

    try {
        if (masterVideo) {
            player = new Plyr(masterVideo, {
                controls: ['play-large', 'rewind', 'play', 'fast-forward', 'progress', 'current-time', 'mute', 'volume', 'captions', 'settings', 'pip', 'airplay', 'fullscreen'],
                settings: ['captions', 'quality', 'speed'],
                speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] },
                seekTime: 10,
            });
        }
    } catch (err) {
        console.error("Plyr error:", err);
    }

    // Toggle Ementa
    const btnToggleEmenta = document.getElementById('btn-toggle-ementa');
    const btnToggleEmentaNav = document.getElementById('btn-toggle-ementa-nav');
    const sidebarEmenta = document.getElementById('sidebar-ementa');
    const colunaVideo = document.getElementById('coluna-video');

    function toggleEmenta() {
        if (sidebarEmenta && colunaVideo) {
            const isHidden = sidebarEmenta.classList.contains('d-none');

            if (isHidden) {
                // Mostrar a ementa novamente
                sidebarEmenta.classList.remove('d-none');

                // Volta o vídeo para col-lg-6
                colunaVideo.classList.remove('col-lg-9');
                colunaVideo.classList.add('col-lg-6');
            } else {
                // Ocultar a ementa
                sidebarEmenta.classList.add('d-none');

                // Expande o vídeo para col-lg-9
                colunaVideo.classList.remove('col-lg-6');
                colunaVideo.classList.add('col-lg-9');
            }

            // Atualiza os ícones
            const icons = document.querySelectorAll('.toggle-ementa-icon');
            icons.forEach(icon => {
                if (isHidden) {
                    icon.classList.replace('bi-layout-sidebar', 'bi-layout-sidebar-inset');
                } else {
                    icon.classList.replace('bi-layout-sidebar-inset', 'bi-layout-sidebar');
                }
            });

            // Dispara resize para que o player de vídeo (Plyr) se ajuste
            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
            }, 50);
        }
    }

    if (btnToggleEmenta) btnToggleEmenta.addEventListener('click', toggleEmenta);
    if (btnToggleEmentaNav) btnToggleEmentaNav.addEventListener('click', toggleEmenta);

    // Clicar numa aula
    document.querySelectorAll('.bloco-link').forEach((item, index) => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const url = item.dataset.videoUrl;

            if (!url) {
                console.error("Nenhuma URL de vídeo encontrada para este bloco.");
                showToast("Erro: Arquivo do vídeo ausente.", "#dc3545");
                return;
            }

            // Styling visual para clique ativo
            document.querySelectorAll('.bloco-link').forEach(el => {
                el.style.color = '#555';
                el.style.background = 'transparent';
            });
            item.style.color = '#0d6efd';
            item.style.background = '#eef2ff';

            // Atualização de Informação Visual
            document.getElementById('breadcrumb-modulo').innerText = item.dataset.moduloTitle || '';
            document.getElementById('current-lesson-title').innerText = item.dataset.lessonTitle || '';
            document.getElementById('current-bloco-title').innerText = "Assistindo: " + (item.dataset.blocoTitle || '');

            // Atualizar Anotações e Materiais
            const lessonId = item.dataset.lessonId;
            if (lessonId) {
                const poolData = document.getElementById(`attachments-data-${lessonId}`);
                if (poolData) {
                    // Carregar HTML de materiais
                    const attachmentsList = document.getElementById('attachments-list');
                    const clonedContent = poolData.cloneNode(true);
                    const rawNotesDiv = clonedContent.querySelector('.raw-notes');
                    if (rawNotesDiv) rawNotesDiv.remove();

                    if (clonedContent.innerHTML.trim() !== '') {
                        attachmentsList.innerHTML = clonedContent.innerHTML;
                    } else {
                        attachmentsList.innerHTML = '<p class="text-muted small">Nenhum material anexado.</p>';
                    }

                    // Carregar Anotações na barra lateral
                    const rawNotesDivOriginal = poolData.querySelector('.raw-notes');
                    const notesTextarea = document.getElementById('lesson-notes-textarea');
                    const btnSaveNotes = document.getElementById('btn-save-notes');

                    notesTextarea.value = rawNotesDivOriginal ? rawNotesDivOriginal.textContent : "";
                    notesTextarea.disabled = false;
                    notesTextarea.placeholder = "Escreva suas anotações aqui...";
                    notesTextarea.dataset.activeLesson = lessonId;
                    btnSaveNotes.disabled = false;
                }
            }

            // ==========================================
            // SOLUÇÃO DEFINITIVA (A MARRETA)
            // ==========================================
            if (videoPlaceholder) {
                videoPlaceholder.remove(); // Remove o elemento completamente do HTML!
            }
            
            // Deixa o Plyr assumir o controle total do espaço
            const plyrContainer = document.querySelector('.plyr');
            if (plyrContainer) {
                plyrContainer.style.display = 'block';
                plyrContainer.style.width = '100%';
                plyrContainer.style.height = '100%';
                plyrContainer.style.opacity = '1';
                plyrContainer.style.zIndex = '10';
            }
            // ==========================================

            // Injeção de vídeo
            if (player) {
                try {
                    player.source = {
                        type: 'video',
                        sources: [{ src: url, type: 'video/mp4' }]
                    };
                    player.play().catch(err => console.error('Play prevented:', err));
                } catch (err) {
                    console.error("Erro ao configurar player.source:", err);
                }
            }
        });
    });

    // Lógica de Navegação (Aula Anterior / Próxima Aula)
    let currentBlocoIndex = -1;
    const blocosLinks = Array.from(document.querySelectorAll('.bloco-link'));

    document.querySelectorAll('.bloco-link').forEach((item, index) => {
        item.addEventListener('click', () => {
            currentBlocoIndex = index;
        });
    });

    function navigateBloco(direction) {
        if (currentBlocoIndex === -1 && blocosLinks.length > 0) {
            currentBlocoIndex = 0;
            direction = 0;
        }

        const targetIndex = currentBlocoIndex + direction;

        if (targetIndex >= 0 && targetIndex < blocosLinks.length) {
            const targetBloco = blocosLinks[targetIndex];

            let currentElement = targetBloco;
            while (currentElement) {
                if (currentElement.classList && currentElement.classList.contains('collapse')) {
                    if (!currentElement.classList.contains('show')) {
                        if (typeof bootstrap !== 'undefined') {
                            bootstrap.Collapse.getOrCreateInstance(currentElement).show();
                        } else {
                            currentElement.classList.add('show');
                        }
                    }
                }
                currentElement = currentElement.parentElement;
            }

            targetBloco.click();
            setTimeout(() => {
                targetBloco.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 300);

        } else {
            showToast(direction > 0 ? "Você já concluiu a última aula." : "Você já está na primeira aula.", direction > 0 ? "#198754" : "#ffc107");
        }
    }

    const btnAnterior = document.getElementById('btn-aula-anterior');
    const btnProximo = document.getElementById('btn-prox-aula');

    if (btnAnterior) btnAnterior.addEventListener('click', () => navigateBloco(-1));
    if (btnProximo) btnProximo.addEventListener('click', () => navigateBloco(1));

    // Lógica para Salvar Anotações
    const btnSaveNotes = document.getElementById('btn-save-notes');
    const notesTextarea = document.getElementById('lesson-notes-textarea');

    if (btnSaveNotes) {
        btnSaveNotes.addEventListener('click', (e) => {
            e.preventDefault();

            const lessonId = notesTextarea.dataset.activeLesson;
            if (!lessonId) return;

            btnSaveNotes.disabled = true;
            const originalText = btnSaveNotes.innerText;
            btnSaveNotes.innerText = "Salvando...";

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const payload = {
                notes: notesTextarea.value
            };

            fetch(`/plataforma/painel/aula/${lessonId}/progresso/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(payload)
            })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        showToast("Anotação salva com sucesso!", "#198754");

                        const poolData = document.getElementById(`attachments-data-${lessonId}`);
                        if (poolData) {
                            let rawNotesDiv = poolData.querySelector('.raw-notes');
                            if (rawNotesDiv) {
                                rawNotesDiv.textContent = notesTextarea.value;
                            }
                        }
                    } else {
                        showToast("Erro ao salvar anotação.", "#dc3545");
                    }
                })
                .catch(err => {
                    console.error("Erro no salvamento das notas:", err);
                    showToast("Erro de conexão.", "#dc3545");
                })
                .finally(() => {
                    btnSaveNotes.innerText = "Salvo!";
                    setTimeout(() => {
                        btnSaveNotes.innerText = originalText;
                        btnSaveNotes.disabled = false;
                    }, 2000);
                });
        });
    }

    // Modo Cinema (Apagar a Luz)
    const btnLuz = document.getElementById('btn-apagar-luz');
    if (btnLuz) {
        btnLuz.addEventListener('click', () => {
            document.body.classList.toggle('cinema-mode');
            if (document.body.classList.contains('cinema-mode')) {
                btnLuz.innerHTML = '<i class="bi bi-lightbulb-fill"></i> Acender a Luz';
                btnLuz.classList.replace('btn-dark', 'btn-light');
            } else {
                btnLuz.innerHTML = '<i class="bi bi-lightbulb"></i> Apagar a Luz';
                btnLuz.classList.replace('btn-light', 'btn-dark');
            }
        });
    }
});