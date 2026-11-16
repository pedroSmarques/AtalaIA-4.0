-- ==========================================================
-- Criação do Banco de Dados: ATALAIA
-- ==========================================================
CREATE DATABASE IF NOT EXISTS atalaia
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE atalaia;

-- ==========================================================
-- 1. Criação das Tabelas Independentes (Sem Chaves Estrangeiras)
-- ==========================================================

CREATE TABLE setor (
    id_setor INT AUTO_INCREMENT PRIMARY KEY,
    nome_setor VARCHAR(50) NOT NULL,
    descricao TEXT,
    nivel_risco ENUM('baixo', 'medio', 'alto', 'critico') NOT NULL
);

CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    cargo ENUM('Gestor', 'Supervisor', 'Tecnico') NOT NULL,
    status_conta ENUM('ativo', 'inativo', 'bloqueado') NOT NULL,
    token_push VARCHAR(255) NULL,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE TipoInfracao (
    id_tipo_infracao INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    gravidade ENUM('leve', 'media', 'grave', 'critica') NOT NULL,
    norma_relacionada VARCHAR(30)
);

-- ==========================================================
-- 2. Criação das Tabelas Dependentes (Com Chaves Estrangeiras)
-- ==========================================================

-- Tabela Associativa N:M (Setor <-> Usuarios)
CREATE TABLE setor_usuario (
    fk_Setor_id_setor INT NOT NULL,
    fk_Usuarios_id_usuario INT NOT NULL,
    PRIMARY KEY (fk_Setor_id_setor, fk_Usuarios_id_usuario),
    FOREIGN KEY (fk_Setor_id_setor) REFERENCES Setor(id_setor) ON DELETE CASCADE,
    FOREIGN KEY (fk_Usuarios_id_usuario) REFERENCES Usuarios(id_usuario) ON DELETE CASCADE
);

CREATE TABLE camera (
    id_camera INT AUTO_INCREMENT PRIMARY KEY,
    codigo_identificador VARCHAR(50) NOT NULL,
    url_rtsp_stream VARCHAR(512) NOT NULL,
    status ENUM('ativa', 'inativa', 'manutenção') NOT NULL,
    fps_operacao INT NOT NULL,
    fk_Setor_id_setor INT NOT NULL,
    FOREIGN KEY (fk_Setor_id_setor) REFERENCES Setor(id_setor)
);

CREATE TABLE incidente (
    id_incidente INT AUTO_INCREMENT PRIMARY KEY,
    data_hora_deteccao DATETIME NOT NULL,
    caminho_snapshot VARCHAR(255) NOT NULL,
    confianca_ia FLOAT NOT NULL,
    status_atendimento ENUM('pendente', 'em atendimento', 'resolvido', 'falso positivo') DEFAULT 'pendente',
    observacao_atendimento TEXT,
    data_hora_resolucao DATETIME NULL,
    fk_Camera_id_camera INT NOT NULL,
    fk_TipoInfracao_id_tipo_infracao INT NOT NULL,
    fk_Usuarios_id_usuario INT NULL, -- NULLable pois a IA cadastra sem dono inicial
    FOREIGN KEY (fk_Camera_id_camera) REFERENCES Camera(id_camera),
    FOREIGN KEY (fk_TipoInfracao_id_tipo_infracao) REFERENCES TipoInfracao(id_tipo_infracao),
    FOREIGN KEY (fk_Usuarios_id_usuario) REFERENCES Usuarios(id_usuario)
);

CREATE TABLE notificacoesPush (
    id_notificacao INT AUTO_INCREMENT PRIMARY KEY,
    data_hora_envio DATETIME NOT NULL,
    status_envio ENUM('enviado', 'entregue', 'lido', 'falha') NOT NULL,
    fk_Usuarios_id_usuario INT NOT NULL,
    fk_Incidente_id_incidente INT NOT NULL,
    FOREIGN KEY (fk_Usuarios_id_usuario) REFERENCES Usuarios(id_usuario),
    FOREIGN KEY (fk_Incidente_id_incidente) REFERENCES Incidente(id_incidente) ON DELETE CASCADE
);

CREATE TABLE logs (
    id_log INT AUTO_INCREMENT PRIMARY KEY,
    acao_realizada VARCHAR(30) NOT NULL,
    tabela_afetada VARCHAR(50) NULL,
    id_registro_afetado INT NULL,
    ip_origem VARCHAR(100) NOT NULL,
    detalhes TEXT NULL,
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    fk_Usuarios_id_usuario INT NULL, -- NULLable para permitir logs do próprio sistema
    FOREIGN KEY (fk_Usuarios_id_usuario) REFERENCES Usuarios(id_usuario)
);

-- FIM DO SCRIPT