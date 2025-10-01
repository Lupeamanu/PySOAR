""" Case management system for PySOAR """

import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent))

from models.case import Case, Status, Severity


class CaseManager:
    """ Manages security cases and incidents """

    def __init__(self, db_path: str = "data/pysoar.db"):
        self.db_path = db_path
        self._ensure_database()


    def _ensure_database(self):
        """ Create database and tables if they don't exist """
        # Create data directory if it doesn't exist
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create cases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                severity TEXT,
                status TEXT,
                assigned_to TEXT,
                tags TEXT,
                created_at TEXT,
                updated_at TEXT,
                closed_at TEXT,
                artifacts TEXT,
                events TEXT,
                playbooks_executed TEXT
            )
        """)

        conn.commit()
        conn.close()


    def create_case(
        self,
        title: str,
        description: str = "",
        severity: str = Severity.MEDIUM.value,
        tags: List[str] = None # type: ignore
    ) -> Case:
        """ Create a new case """
        case = Case(
            title=title,
            description=description,
            severity=severity,
            tags=tags or []
        )

        self._save_case(case)
        return case


    def get_case(self, case_id: str) -> Optional[Case]:
        """ Get a case by ID """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_case(row)
        return None


    def list_cases(self, status: str = None, severity: str = None, limit: int = 100) -> List[Case]: # type: ignore
        """ List cases with optional filters """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM cases WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if severity:
            query += " AND severity = ?"
            params.append(severity)

        query += " ORDER BY created_by DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_case(row) for row in rows]


    def update_case(self, case: Case):
        """ Update an existing case """
        case.updated_at = datetime.now()
        self._save_case(case)


    def delete_case(self, case_id: str) -> bool:
        """ Delete a case """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM cases WHERE id = ?", (case_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted


    def search_cases(self, query: str) -> List[Case]:
        """ Search cases by title or description """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        search_pattern = f"%{query}%"
        cursor.execute("""
            SELECT * FROM cases
            WHERE title LIKE ? OR description LIKE ?
            ORDER BY created_at DESC
        """, (search_pattern, search_pattern))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_case(row) for row in rows]


    def get_statistics(self) -> Dict[str, Any]:
        """ Get case statistics """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total cases
        cursor.execute("SELECT COUNT(*) FROM cases")
        total = cursor.fetchone()[0]

        # By status
        cursor.execute("""
            SELECT status, COUNT(*)
            FROM cases
            GROUP BY status
        """)
        by_status = dict(cursor.fetchall())

        # By severity
        cursor.execute("""
            SELECT severity, COUNT(*)
            FROM cases
            GROUP BY severity
        """)
        by_severity = dict(cursor.fetchall())

        # Open cases
        cursor.execute("""
            SELECT COUNT(*) FROM cases
            WHERE status IN ('open', 'investigating')
        """)
        open_cases = cursor.fetchone()[0]

        conn.close()

        return {
            "total": total,
            "open": open_cases,
            "by_status": by_status,
            "by_severity": by_severity
        }


    def _save_case(self, case: Case):
        """ Save case to database """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO cases
            (id, title, description, severity, status, assigned_to, tags,
            created_at, updated_at, closed_at, artifacts, events, playbooks_executed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case.id,
            case.title,
            case.description,
            case.severity,
            case.status,
            case.assigned_to,
            json.dumps(case.tags),
            case.created_at.isoformat(),
            case.updated_at.isoformat(),
            case.closed_at.isoformat() if case.closed_at else None,
            json.dumps([a.to_dict() for a in case.artifacts]),
            json.dumps([e.to_dict() for e in case.events]),
            json.dumps(case.playbooks_executed)
        ))

        conn.commit()
        conn.close()


    def _row_to_case(self, row) -> Case:
        """ Convert database row to Case object """
        data = {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "severity": row[3],
            "status": row[4],
            "assigned_to": row[5],
            "tags": json.loads(row[6]) if row[6] else [],
            "created_at": row[7],
            "updated_at": row[8],
            "closed_at": row[9],
            "artifacts": json.loads(row[10]) if row[10] else [],
            "events": json.loads(row[11]) if row[11] else [],
            "playbooks_executed": json.loads(row[12]) if row[12] else []
        }

        return Case.from_dict(data)