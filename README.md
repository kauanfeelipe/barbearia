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

<p align="center">
  <img src="https://github.com/user-attachments/assets/dd31b53a-4415-4ad8-b6a6-9a49c40ac04b" width="400" />
  <img src="https://github.com/user-attachments/assets/cf4781cd-2d72-4163-ad49-9a7d3553977b" width="400" />
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/f425e273-290e-4eef-a920-f9054086a944" width="400" />
  <img src="https://github.com/user-attachments/assets/a16c4ab7-1754-4e56-884d-51881a3badd0" width="400" />
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/d0bb5cd3-9b1a-4f25-8d0b-560328ec66ed" width="400" />
  <img src="https://github.com/user-attachments/assets/3e248966-54b8-4357-82ac-5c950fa5d2f4" width="400" />
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/b7119969-422a-43db-a13d-ac4fd99b049c" width="400" />
</p>




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
