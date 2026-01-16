from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import threading
from typing import Any

from zoneinfo import ZoneInfo

from .config import DEFAULT_DEMO_JOB_NAME, DEFAULT_DEMO_RESOURCE_NAME
from .dataverse import DataverseClient, _iso, _normalize_guid, _parse_iso_datetime


@dataclass(frozen=True)
class SchedulingCapabilities:
    has_search_resource_availability_v2: bool
    has_requirement_group_availability: bool
    has_fps_action: bool
    has_book_resource_scheduling_suggestions: bool

    @property
    def can_search_availability(self) -> bool:
        return self.has_search_resource_availability_v2 or self.has_requirement_group_availability or self.has_fps_action

    @property
    def can_book_requirement(self) -> bool:
        # Supported booking path in this repo is the Schedule Board pipeline.
        return self.has_fps_action and self.has_book_resource_scheduling_suggestions


def _state_dir() -> Path:
    # mcp-dataverse-server/state
    base = Path(__file__).resolve().parent.parent.parent
    return base / "state"


class _IdempotencyStore:
    def __init__(self, filename: str = "idempotency.customer-self-service.v2.json") -> None:
        self._path = _state_dir() / filename
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def get(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            data = self._read_all_unlocked()
            v = data.get(key)
            return v if isinstance(v, dict) else None

    def put(self, key: str, value: dict[str, Any]) -> None:
        with self._lock:
            data = self._read_all_unlocked()
            data[key] = value
            tmp = self._path.with_suffix(self._path.suffix + ".tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self._path)

    def clear(self) -> None:
        with self._lock:
            try:
                if self._path.exists():
                    self._path.unlink()
            except Exception:
                # Best-effort: cache clearing should never block startup.
                pass

    def _read_all_unlocked(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            return {}


def _compute_idempotency_key(
    *,
    environment_id: str,
    contact_id: str,
    window_start_utc: datetime,
    window_end_utc: datetime,
    preferred_start_utc: datetime,
    duration_minutes: int,
    scenario: str,
) -> str:
    # Stable, human-debuggable idempotency key.
    return "|".join(
        [
            (environment_id or "").strip().lower(),
            (scenario or "field_service").strip().lower(),
            _normalize_guid(contact_id),
            _iso(window_start_utc),
            _iso(window_end_utc),
            _iso(preferred_start_utc),
            str(int(duration_minutes)),
        ]
    )


class CustomerSelfServiceSchedulingService:
    """Supported Field Service self-scheduling pattern.

    Implements:
    - createWorkOrder()
    - searchAvailability(requirement, window)
    - bookRequirement(requirement, chosenSlot)

    Notes:
    - Availability is returned as discrete duration-fitting START slots.
    - Engineers/resources are not returned for availability, but booking confirmation may include the assigned resource.
    """

    def __init__(
        self,
        dv: DataverseClient,
        demo_bookable_resource_id: str | None = None,
        *,
        demo_resource_name: str = DEFAULT_DEMO_RESOURCE_NAME,
        demo_job_name: str = DEFAULT_DEMO_JOB_NAME,
        demo_fast: bool = True,
        clear_demo_caches_on_start: bool = True,
    ) -> None:
        self._dv = dv
        self._idempotency = _IdempotencyStore()
        self._caps: SchedulingCapabilities | None = None

        self._demo_bookable_resource_id = (
            _normalize_guid(demo_bookable_resource_id) if isinstance(demo_bookable_resource_id, str) and demo_bookable_resource_id.strip() else None
        )

        self._demo_resource_name = (demo_resource_name or DEFAULT_DEMO_RESOURCE_NAME).strip() or DEFAULT_DEMO_RESOURCE_NAME
        self._demo_job_name = (demo_job_name or DEFAULT_DEMO_JOB_NAME).strip() or DEFAULT_DEMO_JOB_NAME
        self._demo_fast = bool(demo_fast)

        if self._demo_fast and bool(clear_demo_caches_on_start):
            # Clear file-backed booking idempotency cache on each server start.
            # This keeps demos from "replaying" older bookings across sessions.
            self._idempotency.clear()

        # Presales demo optimization: cache availability for a short period.
        # Single-user flows often re-ask the same question (“earliest slot”, “today/tomorrow”, etc.).
        self._availability_cache: dict[tuple[str, str, str, int, int], tuple[float, dict[str, Any]]] = {}
        self._availability_cache_lock = threading.Lock()

        # Default characteristic (skill) applied to boiler repair requirements when present in the org.
        self._boiler_characteristic_name = "Boiler Heating Household Specialist"

    def probe_capabilities(self) -> SchedulingCapabilities:
        if self._caps is not None:
            return self._caps

        # Small probe: check only the actions we need.
        has_v2 = self._dv.probe_unbound_action_exists("msdyn_SearchResourceAvailabilityV2")
        has_req_group = self._dv.probe_unbound_action_exists("msdyn_SearchResourceAvailabilityForRequirementGroup")
        has_fps = self._dv.probe_unbound_action_exists("msdyn_FpsAction")
        has_book = self._dv.probe_unbound_action_exists("msdyn_BookResourceSchedulingSuggestions")

        self._caps = SchedulingCapabilities(
            has_search_resource_availability_v2=has_v2,
            has_requirement_group_availability=has_req_group,
            has_fps_action=has_fps,
            has_book_resource_scheduling_suggestions=has_book,
        )
        return self._caps

    def create_work_order(self, *, case_id: str | None, priority: str = "normal") -> str:
        # For this repo/demo we keep the Work Order creation centralized in DataverseClient.
        return self._dv.create_boiler_repair_work_order(case_id=case_id, priority=priority)

    def _get_or_wait_for_requirement_id_for_work_order(self, *, work_order_id: str) -> tuple[str | None, list[dict[str, Any]]]:
        # Many orgs auto-create a requirement when a work order is created.
        # Poll briefly because that creation can be async.
        items = self._dv.wait_for_work_order_resource_requirements(
            work_order_id=work_order_id,
            timeout_seconds=25.0,
            poll_interval_seconds=1.0,
            top=10,
        )
        if not items:
            return None, []

        # If duplicates exist (e.g. older MCP-created requirement + platform-created requirement),
        # prefer the non-demo name and otherwise prefer the oldest.
        demo_name = self._demo_job_name

        def _created_on(it: dict[str, Any]) -> datetime:
            v = it.get("createdon")
            if isinstance(v, str):
                try:
                    return _parse_iso_datetime(v)
                except Exception:
                    pass
            return datetime.max.replace(tzinfo=timezone.utc)

        sorted_items = sorted([it for it in items if isinstance(it, dict)], key=_created_on)
        if len(sorted_items) > 1:
            non_demo = [it for it in sorted_items if str(it.get("msdyn_name") or "").strip() != demo_name]
            if non_demo:
                chosen = non_demo[0]
            else:
                chosen = sorted_items[0]
        else:
            chosen = sorted_items[0]

        req_id = chosen.get("msdyn_resourcerequirementid")
        return (str(req_id) if req_id else None), items

    def search_availability(
        self,
        *,
        requirement_id: str | None,
        window_start_utc: datetime,
        window_end_utc: datetime,
        duration_minutes: int,
        max_slots: int = 8,
    ) -> dict[str, Any]:
        effective_requirement_id = None if self._demo_fast else requirement_id

        cache_key = (
            str(effective_requirement_id or ""),
            _iso(window_start_utc),
            _iso(window_end_utc),
            int(duration_minutes),
            int(max_slots),
        )

        if self._demo_fast:
            now_ts = datetime.now(timezone.utc).timestamp()
            with self._availability_cache_lock:
                cached = self._availability_cache.get(cache_key)
                if cached is not None:
                    expires_ts, value = cached
                    if expires_ts > now_ts:
                        return dict(value)
                    self._availability_cache.pop(cache_key, None)

        max_time_slots = int(max_slots) if self._demo_fast else int(max_slots) * 3

        raw = self._dv.search_field_service_availability(
            start_utc=window_start_utc,
            end_utc=window_end_utc,
            duration_minutes=int(duration_minutes),
            requirement_id=effective_requirement_id,
            max_time_slots=max_time_slots,
            only_bookable_resource_id=self._demo_bookable_resource_id,
        )

        # Some orgs return zero slots for requirement-based availability even when the
        # broader scheduling model can find valid slots. Provide a pragmatic fallback
        # for slot suggestions while retaining diagnostics for troubleshooting.
        if (not self._demo_fast) and requirement_id and not list(raw.get("slots", []) or []):
            try:
                generic = self._dv.search_field_service_availability(
                    start_utc=window_start_utc,
                    end_utc=window_end_utc,
                    duration_minutes=int(duration_minutes),
                    requirement_id=None,
                    max_time_slots=int(max_slots) * 3,
                    only_bookable_resource_id=self._demo_bookable_resource_id,
                )
                if list(generic.get("slots", []) or []):
                    raw = {
                        "status": "ok",
                        "action": f"fallback:{generic.get('action')}",
                        "message": "Requirement-based availability returned no slots; using generic availability for slot suggestions.",
                        "details": {
                            "requirement_based": {
                                "status": raw.get("status"),
                                "action": raw.get("action"),
                                "message": raw.get("message"),
                                "details": raw.get("details"),
                            },
                            "generic": {
                                "status": generic.get("status"),
                                "action": generic.get("action"),
                                "message": generic.get("message"),
                                "details": generic.get("details"),
                            },
                        },
                        "slots": list(generic.get("slots", []) or []),
                        "raw": {
                            "requirement_based": raw.get("raw"),
                            "generic": generic.get("raw"),
                        },
                    }
            except Exception:
                pass

        # Canonicalize timestamps to avoid visually-identical duplicates
        # (e.g., Z vs +00:00, differing seconds precision, etc.).
        # Apply lead-time and rounding rules in *local time* (customer experience).
        try:
            local_tz = ZoneInfo("Europe/London")
        except Exception:
            local_tz = timezone.utc

        lead_time_utc = datetime.now(timezone.utc) + timedelta(minutes=30)
        duration_delta = timedelta(minutes=int(duration_minutes))

        business_open_h = 8
        business_close_h = 18

        def _ceil_to_half_hour_local(dt_utc: datetime) -> datetime:
            local = dt_utc.astimezone(local_tz)
            minute = local.minute
            if minute == 0 or minute == 30:
                rounded = local.replace(second=0, microsecond=0)
            elif minute < 30:
                rounded = local.replace(minute=30, second=0, microsecond=0)
            else:
                rounded = (local.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
            return rounded.astimezone(timezone.utc)

        exact_windows: dict[str, tuple[datetime, datetime, str]] = {}
        for slot in list(raw.get("slots", [])):
            start_raw = slot.get("start")
            end_raw = slot.get("end")
            if not isinstance(start_raw, str) or not isinstance(end_raw, str):
                continue

            # DataverseClient normalizes slot_id as <resourceId>|<startIso>|<endIso>.
            # Preserve resourceId so callers can create `bookableresourcebookings` directly.
            resource_id = "unknown"
            try:
                raw_slot_id = slot.get("slot_id")
                if isinstance(raw_slot_id, str):
                    parts = raw_slot_id.split("|", 2)
                    if len(parts) == 3 and parts[0].strip():
                        resource_id = parts[0].strip()
            except Exception:
                resource_id = "unknown"
            try:
                start_dt = _parse_iso_datetime(start_raw)
                end_dt = _parse_iso_datetime(end_raw)
            except Exception:
                continue
            if end_dt <= start_dt:
                continue

            # Enforce lead-time and aligned starts.
            if start_dt < lead_time_utc:
                start_dt = lead_time_utc
            start_dt = _ceil_to_half_hour_local(start_dt)

            # Enforce business hours (local): only include starts that can finish by close.
            start_local = start_dt.astimezone(local_tz)
            open_local = start_local.replace(hour=business_open_h, minute=0, second=0, microsecond=0)
            close_local = start_local.replace(hour=business_close_h, minute=0, second=0, microsecond=0)

            if start_local < open_local:
                start_dt = open_local.astimezone(timezone.utc)
                start_dt = _ceil_to_half_hour_local(start_dt)
                start_local = start_dt.astimezone(local_tz)
                close_local = start_local.replace(hour=business_close_h, minute=0, second=0, microsecond=0)

            # Cap the window end to the close of the *start day*.
            end_dt = min(end_dt, close_local.astimezone(timezone.utc))

            if end_dt < (start_dt + duration_delta):
                continue

            start_iso = _iso(start_dt)
            end_iso = _iso(end_dt)
            exact_windows[f"{start_iso}|{end_iso}"] = (start_dt, end_dt, resource_id)

        # Collapse repeats by start time: keep the smallest end that still fits duration.
        min_end_by_start: dict[str, tuple[datetime, str]] = {}
        for key, (start_dt, end_dt, resource_id) in exact_windows.items():
            start_iso = _iso(start_dt)
            required_end = start_dt + duration_delta
            if end_dt < required_end:
                continue
            cur = min_end_by_start.get(start_iso)
            if cur is None or end_dt < cur[0]:
                min_end_by_start[start_iso] = (end_dt, resource_id)

        slots: list[dict[str, Any]] = []
        for start_iso, (end_dt, resource_id) in sorted(min_end_by_start.items(), key=lambda kv: kv[0]):
            start_dt = _parse_iso_datetime(start_iso)
            slot_end_dt = start_dt + duration_delta
            if slot_end_dt > end_dt:
                continue
            slot_start_iso = _iso(start_dt)
            slot_end_iso = _iso(slot_end_dt)
            slot_id = f"{resource_id}|{slot_start_iso}|{slot_end_iso}"
            slots.append(
                {
                    "slot_number": len(slots) + 1,
                    "slot_id": slot_id,
                    "start": slot_start_iso,
                    "end": slot_end_iso,
                    "display": f"{slot_start_iso} to {slot_end_iso}",
                }
            )
            if 0 < int(max_slots) <= len(slots):
                break

        out = {
            "status": raw.get("status", "ok"),
            "action": raw.get("action"),
            "count": len(slots),
            "slots": slots,
            "message": raw.get("message"),
            "details": raw.get("details"),
            "raw": raw.get("raw"),
        }

        if self._demo_fast:
            ttl_seconds = 180.0
            expires_ts = datetime.now(timezone.utc).timestamp() + ttl_seconds
            with self._availability_cache_lock:
                self._availability_cache[cache_key] = (expires_ts, dict(out))

        return out

    def book_requirement(
        self,
        *,
        requirement_id: str,
        schedule_start_utc: datetime,
        schedule_end_utc: datetime,
        work_order_id: str | None = None,
    ) -> dict[str, Any]:
        duration_minutes = int((schedule_end_utc - schedule_start_utc).total_seconds() // 60)
        if duration_minutes <= 0:
            return {
                "status": "error",
                "message": "Invalid booking window: duration must be > 0 minutes.",
                "requested": {"start": _iso(schedule_start_utc), "end": _iso(schedule_end_utc)},
            }

        target_start = _iso(schedule_start_utc)
        target_end = _iso(schedule_end_utc)

        # Presales demo: lock booking to a single known resource and avoid additional
        # availability calls (single-user flows, speed > completeness).
        if self._demo_fast and self._demo_bookable_resource_id:
            chosen_slot_id = f"{self._demo_bookable_resource_id}|{target_start}|{target_end}"
            try:
                booking_created = self._dv.create_booking_for_requirement(
                    slot_id=chosen_slot_id,
                    requirement_id=requirement_id,
                    work_order_id=work_order_id,
                    booking_status_name="Scheduled",
                    name=self._demo_job_name,
                )
                booking = booking_created.get("booking") if isinstance(booking_created, dict) else None
                if not isinstance(booking, dict):
                    booking = {}
                booking.update({"start": target_start, "end": target_end})
                return {
                    "status": "ok",
                    "booking": booking,
                    "selected_slot": booking_created.get("selected_slot"),
                    "raw": booking_created,
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": "Failed to create Bookable Resource Booking record.",
                    "details": str(e),
                }

        # Resolve a concrete resource slot_id for this requirement and window.
        # We do not require Schedule Assistant pipeline capabilities for this flow.
        availability = self._dv.search_field_service_availability(
            start_utc=schedule_start_utc,
            end_utc=schedule_end_utc,
            duration_minutes=duration_minutes,
            requirement_id=requirement_id,
            max_time_slots=25,
            max_resources=5,
            only_bookable_resource_id=self._demo_bookable_resource_id,
        )

        chosen_slot_id: str | None = None
        used_generic_fallback = False
        generic_fallback_action: str | None = None
        for s in list(availability.get("slots", [])):
            sid = s.get("slot_id")
            if not isinstance(sid, str) or sid.count("|") != 2:
                continue
            # Expect <resource>|<start>|<end>
            try:
                rid, st, en = sid.split("|", 2)
            except Exception:
                continue
            if rid.strip().lower() == "unknown":
                continue
            if st == target_start and en == target_end:
                chosen_slot_id = sid
                break

        if chosen_slot_id is None:
            # Fall back to the first concrete slot if exact match isn't returned.
            for s in list(availability.get("slots", [])):
                sid = s.get("slot_id")
                if not isinstance(sid, str) or sid.count("|") != 2:
                    continue
                if sid.split("|", 1)[0].strip().lower() == "unknown":
                    continue
                chosen_slot_id = sid
                break

        if chosen_slot_id is None:
            generic_preview: dict[str, Any] | None = None
            try:
                generic_preview = self._dv.search_field_service_availability(
                    start_utc=schedule_start_utc,
                    end_utc=schedule_end_utc,
                    duration_minutes=duration_minutes,
                    requirement_id=None,
                    max_time_slots=5,
                    max_resources=3,
                    only_bookable_resource_id=self._demo_bookable_resource_id,
                )
            except Exception:
                generic_preview = None

            if isinstance(generic_preview, dict):
                # Prefer an exact time match when available.
                for s in list(generic_preview.get("slots", [])):
                    sid = s.get("slot_id")
                    if not isinstance(sid, str) or sid.count("|") != 2:
                        continue
                    if sid.split("|", 1)[0].strip().lower() == "unknown":
                        continue
                    try:
                        _, st, en = sid.split("|", 2)
                    except Exception:
                        continue
                    if st == target_start and en == target_end:
                        chosen_slot_id = sid
                        used_generic_fallback = True
                        generic_fallback_action = str(generic_preview.get("action") or "") or None
                        break

                # Otherwise just pick the first concrete slot.
                if chosen_slot_id is None:
                    for s in list(generic_preview.get("slots", [])):
                        sid = s.get("slot_id")
                        if not isinstance(sid, str) or sid.count("|") != 2:
                            continue
                        if sid.split("|", 1)[0].strip().lower() == "unknown":
                            continue
                        chosen_slot_id = sid
                        used_generic_fallback = True
                        generic_fallback_action = str(generic_preview.get("action") or "") or None
                        break

            if chosen_slot_id is not None:
                # Proceed to booking using the fallback-selected concrete slot.
                pass
            else:
                return {
                    "status": "error",
                    "message": "No concrete resource slots returned for this requirement; cannot create Bookable Resource Booking directly.",
                    "requirement": {"id": requirement_id},
                    "requested": {"start": target_start, "end": target_end},
                    "availability": {
                        "status": availability.get("status"),
                        "action": availability.get("action"),
                        "message": availability.get("message"),
                        "count": len(list(availability.get("slots", []))),
                    },
                    "details": {
                        "requirement_based": {
                            "details": availability.get("details"),
                            "raw": availability.get("raw"),
                        },
                        "generic_preview": (
                            {
                                "status": generic_preview.get("status"),
                                "action": generic_preview.get("action"),
                                "message": generic_preview.get("message"),
                                "count": len(list(generic_preview.get("slots", []))),
                            }
                            if isinstance(generic_preview, dict)
                            else None
                        ),
                    },
                }

        try:
            booking_created = self._dv.create_booking_for_requirement(
                slot_id=chosen_slot_id,
                requirement_id=requirement_id,
                work_order_id=work_order_id,
                booking_status_name="Scheduled",
                name=self._demo_job_name,
            )
            booking = booking_created.get("booking") if isinstance(booking_created, dict) else None
            if not isinstance(booking, dict):
                booking = {}
            booking.update({"start": target_start, "end": target_end})
            out: dict[str, Any] = {
                "status": "ok",
                "booking": booking,
                "selected_slot": booking_created.get("selected_slot"),
                "raw": booking_created,
            }

            if used_generic_fallback:
                out["availability_fallback"] = {
                    "used": True,
                    "action": generic_fallback_action,
                    "note": "Requirement-based availability returned no concrete slots; used generic availability to select a concrete resource slot.",
                }

            return out
        except Exception as e:
            return {
                "status": "error",
                "message": "Failed to create Bookable Resource Booking record.",
                "details": str(e),
            }

    def schedule_customer_request(
        self,
        *,
        contact_id: str,
        window_id: str,
        preferred_start_local: str,
        duration_minutes: int,
        priority: str = "normal",
        create_case: bool = True,
        scenario: str = "boiler_repair",
    ) -> dict[str, Any]:
        contact_id = _normalize_guid(contact_id)
        duration_minutes = int(duration_minutes)

        try:
            w_start_str, w_end_str = window_id.split("|", 1)
            window_start_utc = _parse_iso_datetime(w_start_str)
            window_end_utc = _parse_iso_datetime(w_end_str)
        except Exception as e:
            raise RuntimeError("Invalid window_id. Expected format: <windowStartIso>|<windowEndIso>") from e

        preferred_start_utc = self._dv.parse_preferred_local_start_to_utc(preferred_start_local)
        preferred_end_utc = preferred_start_utc + timedelta(minutes=duration_minutes)

        if preferred_start_utc < window_start_utc or preferred_end_utc > window_end_utc:
            return {
                "status": "error",
                "message": "Requested appointment time is outside the selected availability window.",
                "window": {"start": _iso(window_start_utc), "end": _iso(window_end_utc)},
                "requested": {"start": _iso(preferred_start_utc), "end": _iso(preferred_end_utc)},
            }

        env_id = f"{(self._dv.base_url or '').rstrip('/').lower()}|{(getattr(self._dv, 'api_version', '') or '').strip().lower()}"

        key = _compute_idempotency_key(
            environment_id=env_id,
            contact_id=contact_id,
            window_start_utc=window_start_utc,
            window_end_utc=window_end_utc,
            preferred_start_utc=preferred_start_utc,
            duration_minutes=duration_minutes,
            scenario=scenario,
        )
        existing = self._idempotency.get(key)

        if existing and existing.get("booking", {}).get("id"):
            booking_id = str((existing.get("booking") or {}).get("id") or "").strip()
            if booking_id:
                # Guard against stale replays (e.g., switching Dataverse orgs or manual cleanup).
                try:
                    self._dv._get(
                        f"bookableresourcebookings({booking_id})?$select=bookableresourcebookingid",
                        include_annotations=False,
                    )
                    return {"status": "ok", "idempotent_replay": True, **existing}
                except Exception:
                    # Treat as cache miss; proceed to create fresh records.
                    existing = None

        case_id: str | None = None
        if create_case:
            case_id = self._dv.create_case_for_contact(
                contact_id=contact_id,
                title=self._demo_job_name,
                description=f"{self._demo_job_name} request (presales demo).",
                priority=priority,
                origin="web",
            )

        work_order_id = self.create_work_order(case_id=case_id, priority=priority)

        requirement_id, rr_candidates = self._get_or_wait_for_requirement_id_for_work_order(work_order_id=work_order_id)
        if not requirement_id:
            return {
                "status": "error",
                "message": "Work Order was created, but no auto-created Resource Requirement was found.",
                "case": {"id": case_id} if case_id else None,
                "work_order": {"id": work_order_id},
                "details": {
                    "hint": "Check Field Service settings/automation for work order requirement creation.",
                    "candidates": rr_candidates,
                },
            }

        # Constrain the auto-created requirement to the selected availability window and duration.
        self._dv.update_record(
            "msdyn_resourcerequirements",
            requirement_id,
            {
                "msdyn_fromdate": _iso(window_start_utc),
                "msdyn_todate": _iso(window_end_utc),
                "msdyn_duration": int(duration_minutes),
                # Requirement-based availability in many orgs depends on these fields.
                "msdyn_timewindowstart": _iso(window_start_utc),
                "msdyn_timewindowend": _iso(window_end_utc),
                "msdyn_timezonefortimewindow": 85,
                "msdyn_worklocation": 690970000,
                "msdyn_latitude": 52.41882,
                "msdyn_longitude": -1.78605,
            },
        )

        # Optional validation: only meaningful when the selected window is wider than the appointment.
        # For slot-based booking (window == appointment), this check can produce false negatives.
        window_minutes = int((window_end_utc - window_start_utc).total_seconds() // 60)
        if (not self._demo_fast) and window_minutes > (duration_minutes + 5):
            try:
                availability = self._dv.search_field_service_availability(
                    start_utc=window_start_utc,
                    end_utc=window_end_utc,
                    duration_minutes=duration_minutes,
                    requirement_id=requirement_id,
                    max_time_slots=50,
                    only_bookable_resource_id=self._demo_bookable_resource_id,
                )
                matches = False
                for s in list(availability.get("slots", [])):
                    s_start = s.get("start")
                    s_end = s.get("end")
                    if not isinstance(s_start, str) or not isinstance(s_end, str):
                        continue
                    if _parse_iso_datetime(s_start) <= preferred_start_utc and _parse_iso_datetime(s_end) >= preferred_end_utc:
                        matches = True
                        break
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
                            "count": len(list(availability.get("slots", []))),
                        },
                    }
            except Exception:
                pass

        booking_result = self.book_requirement(
            requirement_id=requirement_id,
            schedule_start_utc=preferred_start_utc,
            schedule_end_utc=preferred_end_utc,
            work_order_id=work_order_id,
        )

        out = {
            "case": {"id": case_id} if case_id else None,
            "work_order": {"id": work_order_id},
            "requirement": {"id": requirement_id},
            "booking": booking_result.get("booking"),
            "requirement_characteristics": {
                "names": [],
                "ids": [],
            },
            "requested": {"start": _iso(preferred_start_utc), "end": _iso(preferred_end_utc)},
            "slot": {"slot_id": f"{_iso(preferred_start_utc)}|{_iso(preferred_end_utc)}", "start": _iso(preferred_start_utc), "end": _iso(preferred_end_utc)},
            "customer_friendly": {
                "appointment_text": f"{_iso(preferred_start_utc)} to {_iso(preferred_end_utc)}",
            },
        }

        if booking_result.get("status") != "ok":
            return {
                "status": booking_result.get("status", "error"),
                **out,
                "details": booking_result.get("error") or booking_result.get("raw"),
            }

        # Verify booking exists before persisting (prevents the model from replaying
        # an ID that never actually made it into Dataverse).
        booking_id = str((out.get("booking") or {}).get("id") or "").strip()
        if booking_id:
            try:
                self._dv._get(
                    f"bookableresourcebookings({booking_id})?$select=bookableresourcebookingid",
                    include_annotations=False,
                )
            except Exception as e:
                return {
                    "status": "error",
                    **out,
                    "message": "Booking was returned by the booking flow but could not be confirmed in Dataverse.",
                    "details": str(e),
                }

        self._idempotency.put(key, {"status": "ok", **out})
        return {"status": "ok", **out}
