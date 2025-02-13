"""FastAPI web interface for the Digital Forensics Triage Tool."""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from services.forensics_scanner import ForensicsScanner
from config.config_manager import ConfigManager
from utils.logging_config import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Digital Forensics Triage Tool",
    description="Web interface for digital forensics analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Temporary upload directory
upload_dir = Path(__file__).parent / "uploads"
upload_dir.mkdir(exist_ok=True)

# Results directory
results_dir = Path(__file__).parent / "results"
results_dir.mkdir(exist_ok=True)

class ScanManager:
    """Manages forensic scans and their status."""
    
    def __init__(self):
        self.scans: Dict[str, Dict[str, Any]] = {}
        
    def create_scan(self, directory: Path) -> str:
        """Create a new scan job."""
        scan_id = str(uuid.uuid4())
        self.scans[scan_id] = {
            'status': 'pending',
            'directory': str(directory),
            'created': datetime.now().isoformat(),
            'completed': None,
            'result_file': None,
            'error': None
        }
        return scan_id
        
    def update_scan(self, scan_id: str, **kwargs) -> None:
        """Update scan status."""
        if scan_id in self.scans:
            self.scans[scan_id].update(kwargs)
            
    def get_scan(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get scan status."""
        return self.scans.get(scan_id)

scan_manager = ScanManager()

async def process_scan(scan_id: str, directory: Path):
    """Process a scan in the background."""
    try:
        scanner = ForensicsScanner(str(directory))
        results = scanner.scan()
        
        # Save results
        result_file = results_dir / f"scan_{scan_id}.json"
        scanner.save_results(results, str(result_file))
        
        scan_manager.update_scan(
            scan_id,
            status='completed',
            completed=datetime.now().isoformat(),
            result_file=str(result_file)
        )
        
    except Exception as e:
        logger.error(f"Error processing scan {scan_id}: {e}", exc_info=True)
        scan_manager.update_scan(
            scan_id,
            status='error',
            error=str(e),
            completed=datetime.now().isoformat()
        )
        
    finally:
        # Cleanup upload directory
        if directory.exists() and directory.is_dir():
            shutil.rmtree(directory)

@app.post("/api/scan/upload")
async def upload_for_scan(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
) -> JSONResponse:
    """Handle file upload and initiate scan."""
    try:
        # Create unique directory for this upload
        upload_path = upload_dir / str(uuid.uuid4())
        upload_path.mkdir(parents=True)
        
        # Save uploaded file
        file_path = upload_path / file.filename
        with file_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
            
        # Create scan job
        scan_id = scan_manager.create_scan(upload_path)
        
        # Start processing in background
        background_tasks.add_task(process_scan, scan_id, upload_path)
        
        return JSONResponse({
            'scan_id': scan_id,
            'status': 'pending',
            'message': 'Scan initiated'
        })
        
    except Exception as e:
        logger.error(f"Error handling upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scan/{scan_id}")
async def get_scan_status(scan_id: str) -> JSONResponse:
    """Get status of a scan."""
    scan = scan_manager.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return JSONResponse(scan)

@app.get("/api/scan/{scan_id}/results")
async def get_scan_results(scan_id: str) -> FileResponse:
    """Download scan results."""
    scan = scan_manager.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
        
    if scan['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Scan not completed")
        
    result_file = Path(scan['result_file'])
    if not result_file.exists():
        raise HTTPException(status_code=404, detail="Result file not found")
        
    return FileResponse(
        result_file,
        media_type='application/json',
        filename=f'scan_results_{scan_id}.json'
    )

@app.get("/api/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })
