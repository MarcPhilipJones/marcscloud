from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
from typing import Any

from .dataverse import DataverseClient, _parse_iso_datetime, _iso, _normalize_guid
from .config import DEFAULT_DEMO_JOB_NAME


@dataclass(frozen=True)
class SchedulingCapabilities:
    has_fps_action: bool
    has_book_resource_scheduling_suggestions: bool


def _state_dir() -> Path:
    # Persist idempotency data locally for demo reliability.
    # Stored under the server package folder to keep paths self-contained.
    base = Path(__file__).resolve().parent.parent.parent  # .../src
    return base / "state"


class _IdempotencyStore:
    def __init__(self, filename: str = "idempotency.json") -> None:
        self._path = _state_dir() / filename
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> dict[str, Any] | None:
        data = self._read_all()
        v = data.get(key)
        return v if isinstance(v, dict) else None

    def put(self, key: str, value: dict[str, Any]) -> None:
        data = self._read_all()
        data[key] = value
        self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _read_all(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            return {}


def _compute_idempotency_key(
    *,
    contact_id: str,
    window_start_utc: datetime,
    window_end_utc: datetime,
    preferred_start_utc: datetime,
    duration_minutes: int,
    priority: str,
) -> str:
    # Stable, human-debuggable idempotency key.
    return "|".join(
        [
            "boiler_repair",
            _normalize_guid(contact_id),
            _iso(window_start_utc),
            _iso(window_end_utc),
            _iso(preferred_start_utc),
            str(int(duration_minutes)),
            (priority or "normal").strip().lower(),
        ]
    )


class FieldServiceSchedulingService:
    def __init__(self, dv: DataverseClient) -> None:
        self._dv = dv
        self._idempotency = _IdempotencyStore()
        self._capabilities: SchedulingCapabilities | None = None

    def probe_capabilities(self) -> SchedulingCapabilities:
        # Lightweight probe: these are the only capabilities we need for the supported pattern.
        # We avoid expensive full metadata parsing.
        if self._capabilities is not None:
            return self._capabilities

        actions = self._dv.try_list_action_names()
        caps = SchedulingCapabilities(
            has_fps_action=("msdyn_FpsAction" in actions),
            has_book_resource_scheduling_suggestions=("msdyn_BookResourceSchedulingSuggestions" in actions),
        )
        self._capabilities = caps
        return caps

    def search_availability_windows(
        self,
        *,
        start_utc: datetime,
        end_utc: datetime,
        duration_minutes: int,
        max_windows: int = 8,
    ) -> dict[str, Any]:
        """Return customer-safe availability windows (no engineer exposure)."""
        raw = self._dv.search_field_service_availability(
            start_utc=start_utc,
            end_utc=end_utc,
            duration_minutes=int(duration_minutes),
            max_time_slots=int(max_windows) * 3,
        )

        # Normalize into windows only; de-dupe by time.
        seen: set[str] = set()
        windows: list[dict[str, Any]] = []
        for s in list(raw.get("slots", [])):
            start = s.get("start")
            end = s.get("end")
            if not isinstance(start, str) or not isinstance(end, str):
                continue
            window_id = f"{start}|{end}"
            if window_id in seen:
                continue
            seen.add(window_id)
            windows.append(
                {
                    "window_id": window_id,
                    "window_start": start,
                    "window_end": end,
                    "display": f"{start} to {end}",
                }
            )
            if 0 < int(max_windows) <= len(windows):
                break

        return {
            "status": raw.get("status", "ok"),
            "action": raw.get("action"),
            "count": len(windows),
            "windows": windows,
            "details": raw.get("details"),
        }

    def schedule_boiler_repair(
        self,
        *,
        contact_id: str,
        window_id: str,
        preferred_start_local: str,
        duration_minutes: int = 120,
        priority: str = "normal",
        create_case: bool = True,
    ) -> dict[str, Any]:
        """Create WO + Requirement and book via supported scheduling actions.

        `window_id` is `windowStartIso|windowEndIso` (UTC or Z-terminated), as returned by search_availability_windows.
        `preferred_start_local` is an ISO datetime in local time, or `HH:MM` (assumed today in Europe/London).
        """

        contact_id = _normalize_guid(contact_id)
        duration_minutes = int(duration_minutes)

        # Parse window bounds
        try:
            w_start_str, w_end_str = window_id.split("|", 1)
            window_start_utc = _parse_iso_datetime(w_start_str)
            window_end_utc = _parse_iso_datetime(w_end_str)
        except Exception as e:
            raise RuntimeError("Invalid window_id. Expected format: <windowStartIso>|<windowEndIso>") from e

        # Convert preferred local time to UTC.
        preferred_start_utc = self._dv.parse_preferred_local_start_to_utc(preferred_start_local)
        preferred_end_utc = preferred_start_utc + timedelta(minutes=duration_minutes)

        # Validate requested appointment fits in the selected availability window.
        if preferred_start_utc < window_start_utc or preferred_end_utc > window_end_utc:
            return {
                "status": "error",
                "message": "Requested appointment time is outside the selected availability window.",
                "window": {"start": _iso(window_start_utc), "end": _iso(window_end_utc)},
                "requested": {"start": _iso(preferred_start_utc), "end": _iso(preferred_end_utc)},
            }

        key = _compute_idempotency_key(
            contact_id=contact_id,
            window_start_utc=window_start_utc,
            window_end_utc=window_end_utc,
            preferred_start_utc=preferred_start_utc,
            duration_minutes=duration_minutes,
            priority=priority,
        )
        existing = self._idempotency.get(key)
        if existing and existing.get("booking", {}).get("id"):
            return {
                "status": "ok",
                "idempotent_replay": True,
                "case": existing.get("case"),
                "work_order": existing.get("work_order"),
                "requirement": existing.get("requirement"),
                "booking": existing.get("booking"),
                "requested": existing.get("requested"),
            }

        # Create or reuse Case/WO/Requirement to avoid duplicates.
        case_id: str | None = None
        work_order_id: str | None = None
        requirement_id: str | None = None

        if existing:
            case_id = (existing.get("case") or {}).get("id")
            work_order_id = (existing.get("work_order") or {}).get("id")
            requirement_id = (existing.get("requirement") or {}).get("id")

        if create_case and not case_id:
            case_id = self._dv.create_case_for_contact(
                contact_id=contact_id,
                title=DEFAULT_DEMO_JOB_NAME,
                description="Customer boiler repair request (presales demo).",
                priority=priority,
                origin="web",
            )

        if not work_order_id:
            work_order_id = self._dv.create_boiler_repair_work_order(
                case_id=case_id,
                priority=priority,
            )

        if not requirement_id:
            requirement_id = self._dv.create_resource_requirement_for_work_order(
                work_order_id=work_order_id,
                window_start_utc=window_start_utc,
                window_end_utc=window_end_utc,
                duration_minutes=duration_minutes,
            )

        # Validate the requested 2-hour block is actually available for this requirement.
        try:
            availability = self._dv.search_field_service_availability(
                start_utc=window_start_utc,
                end_utc=window_end_utc,
                duration_minutes=duration_minutes,
                requirement_id=requirement_id,
                max_time_slots=50,
            )
            slots = list(availability.get("slots", []))
            matches = False
            for s in slots:
                s_start = s.get("start")
                s_end = s.get("end")
                if not isinstance(s_start, str) or not isinstance(s_end, str):
                    continue
                try:
                    if _parse_iso_datetime(s_start) <= preferred_start_utc and _parse_iso_datetime(s_end) >= preferred_end_utc:
                        matches = True
                        break
                except Exception:
                    continue
            if not matches:
                return {
                    "status": "error",
                    "message": "Requested time is not available for this requirement.",
                    "case": {"id": case_id} if case_id else None,
                    "work_order": {"id": work_order_id},
                    "requirement": {"id": requirement_id},
                    "requested": {"start": _iso(preferred_start_utc), "end": _iso(preferred_end_utc)},
                    "window": {"start": _iso(window_start_utc), "end": _iso(window_end_utc)},
                    "availability": {
                        "status": availability.get("status"),
                        "action": availability.get("action"),
                        "count": len(slots),
                    },
                }
        except Exception:
            # If availability check fails, continue; booking may still succeed.
            pass

        # Book via supported scheduling action(s)
        caps = self.probe_capabilities()
        if not (caps.has_fps_action and caps.has_book_resource_scheduling_suggestions):
            return {
                "status": "error",
                "message": "Org missing required scheduling capabilities for supported booking (msdyn_FpsAction + msdyn_BookResourceSchedulingSuggestions).",
                "capabilities": caps.__dict__,
                "case": {"id": case_id} if case_id else None,
                "work_order": {"id": work_order_id},
                "requirement": {"id": requirement_id},
            }

        booking_result = self._dv.book_requirement_via_schedule_assistant(
            requirement_id=requirement_id,
            schedule_start_utc=preferred_start_utc,
            schedule_end_utc=preferred_end_utc,
        )

        out = {
            "status": booking_result.get("status", "ok"),
            "case": {"id": case_id} if case_id else None,
            "work_order": {"id": work_order_id},
            "requirement": {"id": requirement_id},
            "booking": booking_result.get("booking"),
            "requested": {"start": _iso(preferred_start_utc), "end": _iso(preferred_end_utc)},
            "window": {"start": _iso(window_start_utc), "end": _iso(window_end_utc)},
            "customer_friendly": {
                "window_text": f"{_iso(preferred_start_utc)} to {_iso(preferred_end_utc)}",
            },
            "raw": booking_result.get("raw"),
        }

        self._idempotency.put(
            key,
            {
                "case": {"id": case_id} if case_id else None,
                "work_order": {"id": work_order_id},
                "requirement": {"id": requirement_id},
                "booking": booking_result.get("booking"),
                "requested": out["requested"],
                "window": out["window"],
            },
        )
        return out
