#!/usr/bin/env python3
"""
DATABASE ROUTING MODULE
=======================
Routes complaints to appropriate departments and saves to Neon DB.

Features:
- Connects to Neon PostgreSQL database
- Routes complaints based on urgency, keywords, and language
- Saves complaint records with department assignment
- Handles database connection pooling
- Provides fallback for offline mode
"""

import os
import logging
import json
from typing import Optional, Dict, Tuple
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

DB_AVAILABLE = False
DB_CONNECTION = None

try:
    import psycopg2
    from psycopg2.pool import SimpleConnectionPool
    from psycopg2.extras import RealDictCursor
    DB_AVAILABLE = True
except ImportError:
    logger.warning("psycopg2 not installed. Install with: pip install psycopg2-binary")


def get_db_connection():
    """Get database connection from environment variables."""
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        # Try building from individual components
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        
        if all([db_host, db_name, db_user, db_password]):
            db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"
        else:
            logger.warning("DATABASE_URL or DB_* environment variables not configured")
            return None
    
    try:
        conn = psycopg2.connect(db_url)
        logger.info("✓ Connected to Neon Database")
        return conn
    except psycopg2.Error as e:
        logger.error(f"✗ Database connection failed: {e}")
        return None


def init_database():
    """Initialize database tables if they don't exist."""
    if not DB_AVAILABLE:
        logger.warning("psycopg2 not available, skipping database initialization")
        return False
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create main complaints table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(13) UNIQUE NOT NULL,
                transcript TEXT NOT NULL,
                language_code VARCHAR(10),
                language_name VARCHAR(50),
                urgency_level VARCHAR(10),
                urgency_score INT,
                keywords TEXT[],
                department_assigned VARCHAR(50),
                department_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create complaint logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaint_logs (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(13) NOT NULL REFERENCES complaints(session_id),
                action VARCHAR(255),
                status VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES complaints(session_id)
            );
        """)
        
        # Create department routing table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaint_routes (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(13) NOT NULL UNIQUE,
                department VARCHAR(50),
                priority INT,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                routed_to_url TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                FOREIGN KEY (session_id) REFERENCES complaints(session_id)
            );
        """)
        
        conn.commit()
        cursor.close()
        logger.info("✓ Database tables initialized")
        return True
    
    except psycopg2.Error as e:
        logger.error(f"✗ Database initialization failed: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()


# ============================================================================
# DEPARTMENT ROUTING LOGIC
# ============================================================================

DEPARTMENT_KEYWORDS = {
    "fire": {
        "keywords": ["aag", "आग", "fire", "blaze", "flame", "explosion", "burn", "smoke"],
        "urgency": "CRITICAL",
        "priority": 1,
    },
    "police": {
        "keywords": ["theft", "robbery", "crime", "attack", "accident", "police", "चोरी", "डाका", "अपराध"],
        "urgency": ["CRITICAL", "HIGH"],
        "priority": 2,
    },
    "health": {
        "keywords": ["ambulance", "hospital", "illness", "sick", "injury", "medical", "doctor", "चिकित्सा", "बीमार"],
        "urgency": ["HIGH", "MEDIUM"],
        "priority": 3,
    },
    "water": {
        "keywords": ["water", "pani", "drain", "flood", "pipeline", "leakage", "पानी", "नाली"],
        "urgency": ["MEDIUM", "LOW"],
        "priority": 4,
    },
    "electricity": {
        "keywords": ["electricity", "power", "bijli", "blackout", "outage", "short circuit", "बिजली"],
        "urgency": ["MEDIUM", "LOW"],
        "priority": 4,
    },
}


def route_complaint(
    transcript: str,
    urgency: str,
    keywords: list,
    language: str = "en",
) -> Dict:
    """
    Route complaint to appropriate department based on keywords and urgency.
    
    Returns:
        Dict with routing info: {department, priority, confidence}
    """
    
    # Score each department based on keyword matches
    department_scores = {}
    
    for dept, config in DEPARTMENT_KEYWORDS.items():
        score = 0
        matches = []
        
        # Count keyword matches
        for keyword in config["keywords"]:
            if keyword.lower() in transcript.lower():
                score += 1
                matches.append(keyword)
        
        if score > 0:
            department_scores[dept] = {
                "score": score,
                "matches": list(set(matches)),
                "priority": config["priority"],
                "config_urgency": config["urgency"],
            }
    
    # If no matches, assign to general
    if not department_scores:
        logger.info(f"No department matches found, assigning to GENERAL")
        return {
            "department": "general",
            "priority": 5,
            "confidence": 0,
            "matched_keywords": [],
            "reasoning": "No specific department keywords matched"
        }
    
    # Get best match (highest score)
    best_dept = max(department_scores.items(), key=lambda x: x[1]["score"])
    dept_name = best_dept[0]
    dept_info = best_dept[1]
    
    # Calculate confidence (0-100)
    confidence = min(100, (dept_info["score"] / len(DEPARTMENT_KEYWORDS[dept_name]["keywords"])) * 100)
    
    logger.info(f"Routed to: {dept_name.upper()} (score: {dept_info['score']}, confidence: {confidence:.1f}%)")
    
    return {
        "department": dept_name,
        "priority": dept_info["priority"],
        "confidence": confidence,
        "matched_keywords": dept_info["matches"],
        "reasoning": f"Matched {len(dept_info['matches'])} keywords: {', '.join(dept_info['matches'][:3])}"
    }


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def save_complaint_to_db(
    session_id: str,
    transcript: str,
    language_code: str,
    urgency_level: str,
    keywords: list,
    routing_info: Dict,
) -> bool:
    """Save complaint record to database with department assignment."""
    
    if not DB_AVAILABLE:
        logger.warning("Database not available, complaint not saved to DB")
        return False
    
    conn = get_db_connection()
    if not conn:
        logger.warning("Could not connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Determine urgency score
        urgency_score = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(urgency_level, 0)
        
        # Get language name
        from unified_stt_service import format_language
        language_name = format_language(language_code)
        
        # Insert complaint
        cursor.execute("""
            INSERT INTO complaints 
            (session_id, transcript, language_code, language_name, urgency_level, 
             urgency_score, keywords, department_assigned, department_confidence, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_id) DO UPDATE
            SET updated_at = CURRENT_TIMESTAMP
        """, (
            session_id,
            transcript,
            language_code,
            language_name,
            urgency_level,
            urgency_score,
            keywords,  # PostgreSQL array
            routing_info.get("department", "general"),
            routing_info.get("confidence", 0),
            datetime.utcnow()
        ))
        
        # Insert routing info
        cursor.execute("""
            INSERT INTO complaint_routes
            (session_id, department, route_confidence, routing_keywords, routed_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (
            session_id,
            routing_info.get("department", "general"),
            routing_info.get("confidence", 0),
            str(routing_info.get("matched_keywords", [])),
            datetime.utcnow()
        ))
        
        # Log action
        cursor.execute("""
            INSERT INTO complaint_logs
            (session_id, action, status)
            VALUES (%s, %s, %s)
        """, (
            session_id,
            f"Routed to {routing_info.get('department', 'general')} with confidence {routing_info.get('confidence', 0):.1f}%",
            "routed"
        ))
        
        conn.commit()
        cursor.close()
        logger.info(f"✓ Complaint {session_id} saved to database")
        return True
    
    except psycopg2.Error as e:
        logger.error(f"✗ Error saving complaint: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()


def get_complaint_status(session_id: str) -> Optional[Dict]:
    """Get complaint status from database."""
    
    if not DB_AVAILABLE:
        return None
    
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT c.*, cr.department, cr.priority, cr.status
            FROM complaints c
            LEFT JOIN complaint_routes cr ON c.session_id = cr.session_id
            WHERE c.session_id = %s
        """, (session_id,))
        
        result = cursor.fetchone()
        cursor.close()
        return dict(result) if result else None
    
    except psycopg2.Error as e:
        logger.error(f"Error fetching complaint: {e}")
        return None
    
    finally:
        conn.close()


def get_db_status() -> Dict:
    """Get database connection status."""
    
    if not DB_AVAILABLE:
        return {"status": "unavailable", "reason": "psycopg2 not installed"}
    
    conn = get_db_connection()
    if conn:
        conn.close()
        return {"status": "connected"}
    else:
        return {"status": "disconnected", "reason": "Could not connect to Neon DB"}


# ============================================================================
# INITIALIZATION
# ============================================================================

def init_routing():
    """Initialize database routing system."""
    logger.info("Initializing database routing system...")
    
    if not DB_AVAILABLE:
        logger.warning("psycopg2 not available - database support disabled")
        return False
    
    # Try to initialize database
    if init_database():
        logger.info("✓ Database routing system ready")
        return True
    else:
        logger.warning("⚠️  Database initialization failed - running in offline mode")
        return False
