from fastapi import APIRouter, HTTPException, status
from typing import List
from services.clustering import FrequencyClusteringService
from pydantic import BaseModel, Field, validator
import numpy as np
from utils.exceptions import DFTError
import logging

router = APIRouter()

class FrequencyData(BaseModel):
    dft_output: List[float] = Field(..., description="Magnitude spectrum from DFT")
    frequencies: List[float] = Field(..., description="Corresponding frequency values")
    n_clusters: int = Field(default=3, ge=2, le=10, description="Number of clusters to find")

    @validator('dft_output', 'frequencies')
    def validate_arrays(cls, v):
        if not v:
            raise ValueError("Array cannot be empty")
        if len(v) > 1_000_000:
            raise ValueError("Array too large: maximum 1,000,000 points allowed")
        if any(not np.isfinite(x) for x in v):
            raise ValueError("Array contains invalid values (inf or nan)")
        return v

    @validator('frequencies')
    def validate_frequencies(cls, v, values):
        if 'dft_output' in values and len(v) != len(values['dft_output']):
            raise ValueError("Frequencies and DFT output must have the same length")
        return v

@router.post("/analyze-patterns")
async def analyze_frequency_patterns(data: FrequencyData):
    """
    Analyze frequency patterns in DFT output using K-means clustering.
    
    Args:
        data: FrequencyData containing DFT output and frequencies
        
    Returns:
        Dictionary containing cluster statistics and dominant frequencies
        
    Raises:
        HTTPException: If clustering fails or input data is invalid
    """
    try:
        clustering_service = FrequencyClusteringService(n_clusters=data.n_clusters)
        cluster_stats = clustering_service.get_cluster_statistics(
            data.dft_output,
            data.frequencies,
            use_cache=True
        )
        
        return {
            "status": "success",
            "data": cluster_stats
        }
        
    except ValueError as e:
        raise DFTError(str(e))
    except Exception as e:
        logging.error(f"Clustering error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing frequency patterns"
        )
