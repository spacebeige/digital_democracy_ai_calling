-- PostgreSQL setup script for AI Grievance System

-- Create database
CREATE DATABASE grievance_db;

-- Connect to the database
\c grievance_db;

-- Create tickets table
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    issue VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    priority VARCHAR(50) NOT NULL CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW')),
    status VARCHAR(50) NOT NULL DEFAULT 'Open' CHECK (status IN ('Open', 'In Progress', 'Resolved')),
    sla_hours INTEGER NOT NULL,
    summary TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_priority ON tickets(priority);
CREATE INDEX idx_tickets_location ON tickets(location);

-- Insert sample data for testing
INSERT INTO tickets (issue, location, priority, status, sla_hours, summary, created_at) VALUES
('flood', 'Main Street Market', 'HIGH', 'Open', 1, 'Complaint about flood issue at Main Street Market reported with HIGH priority. Details: Severe flooding reported...', NOW() - INTERVAL '30 minutes'),
('waste', 'Downtown Area', 'LOW', 'Resolved', 24, 'Complaint about waste issue at Downtown Area reported with LOW priority. Details: Garbage piled up...', NOW() - INTERVAL '5 days'),
('flood', 'River Bank', 'HIGH', 'In Progress', 1, 'Complaint about flood issue at River Bank reported with HIGH priority. Details: Water overflowing...', NOW() - INTERVAL '45 minutes'),
('pollution', 'Industrial Zone', 'MEDIUM', 'Open', 6, 'Complaint about pollution issue at Industrial Zone reported with MEDIUM priority. Details: Smoke visible...', NOW() - INTERVAL '2 hours'),
('other', 'City Center', 'MEDIUM', 'Open', 6, 'Complaint about other issue at City Center reported with MEDIUM priority. Details: General complaint...', NOW() - INTERVAL '1 hour');
