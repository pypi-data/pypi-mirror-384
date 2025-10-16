-- mem8 Database Initialization Script
-- This script sets up initial database configuration for PostgreSQL

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create database if it doesn't exist (for development)
-- Note: This runs after the database is already created by Docker
-- but ensures we have proper permissions and extensions

-- Grant necessary permissions to the created database
GRANT ALL PRIVILEGES ON DATABASE mem8_dev TO mem8_user;

-- Set timezone
SET timezone = 'UTC';