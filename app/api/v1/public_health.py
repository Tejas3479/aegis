from fastapi import APIRouter
from sklearn.cluster import HDBSCAN
import numpy as np

router = APIRouter()

@router.post("/cluster")
async def detect_epidemic_clusters(coordinates: list):
    """
    Real-time geospatial HDBSCAN epidemic clustering engine.
    """
    if not coordinates:
        return {"clusters": []}
        
    data = np.array(coordinates)
    clusterer = HDBSCAN(min_cluster_size=5)
    labels = clusterer.fit_predict(data)
    
    return {
        "engine": "HDBSCAN",
        "clusters": labels.tolist(),
        "count": len(set(labels)) - (1 if -1 in labels else 0)
    }
