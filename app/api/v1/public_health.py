import logging
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from sklearn.cluster import HDBSCAN
from app.services.database import db_client

router = APIRouter()
logger = logging.getLogger("aegis_core")

@router.get("/outbreaks")
async def detect_outbreaks():
    """
    Geospatial epidemic clustering routine using HDBSCAN with Haversine metric.
    Identifies high-density patient clusters for public health monitoring.
    """
    try:
        # 1. Extract tracking coordinates from the database
        response = db_client.client.table("patients").select("geo_latitude, geo_longitude").execute()
        data = response.data
        
        if not data or len(data) < 5:
            return {"clusters": [], "message": "Insufficient data for spatial clustering."}

        df = pd.DataFrame(data)
        
        # 2. HDBSCAN Execution with Haversine metric
        # CRITICAL: HDBSCAN requires data conversion into radians for Haversine geospatial calculations
        coords_radians = np.radians(df[['geo_latitude', 'geo_longitude']].to_numpy())
        
        # metric='haversine' assumes [lat, lon] or [phi, lambda] in radians
        clusterer = HDBSCAN(
            min_cluster_size=5, 
            metric='haversine', 
            cluster_selection_epsilon=0.001 / 6371.0 # 1 meter epsilon in radians approx
        )
        labels = clusterer.fit_predict(coords_radians)
        df['cluster_id'] = labels

        # 3. Calculate centers and densities for identified clusters
        clusters = []
        for cluster_id in set(labels):
            if cluster_id == -1:
                continue # Skip noise
            
            cluster_points = df[df['cluster_id'] == cluster_id]
            center_lat = cluster_points['geo_latitude'].mean()
            center_lon = cluster_points['geo_longitude'].mean()
            density = len(cluster_points)
            
            clusters.append({
                "cluster_id": int(cluster_id),
                "center_latitude": float(center_lat),
                "center_longitude": float(center_lon),
                "density_count": density,
                "radius_km_approx": 1.0 # Visualization hint
            })

        return {
            "status": "success",
            "cluster_count": len(clusters),
            "clusters": clusters
        }

    except Exception as e:
        logger.error(f"Geospatial clustering failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal spatial analysis exception.")
