"""
JSON Storage Manager - Organized Result Storage
================================================
Saves grievance analysis results to organized folder structure:
- by_urgency/{CRITICAL,HIGH,MEDIUM,LOW}/
- by_department/{fire,police,electricity,water,gas,municipal}/
- by_date/{YYYY-MM-DD}/
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class JSONStorageManager:
    """Manages organized storage of grievance analysis results."""
    
    def __init__(self, base_output_dir: str = "outputs/json_results"):
        """
        Initialize storage manager.
        
        Args:
            base_output_dir: Root directory for organized outputs
        """
        self.base_dir = Path(base_output_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure subdirectories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create all required subdirectories."""
        # By urgency
        for urgency in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            (self.base_dir / "by_urgency" / urgency).mkdir(parents=True, exist_ok=True)
        
        # By department
        for dept in ["fire", "police", "electricity", "water", "gas", "municipal"]:
            (self.base_dir / "by_department" / dept).mkdir(parents=True, exist_ok=True)
        
        # By date (YYYY-MM-DD structure)
        (self.base_dir / "by_date").mkdir(parents=True, exist_ok=True)
    
    def save_result(
        self,
        session_id: str,
        result: Dict[str, Any],
        urgency_level: str = "MEDIUM",
        department: str = "municipal",
        timestamp: Optional[datetime] = None,
    ) -> Dict[str, str]:
        """
        Save grievance result to multiple organized locations.
        
        Args:
            session_id: Unique grievance identifier
            result: Analysis result dictionary
            urgency_level: CRITICAL, HIGH, MEDIUM, or LOW
            department: fire, police, electricity, water, gas, municipal
            timestamp: When the grievance was filed
            
        Returns:
            Dictionary with file paths where result was saved
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Create filename with timestamp
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"{session_id}_{timestamp_str}.json"
        
        saved_paths = {}
        
        # 1. SAVE BY URGENCY
        urgency_path = self.base_dir / "by_urgency" / urgency_level / filename
        self._save_json(urgency_path, result)
        saved_paths["by_urgency"] = str(urgency_path)
        
        # 2. SAVE BY DEPARTMENT
        dept_path = self.base_dir / "by_department" / department / filename
        self._save_json(dept_path, result)
        saved_paths["by_department"] = str(dept_path)
        
        # 3. SAVE BY DATE (YYYY/MM/DD structure)
        date_str = timestamp.strftime("%Y/%m/%d")
        date_dir = self.base_dir / "by_date" / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        date_path = date_dir / filename
        self._save_json(date_path, result)
        saved_paths["by_date"] = str(date_path)
        
        logger.info(f"✅ Saved result for {session_id} to 3 locations")
        return saved_paths
    
    def _save_json(self, filepath: Path, data: Dict[str, Any]):
        """Save JSON to file with error handling."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved: {filepath}")
        except Exception as e:
            logger.error(f"❌ Failed to save {filepath}: {e}")
            raise
    
    def get_results_by_urgency(self, urgency_level: str) -> list:
        """Get all results for specific urgency level."""
        urgency_dir = self.base_dir / "by_urgency" / urgency_level
        if not urgency_dir.exists():
            return []
        
        results = []
        for json_file in urgency_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    results.append(json.load(f))
            except Exception as e:
                logger.error(f"Failed to read {json_file}: {e}")
        
        return results
    
    def get_results_by_department(self, department: str) -> list:
        """Get all results for specific department."""
        dept_dir = self.base_dir / "by_department" / department
        if not dept_dir.exists():
            return []
        
        results = []
        for json_file in dept_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    results.append(json.load(f))
            except Exception as e:
                logger.error(f"Failed to read {json_file}: {e}")
        
        return results
    
    def get_results_by_date(self, year: int, month: int, day: int) -> list:
        """Get all results for specific date."""
        date_dir = self.base_dir / "by_date" / f"{year:04d}/{month:02d}/{day:02d}"
        if not date_dir.exists():
            return []
        
        results = []
        for json_file in date_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    results.append(json.load(f))
            except Exception as e:
                logger.error(f"Failed to read {json_file}: {e}")
        
        return results
    
    def get_result_by_session(self, session_id: str) -> Optional[Dict]:
        """Find and retrieve result by session ID (searches all locations)."""
        # Search in all urgency levels
        for urgency in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            urgency_dir = self.base_dir / "by_urgency" / urgency
            for json_file in urgency_dir.glob(f"{session_id}*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Failed to read {json_file}: {e}")
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored results."""
        stats = {
            "by_urgency": {},
            "by_department": {},
            "total": 0
        }
        
        # Count by urgency
        for urgency in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            urgency_dir = self.base_dir / "by_urgency" / urgency
            count = len(list(urgency_dir.glob("*.json")))
            stats["by_urgency"][urgency] = count
            stats["total"] += count
        
        # Count by department
        for dept in ["fire", "police", "electricity", "water", "gas", "municipal"]:
            dept_dir = self.base_dir / "by_department" / dept
            count = len(list(dept_dir.glob("*.json")))
            stats["by_department"][dept] = count
        
        return stats
