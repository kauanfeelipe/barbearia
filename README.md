# 💈 Sistema de Gestão e Agendamento para Barbearias

Um projeto full-stack desenvolvido com **Python e Flask**, criado para fornecer uma solução completa de **agendamento, gestão e controle financeiro** para barbearias. Este sistema foi desenvolvido do zero com foco em **robustez, segurança e escalabilidade**.

---

## ✨ Funcionalidades Principais

### 📅 Agendamento Dinâmico
- Escolha de serviço pelo cliente.
- Cálculo em tempo real dos horários disponíveis.
- Considera duração dos serviços, agendamentos existentes e bloqueios manuais.

### 👤 Perfis de Usuário com IA
- Upload de foto de perfil com IA.
- Remoção automática do fundo usando a biblioteca `rembg`.

### 💼 Painel de Gestão para Administradores
- Controle de clientes, serviços e agendamentos.
- Bloqueios manuais e lógica de arquivamento de histórico.
- Visualização centralizada de dados e relatórios.

### 💰 Dashboard Financeiro
- Faturamento diário e mensal.
- Relatórios por tipo de serviço.
- Visão clara da performance da barbearia.

---
📸 Imagens do Sistema
![1750818669083](https://github.com/user-attachments/assets/086a35ba-f6fd-43cc-bfae-2028e2920212)


## 🛠️ Arquitetura & Tecnologias

| Camada         | Descrição                                                                 |
|----------------|---------------------------------------------------------------------------|
| **Backend**    | Flask (Python) com API RESTful e lógica de negócio                        |
| **Frontend**   | HTML com Jinja2 (renderização server-side com herança e blocos dinâmicos) |
| **Banco de Dados** | MySQL (queries parametrizadas com PyMySQL)                            |
| **Assets**     | Estrutura `static/` organizada com CSS, JS e imagens                      |
| **Autenticação** | Controle de acesso + Flask-Bcrypt para hash seguro de senhas           |
| **Inteligência Artificial** | Integração com `rembg` para remover fundo de imagens         |

---
## 📦 Instalação Local

1. **Clone o repositório**
   ```bash
   git clone https://github.com/seu-usuario/barbearia_agendamento.git
   cd barbearia_agendamento
Crie e ative o ambiente virtual

python -m venv venv
.\venv\Scripts\activate  # No Windows

Instale as dependências

pip install -r requirements.txt

Configure as variáveis de ambiente
Crie um arquivo .env com:

DB_HOST=localhost
DB_USER=root
DB_PASSWORD=sua_senha
DB_NAME=barbearia


Inicie o servidor

python app.py
