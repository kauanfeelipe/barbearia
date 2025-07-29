document.addEventListener('DOMContentLoaded', function() {
    const datepicker = document.getElementById('admin-datepicker');
    const container = document.getElementById('agenda-do-dia-container');
    if (!datepicker) {
        return;
    }

    function buscarAgenda(data) {
        container.innerHTML = '<p>Buscando agendamentos...</p>';
        fetch(`/api/admin/agenda-dia?data=${data}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erro no servidor: ${response.status}`);
                }
                return response.json();
            })
            .then(agendamentos => {
                container.innerHTML = '';

                if (!Array.isArray(agendamentos)) {
                    container.innerHTML = '<p class="text-danger">Resposta inesperada do servidor.</p>';
                    return;
                }

                if (agendamentos.length === 0) {
                    container.innerHTML = '<p>Nenhum agendamento para este dia.</p>';
                    return;
                }

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

                tabelaHTML += `</tbody></table>`;

                container.innerHTML = tabelaHTML;
            })
            .catch(error => {
                container.innerHTML = '<p class="text-danger">Erro ao buscar a agenda. Tente novamente.</p>';
                console.error('Erro no fetch:', error);
            });
    }

    flatpickr(datepicker, {
        locale: 'pt',
        dateFormat: "Y-m-d",
        onChange: function(selectedDates, dateStr, instance) {
            buscarAgenda(dateStr);
        }
    });
});