from typing import List, Dict

class MockDatasets:
    """
    Embedded test fixtures simulating localized patient cohorts.
    """
    PATIENTS = [
        {"anon_hash": "a1b2c3d4", "geo_latitude": 37.7749, "geo_longitude": -122.4194},
        {"anon_hash": "e5f6g7h8", "geo_latitude": 34.0522, "geo_longitude": -118.2437},
        {"anon_hash": "i9j0k1l2", "geo_latitude": 40.7128, "geo_longitude": -74.0060},
    ]

    SYMPTOMS = [
        {"patient_id": "a1b2c3d4", "symptoms": ["headache", "fever"]},
        {"patient_id": "e5f6g7h8", "symptoms": ["cough", "fatigue"]},
    ]

    def get_test_cohort(self) -> List[Dict]:
        return self.PATIENTS

mock_data = MockDatasets()
