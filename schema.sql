-- Aegis Triage OS - Database Schema Initialization
-- Version: 1.0.0

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Patients Table: Stores anonymized patient records with geospatial data
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    anon_hash VARCHAR(64) UNIQUE NOT NULL,
    geo_latitude DECIMAL(9,6) NOT NULL,
    geo_longitude DECIMAL(9,6) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_patients_hash ON patients(anon_hash);

-- 2. Triage Sessions: Tracks the lifecycle of a patient's health inquiry
CREATE TABLE triage_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE RESTRICT,
    care_level VARCHAR(20) CHECK (care_level IN ('HOME_CARE', 'CLINIC_VISIT', 'EMERGENCY_ROOM')),
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'CLOSED', 'ESCALATED')),
    webrtc_room_url TEXT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Medical Audit Logs: Secure ledger for clinical data and model metadata
CREATE TABLE medical_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES triage_sessions(id) ON DELETE CASCADE,
    symptoms JSONB NOT NULL,
    model_metadata JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_session ON medical_audit_logs(session_id);

-- 4. DPDP Consent Logs: Digital Personal Data Protection compliance tracking
CREATE TABLE dpdp_consent_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE RESTRICT,
    consent_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    purpose_agreed TEXT NOT NULL,
    ip_address_hashed VARCHAR(64) NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE
);

-- 5. Medication Reminders: Scheduling engine for patient adherence
CREATE TABLE medication_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES patients(id) ON DELETE CASCADE,
    medication_name VARCHAR(255) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    cron_schedule VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Outbreaks: Geospatial clustering results for public health monitoring
CREATE TABLE outbreaks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id INT NOT NULL,
    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    predicted_pathology TEXT NOT NULL,
    density_count INT NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
