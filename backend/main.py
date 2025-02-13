from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, TypedDict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from forensics_triage_tool import ForensicsTriageTool
from config import ForensicsConfig
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Forensics Triage Tool API",
    description="API for performing forensic analysis on systems",
    version="1.0.0"
)

# Pydantic models for request/response
class ScanConfig(BaseModel):
    scan_type: str = Field(..., description="Type of scan to perform", pattern="^(system|network|memory|all)$")
    target: str = Field("192.168.1.0/24", description="Network target for scanning")
    output_dir: Optional[str] = Field(None, description="Custom output directory")
    log_level: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    max_depth: int = Field(3, ge=0, description="Maximum directory depth for system scan")
    timeout: float = Field(2.0, gt=0, description="Network scan timeout in seconds")
    yara_rules_dir: Optional[str] = None

class ScanResults(TypedDict):
    system_results: List[dict]
    network_results: Dict[str, dict]
    memory_results: Dict[str, dict]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/scan", response_model=ScanResults)
async def perform_scan(config: ScanConfig) -> ScanResults:
    try:
        forensics_tool = ForensicsTriageTool(
            config_path=None,
            custom_config={
                'log_level': config.log_level,
                'output_dir': config.output_dir or ForensicsConfig.RESULTS_BASE_DIR,
                'yara_rules_dir': config.yara_rules_dir or ForensicsConfig.YARA_RULES_DIR
            }
        )
        
        system_results: List[dict] = []
        network_results: Dict[str, dict] = {}
        memory_results: Dict[str, dict] = {}
        
        match config.scan_type:
            case 'system' | 'all':
                system_results = await forensics_tool.system_scan(max_depth=config.max_depth)
            case 'network' | 'all':
                network_results = await forensics_tool.network_scan(
                    target=config.target,
                    timeout=config.timeout
                )
            case 'memory' | 'all':
                memory_results = await forensics_tool.memory_analysis()
        
        # Save results
        await forensics_tool.save_results(system_results, network_results, memory_results)
        
        return {
            "system_results": system_results,
            "network_results": network_results,
            "memory_results": memory_results
        }
        
    except Exception as e:
        logger.error(f"Forensics triage failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP error occurred: {exc.detail}")
    return {
        "status": "error",
        "message": exc.detail,
        "status_code": exc.status_code
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unexpected error occurred: {str(exc)}")
    return {
        "status": "error",
        "message": "An unexpected error occurred",
        "status_code": 500
    }

def main():
    """Run the FastAPI application using uvicorn."""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
