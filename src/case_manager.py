"""
NetSage AI - Case Manager & Review State Store
Handles dataset loading, filtering, human review auditing, and persistence to disk.
Supports live dynamic updating of both review_log.csv and responsible_ai_log.csv.
"""

import os
import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional

class CaseManager:
    def __init__(self, base_dir: Optional[str] = None):
        if not base_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = base_dir
        self.data_dir = os.path.join(base_dir, "data")
        self.cases_file = os.path.join(self.data_dir, "cases.json")
        self.review_log_file = os.path.join(self.data_dir, "review_log.csv")
        self.responsible_log_file = os.path.join(self.data_dir, "responsible_ai_log.csv")
        self.cases = []
        self.reviews = {}
        self.load_cases()
        self.load_reviews()

    def load_cases(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.cases_file):
            with open(self.cases_file, "r", encoding="utf-8") as f:
                self.cases = json.load(f)
        else:
            from src.cases_data import CASES
            self.cases = CASES
        return self.cases

    def get_case_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        for c in self.cases:
            if c["case_id"] == case_id:
                return c
        return None

    def filter_cases(self, concept: Optional[str] = None, layer: Optional[str] = None, severity: Optional[str] = None, search_term: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self.cases
        if concept and concept != "All":
            results = [c for c in results if c.get("concept_tag") == concept]
        if layer and layer != "All":
            results = [c for c in results if c.get("osi_layer") == layer]
        if severity and severity != "All":
            results = [c for c in results if c.get("severity") == severity]
        if search_term:
            term = search_term.lower()
            results = [
                c for c in results
                if term in c["case_id"].lower()
                or term in c["title"].lower()
                or term in c["symptom"].lower()
                or term in c["expected_fault"].lower()
            ]
        return results

    def load_reviews(self) -> Dict[str, Dict[str, Any]]:
        self.reviews = {}
        if os.path.exists(self.review_log_file):
            with open(self.review_log_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.reviews[row["case_id"]] = row
        return self.reviews

    def submit_review(
        self, 
        case_id: str, 
        verdict: str, 
        reviewer: str, 
        comments: str, 
        edited_root_cause: str = "", 
        edited_fix: str = "",
        title: str = "",
        symptom: str = "",
        ai_output_cause: str = "",
        ai_proposed_fix: str = "",
        failure_category: str = "Human Review Override"
    ) -> Dict[str, Any]:
        """
        Records human review verdict: Accepted, Edited, or Rejected.
        Dynamically updates both review_log.csv and responsible_ai_log.csv.
        """
        now = datetime.now().isoformat()
        record = {
            "case_id": case_id,
            "verdict": verdict,
            "reviewer": reviewer or "Senior Network Engineer",
            "reviewed_at": now,
            "comments": comments,
            "edited_root_cause": edited_root_cause,
            "edited_fix": edited_fix
        }
        self.reviews[case_id] = record
        self._persist_reviews()

        # If the verdict is Rejected or Edited, also dynamically log/update in responsible_ai_log.csv
        if verdict in ["Rejected", "Edited"]:
            self._log_responsible_ai_incident(
                case_id=case_id,
                title=title or f"Custom Troubleshooting Incident ({case_id})",
                symptom=symptom or "Custom scenario symptom",
                ai_output_cause=ai_output_cause or "AI diagnosed root cause",
                ai_proposed_fix=ai_proposed_fix or "AI proposed fix commands",
                failure_category=failure_category,
                human_correction=edited_root_cause or comments,
                correct_fix=edited_fix,
                responsible_ai_lesson=f"Reviewer override by {reviewer}: {comments}"
            )

        return record

    def _persist_reviews(self):
        fieldnames = ["case_id", "verdict", "reviewer", "reviewed_at", "comments", "edited_root_cause", "edited_fix"]
        with open(self.review_log_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in self.reviews.values():
                writer.writerow(r)

    def _log_responsible_ai_incident(self, case_id, title, symptom, ai_output_cause, ai_proposed_fix, failure_category, human_correction, correct_fix, responsible_ai_lesson):
        """Appends or updates an incident entry in responsible_ai_log.csv."""
        fieldnames = [
            "case_id", "title", "symptom", "ai_output_cause", "ai_proposed_fix",
            "failure_category", "human_correction", "correct_fix", "responsible_ai_lesson"
        ]
        
        existing_rows = []
        if os.path.exists(self.responsible_log_file):
            with open(self.responsible_log_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                existing_rows = list(reader)
                
        # Update existing or append new
        updated = False
        new_row = {
            "case_id": case_id,
            "title": title,
            "symptom": symptom,
            "ai_output_cause": ai_output_cause,
            "ai_proposed_fix": ai_proposed_fix,
            "failure_category": failure_category,
            "human_correction": human_correction,
            "correct_fix": correct_fix,
            "responsible_ai_lesson": responsible_ai_lesson
        }
        
        for i, row in enumerate(existing_rows):
            if row.get("case_id") == case_id:
                existing_rows[i] = new_row
                updated = True
                break
                
        if not updated:
            existing_rows.append(new_row)
            
        with open(self.responsible_log_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in existing_rows:
                writer.writerow(row)

    def get_review_stats(self) -> Dict[str, Any]:
        total_cases = len(self.cases)
        total_reviewed = len(self.reviews)
        accepted = sum(1 for r in self.reviews.values() if r["verdict"] == "Accepted")
        edited = sum(1 for r in self.reviews.values() if r["verdict"] == "Edited")
        rejected = sum(1 for r in self.reviews.values() if r["verdict"] == "Rejected")
        pending = max(0, total_cases - total_reviewed)
        
        agreement_rate = (accepted / total_reviewed * 100) if total_reviewed > 0 else 0.0
        
        return {
            "total_cases": total_cases,
            "total_reviewed": total_reviewed,
            "accepted": accepted,
            "edited": edited,
            "rejected": rejected,
            "pending": pending,
            "agreement_rate": round(agreement_rate, 1)
        }

if __name__ == "__main__":
    mgr = CaseManager()
    print(f"Loaded {len(mgr.cases)} cases.")
    print("Review Stats:", mgr.get_review_stats())