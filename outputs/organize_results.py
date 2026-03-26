"""
Organize Results Helper - Utility Functions
===========================================
Helper functions to organize grievance analysis results
and migrate existing results to new folder structure.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OrganizeResultsHelper:
    """Helper class for organizing results."""
    
    @staticmethod
    def migrate_existing_results(
        source_dir: str = ".",
        target_base_dir: str = "outputs/json_results"
    ) -> Dict[str, int]:
        """
        Migrate existing JSON result files to organized folder structure.
        
        Looks for complaint_analysis_*.json files and moves them to appropriate folders.
        
        Args:
            source_dir: Directory containing existing JSON files
            target_base_dir: Root directory for organized outputs
            
        Returns:
            Dictionary with migration statistics
        """
        source_path = Path(source_dir)
        target_path = Path(target_base_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        
        stats = {
            "total_migrated": 0,
            "by_urgency": 0,
            "by_department": 0,
            "by_date": 0,
            "errors": 0
        }
        
        # Find all complaint_analysis_*.json files
        json_files = list(source_path.glob("complaint_analysis_*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract metadata
                urgency = data.get("urgency_level", "MEDIUM")
                department = data.get("routing", {}).get("department", "municipal")
                
                # Create filename
                try:
                    timestamp = datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat()))
                except:
                    timestamp = datetime.utcnow()
                
                session_id = data.get("session_id", json_file.stem)
                timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
                filename = f"{session_id}_{timestamp_str}.json"
                
                # COPY to by_urgency
                urgency_dir = target_path / "by_urgency" / urgency
                urgency_dir.mkdir(parents=True, exist_ok=True)
                urgency_file = urgency_dir / filename
                with open(urgency_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                stats["by_urgency"] += 1
                
                # COPY to by_department
                dept_dir = target_path / "by_department" / department
                dept_dir.mkdir(parents=True, exist_ok=True)
                dept_file = dept_dir / filename
                with open(dept_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                stats["by_department"] += 1
                
                # COPY to by_date
                date_str = timestamp.strftime("%Y/%m/%d")
                date_dir = target_path / "by_date" / date_str
                date_dir.mkdir(parents=True, exist_ok=True)
                date_file = date_dir / filename
                with open(date_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                stats["by_date"] += 1
                
                stats["total_migrated"] += 1
                logger.info(f"✅ Migrated: {json_file.name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to migrate {json_file.name}: {e}")
                stats["errors"] += 1
        
        return stats
