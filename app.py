import os
os.environ['NUMBA_CACHE_DIR'] = os.path.join(os.getcwd(), 'numba_cache')
import locale
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
    except locale.Error:
        print("Locale pt_BR não encontrado, o mês pode aparecer em inglês.")

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import pymysql
from datetime import datetime, time, timedelta
from functools import wraps
from werkzeug.utils import secure_filename
from rembg import remove
from PIL import Image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/profile_pics'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'webp'}
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-segura-e-dificil'

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, faça o login para acessar esta página."
login_manager.login_message_category = "info"

def get_db_connection():
    return pymysql.connect(
        host='localhost', user='root', password='Buceta10*', # ATENÇÃO: COLOQUE SUA SENHA
        database='barbearia', cursorclass=pymysql.cursors.DictCursor
    )

class User(UserMixin):
    # MUDANÇA: Adicionado 'foto_perfil' ao construtor
    def __init__(self, id, nome, email, role, foto_perfil):
        self.id = id
        self.nome = nome
        self.email = email
        self.role = role
        self.foto_perfil = foto_perfil # NOVO ATRIBUTO


FERIADOS = [
    '2025-01-01', '2025-03-03', '2025-03-04', '2025-04-18', '2025-04-21',
    '2025-05-01', '2025-06-19', '2025-09-07', '2025-10-12', '2025-11-02',
    '2025-11-15', '2025-11-20', '2025-12-25',
]

@app.route('/api/feriados')
def api_feriados():
    return jsonify(FERIADOS)
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        # MUDANÇA: Adicionado 'foto_perfil' à consulta SQL
        cur.execute("SELECT id, nome, email, role, foto_perfil FROM clientes WHERE id = %s", (user_id,))
        user_data = cur.fetchone()
    conn.close()
    if user_data:
        # MUDANÇA: Passando o valor de 'foto_perfil' ao criar o objeto User
        return User(id=user_data['id'], 
                    nome=user_data['nome'], 
                    email=user_data['email'], 
                    role=user_data['role'], 
                    foto_perfil=user_data['foto_perfil'])
    return None

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("Acesso negado. Esta área é restrita aos administradores.", "danger")
            return redirect(url_for('agendar'))
        return f(*args, **kwargs)
    return decorated_function

# ROTAS DE AUTENTICAÇÃO E PÁGINAS DE USUÁRIO
@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('agendar'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        senha = request.form.get('senha')
        conn = get_db_connection()
        with conn.cursor() as cur:
            # MUDANÇA: Adicionado 'foto_perfil' à query
            cur.execute("SELECT id, nome, email, senha_hash, role, foto_perfil FROM clientes WHERE nome = %s AND role = 'cliente'", (nome,))
            user_data = cur.fetchone()
        conn.close()

        if user_data and bcrypt.check_password_hash(user_data['senha_hash'], senha):
            # MUDANÇA: Passando 'foto_perfil' ao criar o User
            user = User(id=user_data['id'], 
                        nome=user_data['nome'], 
                        email=user_data['email'], 
                        role=user_data['role'], 
                        foto_perfil=user_data['foto_perfil'])
            login_user(user)
            return redirect(url_for('agendar'))
        else:
            flash("Falha no login. Verifique seu nome de usuário e senha.", "danger")
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/agendar')
@login_required
def agendar():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('agendar'))
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        senha = request.form.get('senha')
        
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM clientes WHERE nome = %s", (nome,))
            nome_exists = cur.fetchone()
        
        if nome_exists:
            flash("Este nome de usuário já está em uso. Por favor, escolha outro.", "warning")
            conn.close()
            return redirect(url_for('signup'))

        senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')
        
        with conn.cursor() as cur:
            cur.execute("INSERT INTO clientes (nome, email, telefone, senha_hash) VALUES (%s, %s, %s, %s)",
                        (nome, email, telefone, senha_hash))
        conn.commit()
        conn.close()

        flash("Cadastro realizado com sucesso! Por favor, faça o login.", "success")
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Você foi desconectado.", "success")
    return redirect(url_for('login'))

@app.route('/meus-agendamentos')
@login_required
def meus_agendamentos():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT a.id, s.nome as servico, a.data_agendamento, 
                   TIME_FORMAT(a.hora_agendamento, '%%H:%%i') as hora_agendamento, 
                   a.status
            FROM agendamentos a JOIN servicos s ON a.id_servico = s.id
            WHERE a.id_cliente = %s AND a.data_agendamento >= CURDATE()
            ORDER BY a.data_agendamento, a.hora_agendamento
        """, (current_user.id,))
        agendamentos_futuros = cur.fetchall()
        
    conn.close()
    return render_template('meus_agendamentos.html', futuros=agendamentos_futuros)

# --- ROTAS DO PAINEL DE ADMIN ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        senha = request.form.get('senha')
        conn = get_db_connection()
        with conn.cursor() as cur:
            # MUDANÇA: Adicionado 'foto_perfil' à query
            cur.execute("SELECT id, nome, email, senha_hash, role, foto_perfil FROM clientes WHERE nome = %s AND role = 'admin'", (nome,))
            user_data = cur.fetchone()
        conn.close()

        if user_data and bcrypt.check_password_hash(user_data['senha_hash'], senha):
            # MUDANÇA: Passando 'foto_perfil' ao criar o User
            user = User(id=user_data['id'], 
                        nome=user_data['nome'], 
                        email=user_data['email'], 
                        role=user_data['role'], 
                        foto_perfil=user_data['foto_perfil'])
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Credenciais de administrador inválidas.", "danger")
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

# Em app.py, substitua esta função inteira

# Em app.py, substitua a função admin_dashboard

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # MUDANÇA: O filtro agora é "WHERE a.arquivado = FALSE"
            cur.execute("""
                SELECT a.id, c.nome as cliente_nome, c.telefone, s.nome as servico_nome, a.data_agendamento, 
                       TIME_FORMAT(a.hora_agendamento, '%H:%i') as hora_agendamento, 
                       a.status
                FROM agendamentos a 
                JOIN clientes c ON a.id_cliente = c.id 
                JOIN servicos s ON a.id_servico = s.id
                WHERE a.data_agendamento >= CURDATE() AND a.arquivado = FALSE
                ORDER BY a.data_agendamento, a.hora_agendamento
            """)
            agendamentos = cur.fetchall()
    except Exception as e:
        print(f"Erro ao buscar agendamentos para o admin dashboard: {e}")
        agendamentos = []
    finally:
        if conn:
            conn.close()
            
    return render_template('admin_dashboard.html', agendamentos=agendamentos)

@app.route('/agendamentos/cancelar/<int:agendamento_id>', methods=['POST'])
@login_required
def cancelar_agendamento_cliente(agendamento_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM agendamentos WHERE id = %s AND id_cliente = %s", (agendamento_id, current_user.id))
        agendamento = cur.fetchone()
        if agendamento:
            cur.execute("UPDATE agendamentos SET status = 'Cancelado pelo Cliente' WHERE id = %s", (agendamento_id,))
            conn.commit()
            flash("Seu agendamento foi cancelado.", "success")
        else:
            flash("Não foi possível cancelar este agendamento.", "danger")
    conn.close()
    return redirect(url_for('meus_agendamentos'))

# Em app.py, substitua esta função inteira

@app.route('/admin/agendamento/mudar-status/<int:agendamento_id>', methods=['POST'])
@login_required
@admin_required
def mudar_status_agendamento_admin(agendamento_id):
    # MUDANÇA: O novo status agora vem da URL (query parameter) em vez do formulário.
    novo_status = request.args.get('novo_status') 
    
    status_permitidos = ['Agendado', 'Concluído', 'Cancelado pelo Admin']

    if not novo_status or novo_status not in status_permitidos:
        flash("Ação de status inválida.", "danger")
        return redirect(url_for('admin_dashboard'))

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("UPDATE agendamentos SET status = %s WHERE id = %s", (novo_status, agendamento_id))
    conn.commit()
    conn.close()
    flash(f"Status do agendamento alterado para '{novo_status}'.", "success")
    return redirect(url_for('admin_dashboard'))

# ROTAS DE GERENCIAMENTO (NOVAS)
@app.route('/admin/servicos')
@login_required
@admin_required
def admin_servicos():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM servicos ORDER BY nome")
        servicos = cur.fetchall()
    conn.close()
    return render_template('admin_servicos.html', servicos=servicos)

@app.route('/admin/servico/add', methods=['POST'])
@login_required
@admin_required
def add_servico():
    nome = request.form.get('nome')
    duracao = request.form.get('duracao')
    preco = request.form.get('preco')
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("INSERT INTO servicos (nome, duracao_minutos, preco) VALUES (%s, %s, %s)", (nome, duracao, preco))
    conn.commit()
    conn.close()
    flash("Serviço adicionado com sucesso!", "success")
    return redirect(url_for('admin_servicos'))

@app.route('/admin/servico/edit/<int:servico_id>', methods=['POST'])
@login_required
@admin_required
def edit_servico(servico_id):
    nome = request.form.get('nome')
    duracao = request.form.get('duracao')
    preco = request.form.get('preco')
    ativo = 'ativo' in request.form
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("UPDATE servicos SET nome = %s, duracao_minutos = %s, preco = %s, ativo = %s WHERE id = %s", 
                    (nome, duracao, preco, ativo, servico_id))
    conn.commit()
    conn.close()
    flash("Serviço atualizado com sucesso!", "success")
    return redirect(url_for('admin_servicos'))

# Em app.py, encontre a função delete_agendamento e SUBSTITUA pela versão abaixo:

@app.route('/admin/agendamento/delete/<int:agendamento_id>', methods=['POST'])
@login_required
@admin_required
def delete_agendamento(agendamento_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1. Busca o status atual do agendamento antes de qualquer ação
            cur.execute("SELECT status FROM agendamentos WHERE id = %s", (agendamento_id,))
            agendamento = cur.fetchone()

            if not agendamento:
                flash("Agendamento não encontrado.", "danger")
                return redirect(url_for('admin_dashboard'))

            # 2. Lógica condicional: Decide se vai ARQUIVAR ou DELETAR
            if agendamento['status'] == 'Concluído':
                # Se já foi concluído, apenas arquiva para manter o registro financeiro
                cur.execute("UPDATE agendamentos SET arquivado = TRUE WHERE id = %s", (agendamento_id,))
                flash("Agendamento concluído foi arquivado com sucesso e mantido no histórico financeiro.", "success")
            else:
                # Para qualquer outro status (Agendado, Cancelado, etc.), deleta permanentemente
                cur.execute("DELETE FROM agendamentos WHERE id = %s", (agendamento_id,))
                flash("Agendamento não concluído foi deletado permanentemente.", "warning")
        
        conn.commit()

    except Exception as e:
        conn.rollback()
        flash(f"Ocorreu um erro: {e}", "danger")
    finally:
        if conn:
            conn.close()
            
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/bloqueios')
@login_required
@admin_required
def admin_bloqueios():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, data_bloqueio, TIME_FORMAT(hora_inicio, '%H:%i') as hora_inicio, TIME_FORMAT(hora_fim, '%H:%i') as hora_fim, motivo FROM horarios_bloqueados WHERE data_bloqueio >= CURDATE() ORDER BY data_bloqueio, hora_inicio")
        bloqueios = cur.fetchall()
    conn.close()
    return render_template('admin_bloqueios.html', bloqueios=bloqueios)

# Em app.py, substitua a função add_bloqueio por esta

@app.route('/admin/bloqueio/add', methods=['POST'])
@login_required
@admin_required
def add_bloqueio():
    data_str = request.form.get('data')
    hora_inicio_str = request.form.get('hora_inicio')
    hora_fim_str = request.form.get('hora_fim')
    motivo = request.form.get('motivo')

    # Validação básica dos horários
    try:
        hora_inicio_obj = datetime.strptime(hora_inicio_str, '%H:%M').time()
        hora_fim_obj = datetime.strptime(hora_fim_str, '%H:%M').time()
        if hora_fim_obj <= hora_inicio_obj:
            flash("O horário final deve ser depois do horário inicial.", "danger")
            return redirect(url_for('admin_bloqueios'))
    except (ValueError, TypeError):
        flash("Formato de horário inválido.", "danger")
        return redirect(url_for('admin_bloqueios'))
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # --- NOVO: VERIFICAÇÃO DE CONFLITO COM BLOQUEIOS EXISTENTES ---
            cur.execute("""
                SELECT id FROM horarios_bloqueados
                WHERE data_bloqueio = %s AND hora_fim > %s AND hora_inicio < %s
            """, (data_str, hora_inicio_str, hora_fim_str))
            
            if cur.fetchone():
                flash("Este período já está total ou parcialmente bloqueado. Verifique os horários.", "danger")
                return redirect(url_for('admin_bloqueios'))

            # --- LÓGICA DE CONFLITO COM AGENDAMENTOS (já existente) ---
            cur.execute("""
                SELECT a.id, c.nome as cliente_nome
                FROM agendamentos a JOIN clientes c ON a.id_cliente = c.id
                WHERE a.data_agendamento = %s AND a.hora_agendamento >= %s AND a.hora_agendamento < %s AND a.status = 'Agendado'
            """, (data_str, hora_inicio_str, hora_fim_str))
            agendamentos_afetados = cur.fetchall()

            nomes_clientes_afetados = []
            if agendamentos_afetados:
                for ag in agendamentos_afetados:
                    cur.execute("UPDATE agendamentos SET status = 'Cancelado por Bloqueio' WHERE id = %s", (ag['id'],))
                    nomes_clientes_afetados.append(ag['cliente_nome'])

            # Insere o novo bloqueio
            cur.execute("INSERT INTO horarios_bloqueados (data_bloqueio, hora_inicio, hora_fim, motivo) VALUES (%s, %s, %s, %s)",
                        (data_str, hora_inicio_str, hora_fim_str, motivo))
        
        conn.commit()

        if nomes_clientes_afetados:
            msg_cancelados = " Agendamento(s) de: " + ", ".join(nomes_clientes_afetados) + " foram cancelados automaticamente."
            flash("Horário bloqueado com sucesso!" + msg_cancelados, "warning")
        else:
            flash("Horário bloqueado com sucesso!", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Ocorreu um erro ao tentar bloquear o horário: {e}", "danger")
    finally:
        conn.close()
        
    return redirect(url_for('admin_bloqueios'))

# NOVO: Rota para o Dashboard Financeiro

@app.route('/admin/financeiro', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_financeiro():
    conn = get_db_connection()
    dados_financeiros = {}
    agendamentos_dia = []
    faturamento_servicos_mes = []
    
    data_filtro_str = datetime.now().strftime('%Y-%m-%d')
    mes_filtro_str = datetime.now().strftime('%Y-%m')

    # Prioriza o filtro por dia se ambos forem enviados
    if request.method == 'POST':
        if 'data_filtro' in request.form:
             data_filtro_str = request.form.get('data_filtro')
             mes_filtro_str = datetime.strptime(data_filtro_str, '%Y-%m-%d').strftime('%Y-%m')
        elif 'mes_filtro' in request.form:
             mes_filtro_str = request.form.get('mes_filtro')
             # Define o filtro de dia para o primeiro dia do mês filtrado para consistência
             data_filtro_str = mes_filtro_str + '-01'


    try:
        data_filtro_obj = datetime.strptime(data_filtro_str, '%Y-%m-%d')
        data_formatada = data_filtro_obj.strftime('%d/%m/%Y')
        mes_formatado = datetime.strptime(mes_filtro_str, '%Y-%m').strftime('%B de %Y').capitalize()
    except (ValueError, TypeError):
        # Lógica de fallback
        data_filtro_obj = datetime.now()
        data_filtro_str = data_filtro_obj.strftime('%Y-%m-%d')
        data_formatada = data_filtro_obj.strftime('%d/%m/%Y')
        mes_formatado = data_filtro_obj.strftime('%B de %Y').capitalize()
        flash("Data inválida, mostrando resultados para hoje.", "warning")

    try:
        with conn.cursor() as cur:
            # Métricas Gerais
            cur.execute("SELECT SUM(s.preco) as total FROM agendamentos a JOIN servicos s ON a.id_servico = s.id WHERE a.status = 'Concluído' AND a.data_agendamento = CURDATE()")
            faturamento_hoje = cur.fetchone()['total'] or 0

            cur.execute("SELECT SUM(s.preco) as total FROM agendamentos a JOIN servicos s ON a.id_servico = s.id WHERE a.status = 'Concluído' AND MONTH(a.data_agendamento) = MONTH(CURDATE()) AND YEAR(a.data_agendamento) = YEAR(CURDATE())")
            faturamento_mes_atual = cur.fetchone()['total'] or 0
            
            # Detalhes do Dia Filtrado
            cur.execute("SELECT c.nome as cliente, s.nome as servico, s.preco FROM agendamentos a JOIN servicos s ON a.id_servico = s.id JOIN clientes c ON a.id_cliente = c.id WHERE a.status = 'Concluído' AND a.data_agendamento = %s", (data_filtro_str,))
            agendamentos_dia = cur.fetchall()
            total_dia_filtrado = sum(ag['preco'] for ag in agendamentos_dia)

            # Detalhes do Mês Filtrado (por serviço)
            cur.execute("""
                SELECT s.nome as servico_nome, SUM(s.preco) as total_servico
                FROM agendamentos a JOIN servicos s ON a.id_servico = s.id
                WHERE a.status = 'Concluído' AND DATE_FORMAT(a.data_agendamento, '%%Y-%%m') = %s
                GROUP BY s.nome ORDER BY total_servico DESC
            """, (mes_filtro_str,))
            faturamento_servicos_mes = cur.fetchall()
            total_mes_filtrado = sum(s['total_servico'] for s in faturamento_servicos_mes)

            dados_financeiros = {
                'hoje': faturamento_hoje,
                'mes_atual': faturamento_mes_atual,
                'total_dia_filtrado': total_dia_filtrado,
                'total_mes_filtrado': total_mes_filtrado
            }

    except Exception as e:
        flash("Ocorreu um erro ao buscar os dados financeiros.", "danger")
        print(f"Erro no dashboard financeiro: {e}")
    finally:
        conn.close()

    return render_template('admin_financeiro.html', 
                           dados=dados_financeiros, 
                           agendamentos_dia=agendamentos_dia, 
                           faturamento_servicos_mes=faturamento_servicos_mes,
                           data_filtro=data_filtro_str, 
                           data_formatada=data_formatada,
                           mes_filtro=mes_filtro_str,
                           mes_formatado=mes_formatado)
@app.route('/admin/bloqueio/delete/<int:bloqueio_id>', methods=['POST'])
@login_required
@admin_required
def delete_bloqueio(bloqueio_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM horarios_bloqueados WHERE id = %s", (bloqueio_id,))
    conn.commit()
    conn.close()
    flash("Bloqueio removido com sucesso!", "success")
    return redirect(url_for('admin_bloqueios'))

# Rotas de Gestão de Clientes
@app.route('/admin/clientes')
@login_required
@admin_required
def admin_clientes():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, nome, email, telefone FROM clientes WHERE role = 'cliente' ORDER BY nome")
        clientes = cur.fetchall()
    conn.close()
    return render_template('admin_clientes.html', clientes=clientes)

@app.route('/admin/cliente/<int:cliente_id>')
@login_required
@admin_required
def admin_cliente_detalhes(cliente_id):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT nome, email, telefone FROM clientes WHERE id = %s", (cliente_id,))
        cliente = cur.fetchone()
        cur.execute("""
            SELECT a.data_agendamento, TIME_FORMAT(a.hora_agendamento, '%%H:%%i') as hora_agendamento,
                   s.nome as servico, a.status
            FROM agendamentos a JOIN servicos s ON a.id_servico = s.id
            WHERE a.id_cliente = %s ORDER BY a.data_agendamento DESC, a.hora_agendamento DESC
        """, (cliente_id,))
        agendamentos = cur.fetchall()
    conn.close()

    if not cliente:
        flash("Cliente não encontrado.", "danger")
        return redirect(url_for('admin_clientes'))
        
    return render_template('admin_cliente_detalhes.html', cliente=cliente, agendamentos=agendamentos)

# --- ROTAS DE API ---

@app.route('/api/servicos')
@login_required
def get_servicos():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, nome, duracao_minutos, preco FROM servicos WHERE ativo = TRUE ORDER BY nome")
        servicos = cur.fetchall()
    conn.close()
    return jsonify(servicos)

@app.route('/api/horarios-disponiveis')
@login_required
def get_horarios_disponiveis():
    data_str = request.args.get('data')
    servico_id_str = request.args.get('servico_id')

    if not data_str or not servico_id_str:
        return jsonify({'erro': 'Data ou serviço não fornecido'}), 400

    try:
        data_selecionada = datetime.strptime(data_str, '%Y-%m-%d').date()
        servico_id = int(servico_id_str)
    except (ValueError, TypeError):
        return jsonify({'erro': 'Formato de dados inválido.'}), 400

    if data_selecionada.weekday() in [0, 6]: return jsonify([])

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Pega a duração do serviço selecionado
            cur.execute("SELECT duracao_minutos FROM servicos WHERE id = %s", (servico_id,))
            servico = cur.fetchone()
            if not servico:
                return jsonify({'erro': 'Serviço não encontrado'}), 404
            duracao_servico_selecionado = servico['duracao_minutos']

            # Pega todos os agendamentos e bloqueios do dia
            cur.execute("SELECT hora_agendamento as hora_inicio, duracao_minutos FROM agendamentos a JOIN servicos s ON a.id_servico = s.id WHERE a.data_agendamento = %s AND a.status IN ('Agendado', 'Concluído')", (data_selecionada,))
            agendamentos = cur.fetchall()
            cur.execute("SELECT hora_inicio, TIME_TO_SEC(TIMEDIFF(hora_fim, hora_inicio)) / 60 as duracao_minutos FROM horarios_bloqueados WHERE data_bloqueio = %s", (data_selecionada,))
            bloqueios = cur.fetchall()
    finally:
        conn.close()

    # Cria uma lista com todos os períodos ocupados do dia
    periodos_ocupados = []
    for ag in agendamentos:
        inicio = (datetime.combine(data_selecionada, time(0,0)) + ag['hora_inicio']).time()
        fim = (datetime.combine(data_selecionada, inicio) + timedelta(minutes=ag['duracao_minutos'])).time()
        periodos_ocupados.append((inicio, fim))

    for bl in bloqueios:
        inicio = (datetime.combine(data_selecionada, time(0,0)) + bl['hora_inicio']).time()
        fim = (datetime.combine(data_selecionada, inicio) + timedelta(minutes=int(bl['duracao_minutos']))).time()
        periodos_ocupados.append((inicio, fim))

    # Ordena os períodos ocupados pelo horário de início
    periodos_ocupados.sort()

    # Gera os horários disponíveis
    horarios_disponiveis = []
    horario_abertura = time(9, 0)
    horario_fechamento = time(18, 0)
    
    # Se a data for hoje, começa a busca a partir do horário atual
    agora = datetime.now()
    if data_selecionada == agora.date():
        # Arredonda para o próximo slot de 15 minutos
        minuto_arredondado = (agora.minute // 15 + 1) * 15
        if minuto_arredondado >= 60:
            hora_arredondada = agora.hour + 1
            minuto_arredondado = 0
        else:
            hora_arredondada = agora.hour
        
        horario_inicio_teste = time(hora_arredondada, minuto_arredondado)
        # Garante que não comece antes da abertura
        if horario_inicio_teste < horario_abertura:
            horario_inicio_teste = horario_abertura
    else:
        horario_inicio_teste = horario_abertura
    
    # Loop principal para encontrar vagas
    while horario_inicio_teste < horario_fechamento:
        horario_fim_teste = (datetime.combine(data_selecionada, horario_inicio_teste) + timedelta(minutes=duracao_servico_selecionado)).time()
        
        # O serviço não pode terminar depois do fechamento
        if horario_fim_teste > horario_fechamento:
            break

        # Verifica se o slot [inicio, fim] do novo serviço colide com algum período ocupado
        colisao = False
        for inicio_ocupado, fim_ocupado in periodos_ocupados:
            # Verifica a sobreposição de intervalos
            if max(horario_inicio_teste, inicio_ocupado) < min(horario_fim_teste, fim_ocupado):
                colisao = True
                break
        
        if not colisao:
            horarios_disponiveis.append(horario_inicio_teste)

        # Avança para o próximo slot de 15 minutos para testar
        horario_inicio_teste = (datetime.combine(data_selecionada, horario_inicio_teste) + timedelta(minutes=15)).time()

    return jsonify([h.strftime('%H:%M') for h in horarios_disponiveis])

@app.route('/api/admin/agenda-dia')
@login_required
@admin_required
def get_agenda_do_dia():
    data_str = request.args.get('data')
    if not data_str:
        return jsonify({'erro': 'Data não fornecida'}), 400
    try:
        data_selecionada = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'erro': 'Formato de data inválido.'}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT TIME_FORMAT(a.hora_agendamento, '%%H:%%i') as hora, c.nome as cliente, s.nome as servico, a.status
                FROM agendamentos a
                LEFT JOIN clientes c ON a.id_cliente = c.id
                LEFT JOIN servicos s ON a.id_servico = s.id
                WHERE a.data_agendamento = %s ORDER BY a.hora_agendamento
            """, (data_selecionada,))
            agenda_do_dia = cur.fetchall()
        return jsonify(agenda_do_dia)
    except Exception as e:
        print(f"ERRO NA API /api/admin/agenda-dia: {e}") 
        return jsonify({'erro': 'Ocorreu um erro interno no servidor.'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/agendar', methods=['POST'])
@login_required
def api_agendar():
    dados = request.get_json()
    if not all(k in dados for k in ['servico_id', 'data', 'hora']):
        return jsonify({'sucesso': False, 'mensagem': 'Dados incompletos.'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO agendamentos (id_cliente, id_servico, data_agendamento, hora_agendamento, status) "
                "VALUES (%s, %s, %s, %s, 'Agendado')",
                (current_user.id, dados['servico_id'], dados['data'], dados['hora'])
            )
        conn.commit()
        return jsonify({'sucesso': True, 'mensagem': 'Agendamento realizado com sucesso!', 'redirect_url': url_for('meus_agendamentos')})
    except Exception as e:
        conn.rollback()
        return jsonify({'sucesso': False, 'mensagem': 'Ocorreu um erro ao salvar o agendamento.'}), 500
    finally:
        if conn:
            conn.close()



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# --- NOVAS ROTAS PARA O PERFIL DO CLIENTE ---

@app.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html')

@app.route('/perfil/editar-dados', methods=['POST'])
@login_required
def editar_dados():
    novo_nome = request.form.get('nome')
    novo_email = request.form.get('email')
    novo_telefone = request.form.get('telefone')

    # Validação para ver se o novo nome de usuário já não está em uso por outra pessoa
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM clientes WHERE nome = %s AND id != %s", (novo_nome, current_user.id))
        nome_exists = cur.fetchone()
        if nome_exists:
            flash("Este nome de usuário já está em uso por outra conta.", "danger")
            return redirect(url_for('perfil'))
        
        # Faz o update dos dados
        cur.execute("UPDATE clientes SET nome = %s, email = %s, telefone = %s WHERE id = %s",
                    (novo_nome, novo_email, novo_telefone, current_user.id))
    conn.commit()
    conn.close()
    
    flash("Dados atualizados com sucesso!", "success")
    return redirect(url_for('perfil'))

@app.route('/perfil/mudar-senha', methods=['POST'])
@login_required
def mudar_senha():
    senha_atual = request.form.get('senha_atual')
    nova_senha = request.form.get('nova_senha')

    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT senha_hash FROM clientes WHERE id = %s", (current_user.id,))
        user_data = cur.fetchone()
    conn.close()

    # Verifica se a senha atual está correta
    if user_data and bcrypt.check_password_hash(user_data['senha_hash'], senha_atual):
        # Criptografa e salva a nova senha
        nova_senha_hash = bcrypt.generate_password_hash(nova_senha).decode('utf-8')
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("UPDATE clientes SET senha_hash = %s WHERE id = %s", (nova_senha_hash, current_user.id))
        conn.commit()
        conn.close()
        flash("Senha alterada com sucesso!", "success")
    else:
        flash("A senha atual está incorreta.", "danger")

    return redirect(url_for('perfil'))

@app.route('/perfil/upload-foto', methods=['POST'])
@login_required
def upload_foto():
    if 'foto' not in request.files:
        flash('Nenhum arquivo enviado.', 'danger')
        return redirect(url_for('perfil'))
    
    file = request.files['foto']
    if file.filename == '':
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('perfil'))

    if file and allowed_file(file.filename):
        # Remove a foto antiga (se não for a padrão)
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT foto_perfil FROM clientes WHERE id = %s", (current_user.id,))
            foto_antiga = cur.fetchone()['foto_perfil']
            if foto_antiga and foto_antiga != 'default.png':
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], foto_antiga))
                except OSError as e:
                    print(f"Erro ao remover foto antiga: {e}")

        # Processa a nova foto
        filename = secure_filename(file.filename)
        # Cria um nome de arquivo único para evitar conflitos
        unique_filename = f"user_{current_user.id}_{filename.rsplit('.', 1)[0]}.png"
        
        # Abre a imagem enviada
        input_image = Image.open(file.stream)
        # Usa a biblioteca rembg para remover o fundo
        output_image = remove(input_image)

        # Salva a imagem processada (com fundo transparente)
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        output_image.save(output_path, 'PNG')
        
        # Atualiza o banco de dados com o nome do novo arquivo
        with conn.cursor() as cur:
            cur.execute("UPDATE clientes SET foto_perfil = %s WHERE id = %s", (unique_filename, current_user.id))
        conn.commit()
        conn.close()

        flash('Foto de perfil atualizada com sucesso!', 'success')
    else:
        flash('Tipo de arquivo não permitido.', 'danger')

    return redirect(url_for('perfil'))

@app.route('/perfil/remover-foto', methods=['POST'])
@login_required
def remover_foto():
    conn = get_db_connection()
    with conn.cursor() as cur:
        # Pega o nome da foto atual para deletar o arquivo
        cur.execute("SELECT foto_perfil FROM clientes WHERE id = %s", (current_user.id,))
        foto_atual = cur.fetchone()['foto_perfil']

        # Deleta o arquivo físico, se não for a imagem padrão
        if foto_atual and foto_atual != 'default.png':
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], foto_atual))
            except OSError as e:
                print(f"Erro ao remover foto: {e}")
        
        # Reseta o nome do arquivo no banco de dados para o padrão
        cur.execute("UPDATE clientes SET foto_perfil = 'default.png' WHERE id = %s", (current_user.id,))
    conn.commit()
    conn.close()

    flash('Foto de perfil removida.', 'success')
    return redirect(url_for('perfil'))

if __name__ == '__main__':
    # O Render usa a variável de ambiente PORT. No seu PC, ele usará a porta 5000 como padrão.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)