import random
import uuid
from typing import List, Dict, Any
from app.models.schemas import PatientProfile, PatientVitals, CareLevel

class MIMICDatasetFixture:
    """
    Automated demonstration dataset generator for Aegis Triage OS.
    Builds structured medical test entries for spatial and clinical evaluation.
    """
    
    TARGET_LAT = 13.1008
    TARGET_LON = 77.5963
    TARGET_SYMPTOMS = ["high fever", "acute localized skin rash"]

    def __init__(self):
        self.data: List[Dict[str, Any]] = []

    def generate_fixture(self) -> List[Dict[str, Any]]:
        """
        Builds exactly 50 structured medical entries with a localized epidemic cluster.
        Includes risk_score and mental_health_flag for prioritization logic testing.
        """
        self.data = []
        
        # 1. Generate 15 Locked Cluster Records (Yelahanka, Bengaluru)
        for _ in range(15):
            lat_offset = random.uniform(-0.002, 0.002)
            lon_offset = random.uniform(-0.002, 0.002)
            
            self.data.append({
                "patient_id": str(uuid.uuid4()),
                "profile": PatientProfile(
                    age=random.randint(5, 75),
                    gender=random.choice(['M', 'F', 'O']),
                    medical_history=["none"],
                    vitals=PatientVitals(
                        heart_rate=random.randint(110, 145), # Elevated for cluster
                        spO2=random.randint(90, 95), # Lower for cluster
                        temperature=random.uniform(102.0, 104.5) # Fever for cluster
                    ),
                    latitude=self.TARGET_LAT + lat_offset,
                    longitude=self.TARGET_LON + lon_offset
                ).model_dump(),
                "extracted_symptoms": self.TARGET_SYMPTOMS,
                "care_level": CareLevel.EMERGENCY_ROOM,
                "risk_score": random.randint(8, 10),
                "mental_health_flag": random.choice([True, False]),
                "is_cluster_member": True
            })

        # 2. Generate 35 Distributed Baseline Records
        for _ in range(35):
            self.data.append({
                "patient_id": str(uuid.uuid4()),
                "profile": PatientProfile(
                    age=random.randint(0, 100),
                    gender=random.choice(['M', 'F', 'O']),
                    medical_history=random.sample(["hypertension", "diabetes", "asthma", "none"], k=random.randint(1, 2)),
                    vitals=PatientVitals(
                        heart_rate=random.randint(60, 100),
                        spO2=random.randint(96, 100),
                        temperature=random.uniform(97.0, 99.0)
                    ),
                    latitude=12.9716 + random.uniform(-0.1, 0.1),
                    longitude=77.5946 + random.uniform(-0.1, 0.1)
                ).model_dump(),
                "extracted_symptoms": random.sample(["headache", "cough", "fatigue", "nausea"], k=random.randint(1, 3)),
                "care_level": random.choice([CareLevel.HOME_CARE, CareLevel.CLINIC_VISIT]),
                "risk_score": random.randint(1, 5),
                "mental_health_flag": False,
                "is_cluster_member": False
            })

        random.shuffle(self.data)
        return self.data

# Singleton for demonstration execution
mock_fixture = MIMICDatasetFixture()
