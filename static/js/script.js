document.addEventListener('DOMContentLoaded', function() {

    // --- ELEMENTOS GLOBAIS ---
    const formAgendamento = document.getElementById('form-agendamento');
    if (!formAgendamento) return; // Sai se não estiver na página de agendamento

    // --- ELEMENTOS DO SELETOR CUSTOMIZADO ---
    const customSelectWrapper = document.getElementById('custom-select-servico');
    const customSelectTrigger = customSelectWrapper.querySelector('.custom-select-trigger');
    const customOptionsContainer = customSelectWrapper.querySelector('.custom-options');
    const triggerText = customSelectTrigger.querySelector('span');
    
    // --- ELEMENTOS DO FORMULÁRIO E MODAL ---
    const selectServicoOriginal = document.getElementById('select-servico');
    const datepickerInput = document.getElementById('datepicker');
    const horariosContainer = document.getElementById('horarios-disponiveis');
    const horaSelecionadaInput = document.getElementById('hora-selecionada');
    const btnAgendar = document.getElementById('btn-agendar');
    const modal = document.getElementById('modal-feedback');
    const modalMessage = document.getElementById('feedback-message');
    const closeButton = modal ? modal.querySelector('.close-button') : null;

    // --- VARIÁVEL GLOBAL PARA FERIADOS ---
    let feriados = [];

    // --- FUNÇÕES AUXILIARES ---
    function mostrarModal(mensagem) {
        if (modal && modalMessage) {
            modalMessage.innerHTML = mensagem;
            modal.style.display = 'flex';
        } else {
            alert(mensagem.replace(/<br>/g, '\n').replace(/<b>/g, '').replace(/<\/b>/g, ''));
        }
    }

    function carregarHorarios(data) {
        const servicoId = selectServicoOriginal.value;
        if (!servicoId) {
            horariosContainer.innerHTML = '<p>Selecione um serviço para ver os horários.</p>';
            return;
        }
        horariosContainer.innerHTML = '<p>Carregando horários...</p>';
        fetch(`/api/horarios-disponiveis?data=${data}&servico_id=${servicoId}`)
            .then(response => response.json())
            .then(horarios => {
                horariosContainer.innerHTML = '';
                if (horarios.length === 0) {
                    horariosContainer.innerHTML = '<p>Nenhum horário disponível para este serviço nesta data.</p>';
                    return;
                }
                horarios.forEach(hora => {
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'horario-btn';
                    btn.textContent = hora;
                    btn.dataset.hora = hora;
                    horariosContainer.appendChild(btn);
                });
            });
    }

    // --- LÓGICA DO SELETOR CUSTOMIZADO ---
    if (customSelectWrapper) {
        customSelectTrigger.addEventListener('click', () => {
            customSelectWrapper.classList.toggle('open');
        });
        window.addEventListener('click', (e) => {
            if (!customSelectWrapper.contains(e.target)) {
                customSelectWrapper.classList.remove('open');
            }
        });
    }

    // --- INICIALIZAÇÃO E LÓGICA PRINCIPAL ---

    // 1. Busca os serviços e popula o seletor customizado
    fetch('/api/servicos')
        .then(response => response.json())
        .then(servicos => {
            servicos.forEach(servico => {
                const originalOption = document.createElement('option');
                originalOption.value = servico.id;
                originalOption.textContent = servico.nome;
                selectServicoOriginal.appendChild(originalOption);
                
                const customOption = document.createElement('div');
                customOption.classList.add('custom-option');
                customOption.dataset.value = servico.id;
                customOption.innerHTML = `
                    <span class="option-nome">${servico.nome}</span>
                    <span class="option-detalhes">${servico.duracao_minutos} min | R$ ${parseFloat(servico.preco).toFixed(2).replace('.', ',')}</span>
                `;

                customOption.addEventListener('click', () => {
                    triggerText.textContent = servico.nome;
                    triggerText.classList.remove('placeholder');
                    selectServicoOriginal.value = servico.id;
                    customSelectWrapper.classList.remove('open');
                    datepickerInput.disabled = false;
                    datepickerInput.placeholder = "Selecione uma data...";
                    if (datepickerInput.value) {
                        carregarHorarios(datepickerInput.value);
                    }
                });
                
                customOptionsContainer.appendChild(customOption);
            });
        });

    // 2. Busca a lista de feriados e DEPOIS inicializa o calendário
    fetch('/api/feriados')
        .then(res => res.json())
        .then(data => {
            feriados = data;
            // A inicialização do Flatpickr agora acontece aqui dentro
            flatpickr(datepickerInput, {
                locale: 'pt',
                dateFormat: "Y-m-d",
                minDate: "today",
                disable: [ date => (date.getDay() === 0 || date.getDay() === 1) ],
                // LÓGICA PARA DESTACAR FERIADOS (PARTE 1)
                onDayCreate: function(dObj, dStr, fp, dayElem) {
                    const dateStr = dayElem.dateObj.toISOString().slice(0, 10);
                    if (feriados.includes(dateStr)) {
                        dayElem.classList.add("feriado");
                        dayElem.title = "Feriado! Barbearia fechada.";
                    }
                },
                // LÓGICA PARA BLOQUEAR O CLIQUE EM FERIADOS (PARTE 2)
                onChange: function(selectedDates, dateStr, instance) {
                    if (feriados.includes(dateStr)) {
                        mostrarModal("<b>Feriado!</b><br>A barbearia não funciona neste dia. Por favor, escolha outra data.");
                        horariosContainer.innerHTML = '<p>Dia selecionado é um feriado.</p>';
                        instance.clear(); // Limpa a data inválida
                        return;
                    }
                    carregarHorarios(dateStr);
                },
            });
        });

    // 3. O resto dos listeners (horários, submit do formulário, modal)
    horariosContainer.addEventListener('click', function(e) {
        if (e.target.classList.contains('horario-btn')) {
            document.querySelectorAll('.horario-btn.selected').forEach(btn => btn.classList.remove('selected'));
            e.target.classList.add('selected');
            horaSelecionadaInput.value = e.target.dataset.hora;
        }
    });

    formAgendamento.addEventListener('submit', function(e) {
        e.preventDefault();
        const dadosAgendamento = {
            servico_id: selectServicoOriginal.value,
            data: datepickerInput.value,
            hora: horaSelecionadaInput.value,
        };
        
        if (!dadosAgendamento.hora || !dadosAgendamento.data || !dadosAgendamento.servico_id) {
            mostrarModal('Por favor, preencha todos os campos: serviço, data e horário.');
            return;
        }

        const confirmacao = confirm("Tem certeza que deseja realizar este agendamento?");
        if (confirmacao) {
            btnAgendar.disabled = true;
            btnAgendar.textContent = 'Agendando...';
            fetch('/api/agendar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dadosAgendamento),
            })
            .then(response => response.json())
            .then(data => {
                if (data.sucesso) {
                    window.location.href = data.redirect_url;
                } else {
                    mostrarModal(data.mensagem);
                }
            })
            .catch(error => mostrarModal('Erro de conexão. Tente novamente.'))
            .finally(() => {
                btnAgendar.disabled = false;
                btnAgendar.textContent = 'Confirmar Agendamento';
            });
        }
    });
    
    if (closeButton) {
        closeButton.addEventListener('click', () => { modal.style.display = 'none'; });
    }
    window.addEventListener('click', (e) => {
        if (modal && e.target == modal) {
            modal.style.display = 'none';
        }
    });
});