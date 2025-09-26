# scripts/init_db.sql - PostgreSQL initialization script
-- Create database if not exists
CREATE DATABASE job_board_db OWNER jobboard_user;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE job_board_db TO jobboard_user;

-- Create extensions
\c job_board_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";