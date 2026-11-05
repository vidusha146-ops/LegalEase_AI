"""
LegalEase AI - Chronological Timeline Engine (Phase 5)
Constructs incident timelines from extracted evidence and citizen inputs,
sorts events chronologically, detects temporal gaps, and supports manual corrections.
"""

from typing import Dict, Any, List, Optional
from datetime import date, datetime


class ChronologicalTimelineEngine:
    """
    Synthesizes extracted procedural events from all uploaded evidence documents
    into a structured, traceable chronological timeline with gap detection.
    """

    @classmethod
    def build_timeline(
        cls,
        document_events: List[Dict[str, Any]],
        manual_events: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Combines automated events from documents with manual citizen events,
        normalizes dates, sorts chronologically, and checks for sequence anomalies.
        """
        all_events: List[Dict[str, Any]] = []

        # 1. Process document extracted events
        for ev in document_events:
            all_events.append({
                "id": ev.get("id"),
                "event_date": ev.get("date") or ev.get("event_date") or "UNDATED",
                "title": ev.get("title") or ev.get("event_title") or "Legal Incident Event",
                "description": ev.get("description") or ev.get("evidence_snippet") or "",
                "source_document": ev.get("source_document"),
                "page_number": ev.get("page_number"),
                "evidence_id": ev.get("evidence_id"),
                "confidence_level": ev.get("confidence") or ev.get("confidence_level") or "HIGH",
                "is_manual": False,
            })

        # 2. Process manual events
        if manual_events:
            for mev in manual_events:
                all_events.append({
                    "id": mev.get("id"),
                    "event_date": mev.get("event_date") or "UNDATED",
                    "title": mev.get("event_title") or mev.get("title") or "Manual Event",
                    "description": mev.get("event_description") or mev.get("description") or "",
                    "source_document": mev.get("source_reference") or "Citizen Statement",
                    "page_number": None,
                    "evidence_id": mev.get("evidence_id"),
                    "confidence_level": mev.get("confidence_level", "HIGH"),
                    "is_manual": True,
                })

        # 3. Partition into dated and undated events
        dated_events: List[Dict[str, Any]] = []
        undated_events: List[Dict[str, Any]] = []

        for ev in all_events:
            parsed_dt = cls._parse_iso_date(ev["event_date"])
            if parsed_dt:
                ev["parsed_date"] = parsed_dt
                dated_events.append(ev)
            else:
                ev["parsed_date"] = None
                undated_events.append(ev)

        # 4. Sort dated events in ascending order
        dated_events.sort(key=lambda x: x["parsed_date"])

        # 5. Detect temporal intervals and sequence gaps
        sequence_warnings = []
        for i in range(len(dated_events) - 1):
            curr_ev = dated_events[i]
            next_ev = dated_events[i + 1]
            diff_days = (next_ev["parsed_date"] - curr_ev["parsed_date"]).days

            # Flag large temporal gap (> 90 days) between active dispute steps
            if diff_days > 90:
                sequence_warnings.append({
                    "type": "EXTENDED_TEMPORAL_GAP",
                    "gap_days": diff_days,
                    "from_event": curr_ev["title"],
                    "to_event": next_ev["title"],
                    "advisory": (
                        f"A gap of {diff_days} days detected between '{curr_ev['title']}' ({curr_ev['event_date']}) "
                        f"and '{next_ev['title']}' ({next_ev['event_date']}). Check for limitation periods under Indian law."
                    ),
                })

        # Remove parsed_date objects before JSON serialization
        sorted_events = []
        seq_num = 1
        for ev in dated_events:
            ev["sequence_number"] = seq_num
            del ev["parsed_date"]
            sorted_events.append(ev)
            seq_num += 1

        for ev in undated_events:
            ev["sequence_number"] = None
            if "parsed_date" in ev:
                del ev["parsed_date"]

        # Date range summary
        earliest_date = sorted_events[0]["event_date"] if sorted_events else None
        latest_date = sorted_events[-1]["event_date"] if sorted_events else None

        return {
            "total_events": len(all_events),
            "dated_events_count": len(sorted_events),
            "undated_events_count": len(undated_events),
            "earliest_date": earliest_date,
            "latest_date": latest_date,
            "chronological_events": sorted_events,
            "undated_events": undated_events,
            "temporal_warnings": sequence_warnings,
        }

    @classmethod
    def _parse_iso_date(cls, date_str: Optional[str]) -> Optional[date]:
        """Parses a date string into a date object."""
        if not date_str or date_str in ("UNDATED", "UNDATED_OR_PENDING"):
            return None
        try:
            return date.fromisoformat(date_str.strip()[:10])
        except Exception:
            return None
