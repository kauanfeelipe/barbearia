document.addEventListener('DOMContentLoaded', function() {
    // Seleciona os elementos da nova funcionalidade no painel do admin
    const datepicker = document.getElementById('admin-datepicker');
    const container = document.getElementById('agenda-do-dia-container');

    // Se o datepicker não existir na página, não faz nada.
    if (!datepicker) {
        return;
    }

    // Função para buscar e renderizar a agenda de um dia específico
    function buscarAgenda(data) {
        // Mostra uma mensagem de carregamento
        container.innerHTML = '<p>Buscando agendamentos...</p>';

        // Faz a chamada para a nova API
        fetch(`/api/admin/agenda-dia?data=${data}`)
            .then(response => {
                if (!response.ok) {
                    // Se a resposta do servidor for um erro (como 500), lança um erro
                    throw new Error(`Erro no servidor: ${response.status}`);
                }
                return response.json();
            })
            .then(agendamentos => {
                // Limpa o container
                container.innerHTML = '';

                // Se a resposta não for um array (pode acontecer em alguns casos de erro)
                if (!Array.isArray(agendamentos)) {
                    container.innerHTML = '<p class="text-danger">Resposta inesperada do servidor.</p>';
                    return;
                }

                // Se não houver agendamentos, mostra uma mensagem
                if (agendamentos.length === 0) {
                    container.innerHTML = '<p>Nenhum agendamento para este dia.</p>';
                    return;
                }

                // Cria o cabeçalho da tabela
                // Usamos 'T00:00:00' para evitar problemas de fuso horário ao formatar a data
                let dataFormatada = new Date(data + 'T00:00:00').toLocaleDateString('pt-BR');
                let tabelaHTML = `
                    <h3>Agendamentos para ${dataFormatada}</h3>
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th>Hora</th>
                                <th>Cliente</th>
                                <th>Serviço</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                // Preenche a tabela com os dados dos agendamentos
                agendamentos.forEach(ag => {
                    tabelaHTML += `
                        <tr>
                            <td>${ag.hora}</td>
                            <td>${ag.cliente}</td>
                            <td>${ag.servico}</td>
                            <td><span class="status-${ag.status.toLowerCase().replace(/ /g, '-')}">${ag.status}</span></td>
                        </tr>
                    `;
                });

                // Fecha a tabela
                tabelaHTML += `</tbody></table>`;

                // Insere a tabela pronta no container
                container.innerHTML = tabelaHTML;
            })
            .catch(error => {
                // Em caso de erro na comunicação, exibe uma mensagem
                container.innerHTML = '<p class="text-danger">Erro ao buscar a agenda. Tente novamente.</p>';
                console.error('Erro no fetch:', error);
            });
    }

    // Inicializa o calendário (Flatpickr)
    flatpickr(datepicker, {
        locale: 'pt',
        dateFormat: "Y-m-d",
        // Quando uma data é selecionada, chama a função para buscar a agenda
        onChange: function(selectedDates, dateStr, instance) {
            buscarAgenda(dateStr);
        }
    });
});