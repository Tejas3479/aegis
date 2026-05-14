-- Aegis Triage OS - Redesigned & Finalized Database Schema
-- Optimizations for Doctor Dashboard Prioritization and Mental Health Tracking

-- 1. Enable Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Clean Environment Reset
DROP TABLE IF EXISTS outbreaks CASCADE;
DROP TABLE IF EXISTS medication_reminders CASCADE;
DROP TABLE IF EXISTS dpdp_consent_logs CASCADE;
DROP TABLE IF EXISTS medical_audit_logs CASCADE;
DROP TABLE IF EXISTS triage_sessions CASCADE;
DROP TABLE IF EXISTS patients CASCADE;

-- 3. Core Structural Tables
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anon_hash VARCHAR(64) UNIQUE NOT NULL,
    geo_latitude DECIMAL(9,6) NOT NULL,
    geo_longitude DECIMAL(9,6) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Optimization: Geospatial index for faster HDBSCAN retrieval
CREATE INDEX idx_patients_coords ON patients(geo_latitude, geo_longitude);

CREATE TABLE triage_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE RESTRICT,
    care_level VARCHAR(20) CHECK (care_level IN ('HOME_CARE', 'CLINIC_VISIT', 'EMERGENCY_ROOM')),
    risk_score INT DEFAULT 0, -- CRITICAL: For Doctor Dashboard prioritization (0-10)
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'CLOSED', 'ESCALATED')),
    mental_health_flag BOOLEAN DEFAULT FALSE, -- For Hackathon Advanced Feature
    webrtc_room_url TEXT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE medical_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES triage_sessions(id) ON DELETE CASCADE,
    symptoms JSONB NOT NULL,
    model_metadata JSONB NOT NULL, -- Lineage, F1-Score, Bias metrics
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dpdp_consent_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE RESTRICT,
    consent_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    purpose_agreed TEXT NOT NULL,
    ip_address_hashed VARCHAR(64) NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE
);

CREATE TABLE medication_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    medication_name VARCHAR(255) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    cron_schedule VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE outbreaks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id INT NOT NULL,
    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    predicted_pathology TEXT NOT NULL,
    density_count INT NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =======================================================
-- 5. ENTERPRISE SECURITY: ROW-LEVEL SECURITY (RLS)
-- =======================================================

-- Enable RLS for all clinical tables
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE triage_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE medication_reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE dpdp_consent_logs ENABLE ROW LEVEL SECURITY;

-- EXAMPLE POLICIES (Intent-Based for Enterprise Hardening)
-- Doctors can see all triage sessions for prioritization
-- CREATE POLICY doctor_all_access ON triage_sessions FOR SELECT 
-- USING (auth.jwt() ->> 'role' = 'DOCTOR');

-- Patients can only see their own anonymized entries (via anon_hash mapping)
-- CREATE POLICY patient_self_access ON patients FOR SELECT
-- USING (anon_hash = (select anon_hash from patients where id = auth.uid()));

-- =======================================================
-- 6. THE HACKATHON WINNING SEED 
-- 15 Patients perfectly clustered in Yelahanka (BMSIT Area)
INSERT INTO patients (id, anon_hash, geo_latitude, geo_longitude)
SELECT 
    gen_random_uuid(),
    md5(random()::text),
    13.1008 + (random() * 0.002 - 0.001), 
    77.5963 + (random() * 0.002 - 0.001)
FROM generate_series(1, 15);

-- 35 Noise patients scattered across Bengaluru
INSERT INTO patients (id, anon_hash, geo_latitude, geo_longitude)
SELECT 
    gen_random_uuid(),
    md5(random()::text),
    12.9716 + (random() * 0.1 - 0.05),
    77.5946 + (random() * 0.1 - 0.05)
FROM generate_series(1, 35);
