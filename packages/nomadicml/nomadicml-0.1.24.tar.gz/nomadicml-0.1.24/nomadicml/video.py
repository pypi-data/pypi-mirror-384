"""
Video-related operations for the NomadicML SDK.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import re
import time
import logging
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional, Union
import random
from .client import NomadicML
from .types import (
    VideoSource,
    RapidReviewEvent,
    UIEvent, 
)
from .utils import (
    format_error_message, infer_source,
    get_file_mime_type, get_filename_from_path
)
from .exceptions import VideoUploadError, NomadicMLError, ValidationError

logger = logging.getLogger("nomadicml")
from pathlib import Path
from typing import Sequence, Union, List, Dict, Any, Optional, overload, Literal
# ──────────────────────────────────────────────────────────────────────────────
# Type aliases
# ──────────────────────────────────────────────────────────────────────────────
VideoInput   = Union[str, Path]           # paths or URLs/video IDs as str
VideoInputs  = Union[VideoInput, Sequence[VideoInput]]
VideoID      = str
VideoIDList  = Sequence[VideoID]
FolderScopeLiteral = Literal["user", "org", "sample"]

class AnalysisType(str, Enum):
    """Canonical analysis types exposed by the SDK."""

    ASK = "rapid_review"  # public surface calls this "Ask"

    # Agent families surfaced in the product UI
    GENERAL_AGENT = "edge_case_agent"
    LANE_CHANGE = "lane_change_agent"
    TURN = "turn_agent"
    RELATIVE_MOTION = "relative_motion_agent"
    DRIVING_VIOLATIONS = "violation_agent"
    CUSTOM_AGENT = "custom_agent"

    # Deprecated / legacy aliases kept temporarily for compatibility
    AGENT_GENERAL = GENERAL_AGENT
    LANE_CHANGE_AGENT = LANE_CHANGE
    TURN_AGENT = TURN
    RELATIVE_MOTION_AGENT = RELATIVE_MOTION
    VIOLATION_AGENT = DRIVING_VIOLATIONS
    EDGE_CASE_AGENT = GENERAL_AGENT

    SEARCH = "search"  # DEPRECATED - kept for backwards compatibility

class CustomCategory(str, Enum):
    DRIVING        = "driving"
    ROBOTICS       = "robotics"
    AERIAL         = "aerial"
    SECURITY       = "security"
    ENVIRONMENT  = "environment"

# Helper ----------------------------------------------------------------------

def _is_iterable(obj):
    """True for list / tuple / set but *not* for strings or Path."""
    return isinstance(obj, Sequence) and not isinstance(obj, (str, Path))


class VideoClient:
    """
    Client for video upload and analysis operations.
    
    This class extends the base NomadicML client with video-specific operations.
    
    Args:
        client: An initialized NomadicML client.
    """
    _status_ranks = {
        "NOT_STARTED": 0,
        "PREPARE_IN_PROGRESS": 0.5,
        "PREPARE_COMPLETED": 1,
        "UPLOADED": 1,
        "DETECTING_IN_PROGRESS": 1.5,
        "PROCESSING": 1.5,
        "DETECTING_COMPLETED": 2,
        "DETECTING_COMPLETED_NO_EVENTS": 2.1,
        "SUMMARIZING_IN_PROGRESS": 2.5,
        "SUMMARIZING_COMPLETED": 3,
        "COMPLETED": 3,
    }

    _BACKEND_SPLIT_SYMBOL = "-----------EVENT_DESCRIPTION-----------"

    _AGENT_DEFAULTS: Dict[AnalysisType, Dict[str, str]] = {
        AnalysisType.GENERAL_AGENT: {
            "edge_case_category": "agent_mode_placeholder",
            "agent_mode": "agent",
        },
        AnalysisType.LANE_CHANGE: {
            "edge_case_category": "Lane Change Detection",
            "agent_mode": "assistant",
        },
        AnalysisType.TURN: {
            "edge_case_category": "Vehicle Turns",
            "agent_mode": "assistant",
        },
        AnalysisType.RELATIVE_MOTION: {
            "edge_case_category": "Relative Motion Analysis",
            "agent_mode": "assistant",
        },
        AnalysisType.DRIVING_VIOLATIONS: {
            "edge_case_category": "Driving Violations",
            "agent_mode": "assistant",
        },
    }

    _ASSISTANT_EDGE_CASES: Dict[AnalysisType, List[Dict[str, Any]]] = {
        AnalysisType.LANE_CHANGE: [
            {
                "title": "lane change",
                "description": "Detect instances where the ego vehicle crosses lane markings to change lanes (left or right).",
                "importance": 80,
            },
        ],
        AnalysisType.TURN: [
            {
                "title": "vehicle turns",
                "description": "Detect left or right turns at intersections or driveways.",
                "importance": 80,
            },
        ],
        AnalysisType.RELATIVE_MOTION: [
            {
                "title": "relative motion",
                "description": "Detect significant relative motion patterns between ego and surrounding vehicles (approach, overtake, diverge).",
                "importance": 70,
            },
        ],
        AnalysisType.DRIVING_VIOLATIONS: [
            {
                "title": "speeding",
                "description": "Detect instances where the ego vehicle exceeds posted speed limits or drives at unsafe speeds.",
                "importance": 90,
            },
            {
                "title": "running red light",
                "description": "Detect when ego vehicle enters intersection after traffic signal turns red.",
                "importance": 95,
            },
            {
                "title": "failure to stop",
                "description": "Detect failures to come to complete stop at stop signs or before right turns on red.",
                "importance": 85,
            },
            {
                "title": "improper lane usage",
                "description": "Detect driving in wrong lane, crossing solid lines, or using emergency/HOV lanes improperly.",
                "importance": 80,
            },
            {
                "title": "following too closely",
                "description": "Detect unsafe following distances or tailgating behavior by ego vehicle.",
                "importance": 75,
            },
        ],
    }

    def _build_agent_request(
        self,
        agent_type: AnalysisType,
        *,
        model_id: str,
        concept_ids: Optional[Sequence[str]] = None,
        _config: str = "default",
    ) -> Dict[str, Any]:
        """Return the form payload matching the agent presets exposed in the product."""

        if agent_type not in self._AGENT_DEFAULTS:
            supported = ", ".join(sorted(t.name for t in self._AGENT_DEFAULTS))
            raise ValueError(f"Unsupported agent analysis type '{agent_type}'. Pick one of: {supported}")

        defaults = self._AGENT_DEFAULTS[agent_type]
        assistant_cases = self._ASSISTANT_EDGE_CASES.get(agent_type, [])

        return {
            "firebase_collection_name": self.client.collection_name,
            "model_id": model_id,
            "edge_case_category": defaults["edge_case_category"],
            "concepts_json": json.dumps(list(concept_ids or [])),
            "mode": defaults["agent_mode"],
            "assistant_edge_cases_json": json.dumps(assistant_cases),
            "config": _config,
        }
    
    def __init__(self, client: NomadicML):
        """
        Initialize the video client with a NomadicML client.
        
        Args:
            client: An initialized NomadicML client.
        """
        self.client = client
        self._user_info = None

    def _print_status_bar(
        self,
        item_id: str,
        *,
        status: str | None = None,
        percent: float | None = None,
        width: int = 30,
    ) -> None:
        """
        Log a tidy ASCII progress-bar.

        Parameters
        ----------
        item_id : str
            Identifier shown in the log line (video_id, sweep_id, …).
        status : str | None
            Human-readable stage label ("UPLOADED", "PROCESSING"…).  
            Ignored when an explicit `percent` is supplied.
        percent : float | None
            0 – 100 exact progress.  If omitted, the method falls back to the
            coarse-grained stage → rank mapping stored in ``self._status_ranks``.
        width : int
            Total bar characters (default 30).
        """
        # ── compute percentage ────────────────────────────────────────────────
        if percent is None:
            # coarse mode: derive % from status → rank table
            rank = self._status_ranks.get((status or "").upper(), 0)
            max_rank = max(self._status_ranks.values()) or 1
            percent = (rank / max_rank) * 100

        # clamp & build bar
        percent = max(0, min(percent, 100))
        filled  = int(percent / 100 * width)
        bar     = "[" + "=" * filled + " " * (width - filled) + "]"

        # choose label
        label = f"{percent:3.0f}%" if status is None else status.upper()

        logger.info(f"{item_id}: {bar} {label}")
            
    async def _get_auth_user(self) -> Optional[Dict[str, Any]]:
        """
        Get the authenticated user information.
        
        Returns:
            A dictionary with user information if available, None otherwise.
        """
        if self.user_info:
            return self.user_info
            
        try:
            response = self.client._make_request(
                method="POST",
                endpoint="/api/keys/verify",
            )
            
            self.user_info = response.json()
            return self.user_info
        except Exception as e:
            logger.warning(f"Failed to get authenticated user info: {e}")
            return None

    def _get_api_events(self, analysis_json: Dict[str, Any]):
        """Return the list of events from either the new or legacy payload."""
        # Check for new analysis document structure first
        if "analysis" in analysis_json and analysis_json["analysis"]:
            events = analysis_json["analysis"].get("events")
            if events is not None:
                return events
        
        # Fall back to legacy structure in metadata.visual_analysis
        events = (
            analysis_json.get("metadata", {})
                        .get("visual_analysis", {})
                        .get("events")
        )
        if events is not None:
            return events
        
        # Try another legacy format
        return (
            analysis_json
            .get("events", {})
            .get("visual_analysis", {})
            .get("status", {})
            .get("quick_summary", {})
            .get("events")
        )

    def _parse_api_events(self, analysis_json, analysis_type=AnalysisType.ASK):
            """
            Parse the API analysis JSON into a list of event dictionaries.
            Handles both legacy (visual_analysis in metadata) and new (analysis document) formats.
            
            Args:
                analysis_json: The raw JSON dict returned from the API.
                default_duration: Default duration (in seconds) to assume if an event only has a single time point.
                analysis_type: The type of analysis performed (e.g., 'rapid_review', 'edge_case', etc.)
                
            Returns:
                list: List of events dictionaries with label, start_time, and end_time
            """
            results = []
            
            # Debug: Print top-level keys to help understand structure
            logger.debug(f"Parsing API events. Top-level keys: {list(analysis_json.keys())}")
            
            # Try different possible paths for events
            events_list = self._get_api_events(analysis_json)

            if not events_list:
                logger.debug("events list empty in API response")
                return results
        
            is_agent_type = False
            if isinstance(analysis_type, AnalysisType):
                is_agent_type = analysis_type in self._AGENT_DEFAULTS
            else:
                try:
                    coerced = self._coerce_analysis_type(analysis_type)
                    is_agent_type = coerced in self._AGENT_DEFAULTS
                except ValueError:
                    is_agent_type = False

            if is_agent_type:
                logger.debug(
                    "Analysis type '%s' detected as agent-based (legacy edge_case), so filtering rejected events.",
                    analysis_type,
                )
                logger.debug(f"Events before filtering: {len(events_list)}")
                events_list = [event for event in events_list if event.get('edgeCaseValidated', 'false').lower() == 'true']
                logger.debug(f"Filtered events count: {len(events_list)}")

            # Process each event
            for event in events_list:
                if not isinstance(event, dict):
                    continue

                # Rapid review events (UI format) → convert to SDK format
                if (analysis_type == AnalysisType.ASK or str(analysis_type) == AnalysisType.ASK.value) and (
                    "type" in event and "time" in event
                ):
                    converted = self._convert_ui_event_to_rapid_review(event)
                    if converted:
                        results.append(converted)
                    continue

                # Already-normalised event (likely from SDK itself)
                if "t_start" in event and "t_end" in event:
                    results.append(event)
                    continue

                # We'll treat 'description' as the label.
                label = event.get("description", "Unknown")

                # Print event structure for debugging
                logger.debug(f"Processing event: {label}")

                # Try to extract start and end time information
                start_time = None
                end_time = None

                if "time" in event:
                    time_str = event.get("time", "")
                    match = re.search(r"t=(\d+(\.\d+)?)", time_str)
                    if match:
                        start_time = float(match.group(1))

                if "end_time" in event:
                    end_time_str = event.get("end_time", "")
                    match = re.search(r"t=(\d+(\.\d+)?)", end_time_str)
                    if match:
                        end_time = float(match.group(1))

                # Check for refined_events if present
                used_refined_events = False
                refined = event.get("refined_events", "")
                if refined:
                    try:
                        refined_data = json.loads(refined)  # Expecting a list of intervals like [start, end, text]
                        if isinstance(refined_data, list):
                            for item in refined_data:
                                if isinstance(item, list) and len(item) >= 2:
                                    st = float(item[0])
                                    en = float(item[1])
                                    results.append({
                                        "label": label,
                                        "start_time": st,
                                        "end_time": en
                                    })
                                    used_refined_events = True
                                    logger.debug(f"  Added refined event: {label} from {st}s to {en}s")
                    except json.JSONDecodeError:
                        logger.warning(f"  Failed to parse refined_events JSON: {refined[:50]}...")
                        pass

                # If no refined intervals and we found basic timing, use that
                if not used_refined_events and start_time is not None and end_time is not None:
                    results.append({
                        "label": label,
                        "start_time": start_time,
                        "end_time": end_time
                    })
                    logger.debug(f"  Added event: {label} from {start_time}s to {end_time}s")
            
            logger.info(f"Total events extracted: {len(results)}")
            return results
    
    def _parse_upload_response(self, video_id: str, payload: Dict[str, Any]) -> Dict[str, str]:
        """Return the compact {{video_id, status}} dict expected by callers."""
        status = (payload.get("status")
                or payload.get("visual_analysis", {})
                        .get("status", {})
                        .get("status", "unknown"))
        return {"video_id": video_id, "status": str(status).lower()}
    
    def _convert_ui_event_to_rapid_review(self, ui_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a UI-formatted event from Firebase back to RapidReviewEvent format.
        
        The backend stores events in UI format using _ui_event() function,
        but the SDK should return them in the original RapidReviewEvent format.
        
        Args:
            ui_event: Event in UI format from Firebase
            
        Returns:
            Event in RapidReviewEvent format expected by SDK users
        """
        if not ui_event:
            return None
            
        def seconds_to_timestamp(time_str: str) -> str:
            """Convert 't=X.XX' format to 'MM:SS' or 'HH:MM:SS' format."""
            if not time_str or time_str == "":
                return "00:00"
                
            # Extract seconds from "t=X.XX" format
            if time_str.startswith("t="):
                try:
                    seconds = float(time_str[2:])
                except (ValueError, IndexError):
                    return "00:00"
            else:
                try:
                    seconds = float(time_str)
                except ValueError:
                    return "00:00"
            
            # Convert to HH:MM:SS or MM:SS
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            else:
                return f"{minutes:02d}:{secs:02d}"
        
        # Extract original data if nested
        original_data = ui_event.get("data", {})
        
        # Build RapidReviewEvent format
        rapid_review_event = {
            "t_start": seconds_to_timestamp(ui_event.get("time", "")),
            "t_end": seconds_to_timestamp(ui_event.get("end_time", "")),
            "category": ui_event.get("type", original_data.get("category", "Unknown")),
            "label": ui_event.get("description", original_data.get("label", "")),
            "severity": ui_event.get("severity", "medium"),
            "aiAnalysis": ui_event.get("aiAnalysis", ""),
            "confidence": original_data.get("confidence", 0.85),  # Default confidence if not present
            "approval": ui_event.get("approval", "pending"),
        }
        
        # Add thumbnail URL if present
        if "annotated_thumbnail_url" in original_data:
            rapid_review_event["annotated_thumbnail_url"] = original_data["annotated_thumbnail_url"]
        elif "annotated_thumbnail_url" in ui_event:
            rapid_review_event["annotated_thumbnail_url"] = ui_event["annotated_thumbnail_url"]
            
        return rapid_review_event

    
    def get_user_id(self) -> Optional[str]:
        """
        Get the authenticated user ID.
        
        Returns:
            The user ID if available, None otherwise.
        """
        # Try to get cached user info
        if self._user_info and "user_id" in self._user_info:
            return self._user_info["user_id"]
        
        # Make a synchronous request to get user info
        try:
            response = self.client._make_request(
                method="POST",
                endpoint="/api/keys/verify"
            )
            self._user_info = response.json()
            return self._user_info.get("user_id")
        except Exception as e:
            logger.warning(f"Failed to get user ID: {str(e)}")
            return None
    
    def _custom_event_detection(
        self,
        video_id: str,
        custom_category: CustomCategory | str,
        event_description: str,
        is_thumbnail: bool = False,
        use_enhanced_motion_analysis: bool = False,
        _config: str = "default",
        confidence: str = "low",
        custom_agent_id: str | None = None
    ) -> Dict[str, Any]:
        """
        Ask the backend to derive structured events for ``video_id`` by asking a specific question.
        Uses the POST /ask endpoint for rapid_review.

        Args:
            video_id: The ID of the video.
            custom_category: The category enum or string value, used to form the prompt.
            event_description: The description of the event, used to form the prompt.

        Returns:
            A dictionary with the backend's response.
            
        Raises:
            NomadicMLError: If the request fails.
        """
        if not event_description and not custom_agent_id:
            raise ValueError("event_description cannot be empty for analysis type rapid_review.")
        if not custom_category and not custom_agent_id:
            raise ValueError("custom_category cannot be empty for analysis type rapid_review.")
        if not isinstance(use_enhanced_motion_analysis, bool) and not custom_agent_id:
            raise ValueError("use_enhanced_motion_analysis must be a boolean value.")
        
        # Extract the string value whether it's an enum or string
        category_value = custom_category.value if isinstance(custom_category, CustomCategory) else custom_category
        prompt = f"{category_value}{self._BACKEND_SPLIT_SYMBOL}{event_description}"

        payload = {
            "question": prompt,
            "video_id": video_id,
            "is_thumbnail": is_thumbnail,
            "use_enhanced_motion_analysis": use_enhanced_motion_analysis,
            "config": _config,
            "confidence": confidence,
            "custom_agent_id": custom_agent_id,
        }

        resp = self.client._make_request("POST", "/api/ask", data=payload)
        
        if resp.status_code == 202:
            # Chunked processing - poll until complete
            result = resp.json()
            analysis_id = result.get("analysis_id")
            if not analysis_id:
                raise NomadicMLError("Backend returned 202 but no analysis_id")
            logger.info(f"Rapid review started. Analysis ID: {analysis_id}")
            # Wait for completion and return final merged result
            return self._wait_for_rapid_review(video_id, analysis_id, is_thumbnail=is_thumbnail)
        elif 200 <= resp.status_code < 300:
            # Immediate response - return as before
            return resp.json()
        else:
            error_msg = resp.json() if resp.content else "Unknown error"
            raise NomadicMLError(f"Failed to generate events via /ask: {format_error_message(error_msg)}")

    # ── batch helpers ───────────────────────────────────────────────────
    def _build_batch_viewer_links(self, batch_id: str) -> Dict[str, str]:
        """Return relative and absolute links for Batch Results Viewer."""
        path = f"/use-cases/rapid-review/batch-view/{batch_id}"

        base_url = os.getenv("NOMADICML_DASHBOARD_BASE_URL")
        if not base_url:
            collection = (self.client.collection_name or "").lower()
            if collection == "videos":
                base_url = "https://app.nomadicml.com"
            else:
                base_url = "https://main.app.nomadicml.com"

        base = base_url.rstrip("/")
        return {"path": path, "url": f"{base}{path}"}

    def _serialize_bool(self, value: bool | None) -> Optional[str]:
        """Serialize booleans for form submissions."""
        if value is None:
            return None
        return "true" if value else "false"

    def _prepare_batch_form(
        self,
        video_ids: List[str],
        *,
        analysis_type: AnalysisType,
        custom_event: Optional[str],
        custom_category: Optional[CustomCategory | str],
        concept_ids: Optional[List[str]],
        model_id: str,
        is_thumbnail: bool,
        use_enhanced_motion_analysis: bool,
        _config: str = "default",
        confidence: str = "low",
        custom_agent_id: Optional[str] = None,
    ) -> tuple[str, List[tuple[str, str]]]:
        """Return mode label and list of (key, value) tuples for create-batch."""

        if not video_ids:
            raise ValidationError("No video_ids provided for batch analysis")

        entries: List[tuple[str, str]] = []
        for vid in video_ids:
            entries.append(("video_ids", vid))

        concepts_json = json.dumps(concept_ids or [])

        if analysis_type == AnalysisType.ASK:
            if not custom_event:
                raise ValueError("custom_event must be provided for asking agent batch analyses")
            if not custom_category:
                raise ValueError("custom_category must be provided for asking agent batch analyses")
            category_value = custom_category.value if isinstance(custom_category, CustomCategory) else custom_category

            entries.extend([
                ("analysis_kind", "rapid_review"),
                ("prompt", custom_event),
                ("category", category_value),
                ("concepts_json", concepts_json),
                ("config", _config),
                ("confidence", confidence)
            ])

            is_thumb = self._serialize_bool(is_thumbnail)
            if is_thumb is not None:
                entries.append(("is_thumbnail", is_thumb))

            enhanced_motion = self._serialize_bool(use_enhanced_motion_analysis)
            if enhanced_motion is not None:
                entries.append(("use_enhanced_motion_analysis", enhanced_motion))

            mode_label = "rapid_review"
        elif analysis_type == AnalysisType.CUSTOM_AGENT:
            if not custom_agent_id:
                raise ValueError("custom_agent_id must be provided for custom_agent batch analyses")

            entries.extend([
                ("analysis_kind", "rapid_review"),
                ("concepts_json", concepts_json),
                ("model_id", model_id),
                ("config", _config),
                ("custom_agent_id", custom_agent_id),
            ])
            mode_label = "rapid_review"
        else:
            if analysis_type not in self._AGENT_DEFAULTS:
                supported = ", ".join(sorted(t.name for t in self._AGENT_DEFAULTS))
                raise ValueError(
                    f"Batch agent analyses support only {supported}. Received {analysis_type!r}."
                )

            defaults = self._AGENT_DEFAULTS[analysis_type]
            assistant_edge_cases = self._ASSISTANT_EDGE_CASES.get(analysis_type, [])

            entries.extend([
                ("analysis_kind", "edge_agent"),
                ("concepts_json", concepts_json),
                ("model_id", model_id),
                ("config", _config),
            ])
            entries.append(("edge_case_category", defaults["edge_case_category"]))
            entries.append(("agent_mode", defaults["agent_mode"]))
            entries.append(("assistant_edge_cases_json", json.dumps(assistant_edge_cases)))

            # Return the renamed public-facing mode so batch + single analyses match
            mode_label = "agent"

        entries.append(("start", "true"))
        entries.append(("client_batch_id", uuid.uuid4().hex))

        return mode_label, entries

    def _submit_batch(
        self,
        entries: List[tuple[str, str]],
    ) -> Dict[str, Any]:
        """Call /create-batch and validate response."""
        response = self.client._make_request(
            method="POST",
            endpoint="/api/create-batch",
            data=entries,
        )
        payload = response.json()
        batch_id = payload.get("batch_id")
        if not batch_id:
            raise NomadicMLError("Backend create-batch response was missing batch_id")
        return payload

    def _poll_batch_status(
        self,
        batch_id: str,
        *,
        timeout: int,
        poll_interval: int = 5,
    ) -> Dict[str, Any]:
        """Poll backend batch status endpoint until completion or timeout."""
        deadline = time.time() + timeout
        last_completed = -1

        while True:
            response = self.client._make_request(
                method="GET",
                endpoint=f"/api/batch/{batch_id}/status",
            )
            status_payload = response.json()
            agg = status_payload.get("aggregated_progress") or {}
            total = int(agg.get("total", 0) or 0)
            completed = int(agg.get("completed", 0) or 0)
            status = (status_payload.get("status") or "").lower()

            if completed > last_completed:
                last_completed = completed
                logger.info(
                    "Batch %s progress %s/%s status=%s",
                    batch_id,
                    completed,
                    total,
                    status or "unknown",
                )

            if total > 0 and completed >= total:
                return status_payload
            if status in {"completed", "failed", "cancelled"}:
                return status_payload
            if time.time() > deadline:
                raise TimeoutError(
                    f"Batch {batch_id} did not complete within {timeout} seconds"
                )
            time.sleep(poll_interval)

    def _extract_analysis_id(self, payload: Dict[str, Any]) -> Optional[str]:
        """Best-effort extraction of analysis_id from API payload."""
        if not isinstance(payload, dict):
            return None
        if payload.get("analysis_id"):
            return payload.get("analysis_id")
        analysis = payload.get("analysis")
        if isinstance(analysis, dict) and analysis.get("analysis_id"):
            return analysis.get("analysis_id")
        metadata = payload.get("metadata")
        if isinstance(metadata, dict):
            # Rapid review metadata stores analysis id under visual_analysis
            candidate = metadata.get("analysis_id")
            if candidate:
                return candidate
            visual = metadata.get("visual_analysis", {})
            if isinstance(visual, dict):
                candidate = visual.get("analysis_id") or visual.get("analysisId")
                if candidate:
                    return candidate
        return None

    def _extract_summary(self, payload: Dict[str, Any]) -> str:
        """Fetch summary/answer text from payload where available."""
        if not isinstance(payload, dict):
            return ""
        analysis = payload.get("analysis")
        if isinstance(analysis, dict):
            answer = analysis.get("answer") or analysis.get("summary")
            if isinstance(answer, str):
                return answer
            if isinstance(answer, list):
                return "\n".join(str(item) for item in answer)
        metadata = payload.get("metadata", {})
        if isinstance(metadata, dict):
            visual = metadata.get("visual_analysis", {})
            if isinstance(visual, dict):
                status_block = visual.get("status", {})
                if isinstance(status_block, dict):
                    quick_summary = status_block.get("quick_summary")
                    if isinstance(quick_summary, dict):
                        answer = quick_summary.get("answer")
                        if isinstance(answer, str):
                            return answer
        return ""

    ###### UPLOAD#######################################################################
    @overload
    def upload(self, videos: VideoInput, /, *,
                folder: str | None = None,
                scope: FolderScopeLiteral = "user",
                upload_timeout: int = 1_200,
                wait_for_uploaded: bool = True
                ) -> Dict[str, Any]: ...

    @overload
    def upload(self, videos: Sequence[VideoInput], /, *,
                folder: str | None = None,
                scope: FolderScopeLiteral = "user",
                upload_timeout: int = 1_200,
                wait_for_uploaded: bool = True
                ) -> List[Dict[str, Any]]: ...

    def upload(self, videos: VideoInputs, /, *,
                folder: str | None = None,
                scope: FolderScopeLiteral = "user",
                upload_timeout: int = 1_200,
                wait_for_uploaded: bool = True,
                **_):  # swallow unknown kwargs for forward compat
    # noqa: E701 – keep signature readable
        """Upload one or many videos from local paths or URLs.

        Parameters
        ----------
        videos            : a single string/``Path`` or a sequence thereof, or URLs
        folder            : optional folder to organize videos
        scope             : "user" (default) or "org" scope hint for folder resolution
        upload_timeout    : seconds to wait in `_wait_for_uploaded`
        wait_for_uploaded : block until backend reports "UPLOADED"
        """
        resolved_folder_id: Optional[str] = None

        if folder:
            folder_payload = self.create_or_get_folder(folder, scope=scope)
            resolved_folder_id = folder_payload.get("id")

        if _is_iterable(videos):
            paths = list(videos)
            if not paths:
                raise ValueError("No paths provided")
            return self._upload_many(
                paths,
                upload_timeout,
                wait_for_uploaded,
                resolved_folder_id,
                scope,
            )
        return self._upload_single(
            videos,
            upload_timeout,
            wait_for_uploaded,
            resolved_folder_id,
            scope,
        )

    def create_or_get_folder(
        self,
        name: str,
        *,
        scope: FolderScopeLiteral = "user",
        org_id: str | None = None,
    ) -> Dict[str, Any]:
        """Guarantee a folder exists and return its metadata."""
        if not name or not name.strip():
            raise ValidationError("Folder name cannot be empty")

        scope_value = scope.lower()
        if scope_value not in {"user", "org"}:
            raise ValidationError(f"Unsupported scope '{scope}'")

        payload: Dict[str, Any] = {
            "name": name.strip(),
            "scope": scope_value,
        }
        if org_id:
            payload["org_id"] = org_id

        response = self.client._make_request(
            method="POST",
            endpoint="/api/folders/create-or-get",
            json_data=payload,
        )

        if not (200 <= response.status_code < 300):
            raise NomadicMLError(
                f"Failed to ensure folder: {format_error_message(response.json())}"
            )

        return response.json()

    #  ── helpers ──────────────────────────────────────────────────────
    def _upload_single(
        self,
        video: VideoInput,
        timeout: int,
        wait: bool,
        folder_id: str | None = None,
        scope: FolderScopeLiteral = "user",
    ) -> Dict[str, Any]:
        """Delegate to low‑level helper plus optional wait."""
        res = self._upload_video(
            file_path=str(video),
            folder_id=folder_id,
            scope=scope,
        )

        vid = res["video_id"]

        if wait:
            self._wait_for_uploaded(vid, timeout=timeout)
            res = self.get_video_status(vid)   # refreshed payload

        return self._parse_upload_response(vid, res)
    

    def _upload_many(self, videos: List[VideoInput],
                    timeout: int,
                    wait: bool,
                    folder_id: str | None = None,
                    scope: FolderScopeLiteral = "user") -> List[Dict[str, Any]]:
        """Parallel uploader with basic type checking.

        Raises **TypeError** if any item in *videos* is not a ``str`` or ``Path``.
        This helps catch accidental mistakes like ``[Path(...), True]`` where a
        bool sneaks into the list when the caller meant to pass a keyword arg.
        """
        for v in videos:
            if not isinstance(v, (str, Path)):
                raise TypeError(
                    "upload(videos=…) expects paths or strings – got %r of type %s" %
                    (v, type(v).__name__))

        # CONCURRENCY LIMIT: Only 4 uploads will run simultaneously
        # ThreadPoolExecutor internally maintains a queue of pending tasks.
        # Example: When uploading 50 videos:
        #   - ThreadPoolExecutor creates 4 worker threads (max_workers=4)
        #   - All 50 upload tasks are immediately submitted via exe.submit()
        #   - Each submit() returns a Future object and queues the task internally
        #   - First 4 tasks start executing immediately on the 4 threads
        #   - Remaining 46 tasks wait in ThreadPoolExecutor's internal queue
        #   - As each upload completes, that thread automatically picks the next task from queue
        #   - This continues until all 50 uploads are processed
        # 
        # This prevents overwhelming backend servers, proxies, and load balancers
        # with too many concurrent connections (which can cause timeouts/failures).
        # Using min(4, len(videos)) ensures we don't create unnecessary threads
        # when uploading fewer than 4 videos.
        with ThreadPoolExecutor(max_workers=min(4, len(videos))) as exe:
            futs = [
                exe.submit(
                    self._upload_single,
                    v,
                    timeout,
                    wait,
                    folder_id,
                    scope,
                )
                for v in videos
            ]
            
            # Collect results, handling individual failures gracefully
            results = []
            for i, f in enumerate(futs):
                try:
                    result = f.result()
                    results.append(result)
                except Exception as e:
                    # Log the failure but continue with other uploads
                    logger.error(f"Upload failed for video {i+1}/{len(videos)} ({videos[i]}): {e}")
                    results.append({
                        "video_id": None,
                        "status": "failed", 
                        "error": str(e),
                        "file_path": str(videos[i])
                    })
            return results  # preserves input order, includes both successes and failures

    ####################################### #ANALYZE #################


    #Single Video decorato
    @overload
    def analyze(
        self,
        ids: VideoID,
        /,
        *,
        analysis_type: AnalysisType,
        model_id: str = "Nomadic-VL-XLarge",
        timeout: int = 2_400,
        wait_for_completion: bool = True,
        folder: str | None = None,
        search_query: str | None = None,
        custom_event: str | None = None,
        custom_category: CustomCategory | str | None = None,
        concept_ids: List[str] | None = None,
        mode: str = "assistant",
        return_subset: bool = False,
        is_thumbnail: bool = False,
        use_enhanced_motion_analysis: bool = False,
        confidence: str = "low",
        custom_agent_id: str | None = None
    ) -> Dict[str, Any]: ...
    
    #Batch Analyze decorator
    @overload
    def analyze(
        self,
        ids: VideoIDList,
        /,
        *,
        analysis_type: AnalysisType,
        model_id: str = "Nomadic-VL-XLarge",
        timeout: int = 2_400,
        wait_for_completion: bool = True,
        folder: str | None = None,
        search_query: str | None = None,
        custom_event: str | None = None,
        custom_category: CustomCategory | str | None = None,
        concept_ids: List[str] | None = None,
        mode: str = "assistant",
        return_subset: bool = False,
        is_thumbnail: bool = False,
        use_enhanced_motion_analysis: bool = False,
        confidence: str = "low",
        custom_agent_id: str | None = None
    ) -> Dict[str, Any]: ...

    def analyze(
        self,
        ids: Union[VideoID, VideoIDList, None] = None,
        /,
        *,
        analysis_type: AnalysisType,
        model_id: str = "Nomadic-VL-XLarge",
        timeout: int = 2_400,
        wait_for_completion: bool = True,
        folder: str | None = None,
        search_query: str | None = None,
        custom_event: str | None = None,
        custom_category: CustomCategory | str | None = None,
        concept_ids: List[str] | None = None,
        mode: str = "assistant",
        return_subset: bool = False,
        is_thumbnail: bool = False,
        use_enhanced_motion_analysis: bool = False,
        confidence: str = "low",
        custom_agent_id: str | None = None,
        **legacy_kwargs,
    ):
        """Trigger analysis for one or many video IDs with explicit type.

        Returns a per-video dict for single analyses. When multiple IDs are
        supplied, the return value is a dictionary with ``results`` and
        ``batch_metadata`` keys (see :meth:`_analyze_many`).
        """
        if ids is None and folder is None:
            raise ValueError("Must provide either ids or folder")

        if folder and ids is not None:
            raise ValueError("Provide either ids or folder, not both")

        if confidence not in {"low", "high"}:
            raise ValueError("confidence must be 'low' or 'high'")

        unsupported_kwargs = {key for key in legacy_kwargs if key in {"agent_category", "edge_case_category"}}
        if unsupported_kwargs:
            raise ValueError(
                "Agent categories are now selected via `analysis_type`. "
                "Choose one of the predefined agent types in AnalysisType instead of passing "
                f"{', '.join(sorted(unsupported_kwargs))}."
            )

        analysis_type_enum = self._coerce_analysis_type(analysis_type)
        self._validate_kwargs(
            analysis_type_enum,
            search_query=search_query,
            custom_event=custom_event,
            custom_category=custom_category,
            custom_agent_id=custom_agent_id
        )

        if folder:
            vids_info = self.my_videos(folder_id=folder)
            ids = [v["video_id"] for v in vids_info]
            if not ids:
                raise ValueError(f"No videos found in folder '{folder}'")

        # vector dispatch
        if _is_iterable(ids):
            vids = list(ids)
            if not vids:
                raise ValueError("No video_ids provided")
            return self._analyze_many(
                vids,
                analysis_type_enum,
                model_id,
                timeout,
                wait_for_completion,
                search_query,
                custom_event,
                custom_category,
                concept_ids,
                return_subset,
                is_thumbnail,
                use_enhanced_motion_analysis,
                confidence=confidence,
                custom_agent_id=custom_agent_id
            )

        return self._analyze_single(
            ids,
            analysis_type_enum,
            model_id,
            timeout,
            wait_for_completion,
            search_query,
            custom_event,
            custom_category,
            concept_ids,
            mode,
            return_subset,
            is_thumbnail,
            use_enhanced_motion_analysis,
            confidence=confidence,
            custom_agent_id=custom_agent_id
        )

    #  ── analyze helpers ──────────────────────────────────────────────
    def _validate_kwargs(
        self,
        analysis_type: AnalysisType,
        *,
        search_query: str | None,
        custom_event: str | None,
        custom_category: CustomCategory | str | None,
        custom_agent_id: str | None = None
    ) -> None:
        """Ensure required kwargs are provided for each analysis type."""

        if search_query:
            import warnings
            warnings.warn(
                "analysis_type='search' and search_query parameter are deprecated and have been removed. "
                "Use analysis_type='rapid_review' with custom_event parameter instead "
                "for searching in videos of any length.",
                DeprecationWarning,
                stacklevel=3,
            )
            raise ValueError(
                "analysis_type='search' and search_query parameter have been removed. "
                "Use analysis_type='rapid_review' with custom_event=<your_search_query> instead."
            )

        if analysis_type == AnalysisType.ASK:
            if not custom_event:
                raise ValueError("custom_event is required when analysis_type='ask'")
            if custom_category is None:
                raise ValueError("custom_category is required when analysis_type='ask'")
            if isinstance(custom_category, str) and custom_category not in [cat.value for cat in CustomCategory]:
                valid_values = ", ".join([f"'{cat.value}'" for cat in CustomCategory])
                raise ValueError(f"custom_category must be one of {valid_values}")
            return

        if analysis_type == AnalysisType.CUSTOM_AGENT:
            if not custom_agent_id:
                raise ValueError("custom_agent_id is required when analysis_type='custom_agent'")
            return

        if analysis_type in self._AGENT_DEFAULTS:
            if custom_event is not None:
                raise ValueError("custom_event is only valid for AnalysisType.ASK")
            if custom_category is not None:
                raise ValueError("custom_category is only valid for AnalysisType.ASK")
            return

        supported = ", ".join(sorted({AnalysisType.ASK.name, *[agent.name for agent in self._AGENT_DEFAULTS]}))
        raise ValueError(f"Unsupported analysis type '{analysis_type}'. Supported types: {supported}")

    def _coerce_analysis_type(self, analysis_type: AnalysisType | str) -> AnalysisType:
        """Return the canonical :class:`AnalysisType` for user-provided input."""

        if isinstance(analysis_type, AnalysisType):
            return analysis_type

        alias_map = {
            "ask": AnalysisType.ASK,
            "general": AnalysisType.GENERAL_AGENT,
            "general_agent": AnalysisType.GENERAL_AGENT,
            "general-edge-case": AnalysisType.GENERAL_AGENT,
            "edge_case_agent": AnalysisType.GENERAL_AGENT,
            "lane_change": AnalysisType.LANE_CHANGE,
            "lane-change": AnalysisType.LANE_CHANGE,
            "lane_change_agent": AnalysisType.LANE_CHANGE,
            "turn": AnalysisType.TURN,
            "turn_agent": AnalysisType.TURN,
            "relative_motion": AnalysisType.RELATIVE_MOTION,
            "relative-motion": AnalysisType.RELATIVE_MOTION,
            "relative_motion_agent": AnalysisType.RELATIVE_MOTION,
            "driving_violations": AnalysisType.DRIVING_VIOLATIONS,
            "driving-violations": AnalysisType.DRIVING_VIOLATIONS,
            "violation_agent": AnalysisType.DRIVING_VIOLATIONS,
        }

        lookup = str(analysis_type or "").lower()
        if lookup in alias_map:
            return alias_map[lookup]

        for member in AnalysisType:
            if member.value == lookup or member.name.lower() == lookup:
                return member

        valid_values = sorted({member.name for member in AnalysisType} | set(alias_map.keys()))
        raise ValueError(f"analysis_type must be one of {', '.join(valid_values)}")

    def _analyze_single(
        self,
        video_id: str,
        analysis_type: AnalysisType,
        model_id: str,
        timeout: int,
        wait_for_completion: bool,
        search_query: str | None = None,
        custom_event: str | None = None,
        custom_category: CustomCategory | str | None = None,
        concept_ids: list[str] | None = None,
        mode: str = "assistant",
        return_subset: bool = True,
        is_thumbnail: bool = False,
        use_enhanced_motion_analysis: bool = False,
        _config: str = "default",
        confidence: str = "low",
        custom_agent_id: str | None = None,
    ) -> dict:
        """Run ONE analysis job and hand back a compact dict."""

        # 1) sanity-check combo of flags
        self._validate_kwargs(
            analysis_type,
            search_query=search_query,
            custom_event=custom_event,
            custom_category=custom_category,
            custom_agent_id=custom_agent_id
        )

        analysis_type_enum = analysis_type

        # 2) dispatch by AnalysisType

        if analysis_type_enum == AnalysisType.ASK or analysis_type_enum == AnalysisType.CUSTOM_AGENT:

            if analysis_type_enum == AnalysisType.ASK:
                response = self._custom_event_detection(
                    video_id=video_id,
                    custom_category=custom_category,
                    event_description=custom_event,
                    is_thumbnail=is_thumbnail,
                    use_enhanced_motion_analysis=use_enhanced_motion_analysis,
                    _config=_config,
                    confidence=confidence,
                )
            else:
                response = self._custom_event_detection(
                    event_description='',
                    custom_category='',
                    video_id=video_id,
                    _config=_config,
                    custom_agent_id=custom_agent_id
                )

            
            # For is_thumbnail=True, try to fetch thumbnail URLs
            events = response.get("suggested_events", [])
            analysis_id = response.get("analysis_id")
            
            if is_thumbnail and analysis_id and events:
                try:
                    # Get thumbnails for all events
                    thumbnail_urls = self.get_visuals(video_id, analysis_id)
                    # Add thumbnail URLs to events if we got them
                    if thumbnail_urls and len(thumbnail_urls) == len(events):
                        for i, event in enumerate(events):
                            if isinstance(event, dict) and i < len(thumbnail_urls):
                                event["annotated_thumbnail_url"] = thumbnail_urls[i]
                except Exception as e:
                    logger.warning(f"Failed to fetch thumbnails: {e}")
            
            return {
                "video_id": video_id,
                "analysis_id": analysis_id,
                "mode":     "rapid_review",
                "status":   "completed",
                "summary":  response.get("answer", ""),
                "events":   events,
            }

        if analysis_type_enum in self._AGENT_DEFAULTS:
            mode_label = "agent"
            result = self.analyze_video_edge(
                video_id=video_id,
                agent_type=analysis_type_enum,
                model_id=model_id,
                concept_ids=concept_ids,
                _config=_config,
            )
            analysis_id = result.get("analysis_id")

            if not wait_for_completion:
                return {
                    "video_id": video_id,
                    "mode": mode_label,
                    "status": "started",
                    "analysis_id": analysis_id,
                }

            self.wait_for_analysis(video_id, timeout=timeout, analysis_id=analysis_id)
            payload = self.get_video_analysis(video_id, analysis_id=analysis_id)
            events = self._parse_api_events(payload, analysis_type=analysis_type_enum)

            return {
                "video_id": video_id,
                "mode": mode_label,
                "status": "completed",
                "events": events,
                "analysis_id": analysis_id,
            }

        raise ValueError(f"Unsupported analysis type '{analysis_type_enum}'")


# ───────────────────────── analyze (many) ───────────────────────────
    def _analyze_many(
        self,
        video_ids: list[str],
        analysis_type: AnalysisType,
        model_id: str,
        timeout: int,
        wait_for_completion: bool,
        search_query: str | None,
        custom_event: str | None,
        custom_category: CustomCategory | str | None,
        concept_ids: list[str] | None,
        return_subset: bool,
        is_thumbnail: bool = False,
        use_enhanced_motion_analysis: bool = False,
        _config: str = "default",
        confidence: str = "low",
        custom_agent_id: str | None = None,
    ) -> Dict[str, Any]:
        """Route multi-video analyses through backend batch orchestration.

        Returns a dictionary with two keys:

        * ``batch_metadata`` – batch identifier plus viewer links.
        * ``results`` – list of per-video analysis dictionaries in the same
          format as :meth:`_analyze_single`.
        """

        if search_query:
            raise ValueError(
                "Batch analyses do not support the deprecated search_query parameter. "
                "Use custom_event with analysis_type='rapid_review' instead."
            )

        mode_label, form_entries = self._prepare_batch_form(
            video_ids,
            analysis_type=analysis_type,
            custom_event=custom_event,
            custom_category=custom_category,
            concept_ids=concept_ids,
            model_id=model_id,
            is_thumbnail=is_thumbnail,
            use_enhanced_motion_analysis=use_enhanced_motion_analysis,
            _config=_config,
            confidence=confidence,
            custom_agent_id=custom_agent_id
        )

        batch_response = self._submit_batch(form_entries)
        batch_id = batch_response["batch_id"]
        links = self._build_batch_viewer_links(batch_id)
        logger.info(
            "Started batch %s (%s videos) for analysis_type=%s", batch_id,
            len(video_ids), getattr(analysis_type, "value", analysis_type)
        )

        batch_type = "ask" if mode_label == "rapid_review" else "agent"
        batch_metadata = {
            "batch_id": batch_id,
            "batch_viewer_url": links["url"],
            "batch_type": batch_type,
        }

        # Fast acknowledgement path
        if not wait_for_completion:
            ack = []
            for vid in video_ids:
                ack.append({
                    "video_id": vid,
                    "analysis_id": None,
                    "mode": mode_label,
                    "status": "started",
                })
            return {
                "batch_metadata": batch_metadata,
                "results": ack,
            }

        multiplier = max(1, len(video_ids))
        poll_budget = timeout * multiplier if timeout and timeout > 0 else 2400
        # Poll batch status until orchestrator finishes fan-out and harvest per-video pointers.
        batch_status_payload = self._poll_batch_status(batch_id, timeout=int(poll_budget))

        pointer_map: Dict[str, Dict[str, Any]] = {}
        for entry in batch_status_payload.get("videos", []) or []:
            video_id_value = entry.get("video_id")
            if video_id_value:
                pointer_map[str(video_id_value)] = entry

        missing_pointer_error = "Batch orchestrator did not provide analysis pointer for video"
        results: list[dict] = []
        for vid in video_ids:
            pointer = pointer_map.get(vid)
            if not pointer:
                results.append({
                    "video_id": vid,
                    "mode": mode_label,
                    "status": "failed",
                    "events": [],
                    "analysis_id": None,
                    "error": missing_pointer_error,
                })
                continue

            pointer_status_raw = pointer.get("status")
            pointer_status = str(pointer_status_raw).lower() if pointer_status_raw else None
            analysis_id = pointer.get("analysis_id")
            pointer_error = pointer.get("last_error")

            if not analysis_id:
                failure_status = pointer_status if pointer_status == "failed" else "failed"
                results.append({
                    "video_id": vid,
                    "mode": mode_label,
                    "status": failure_status,
                    "events": [],
                    "analysis_id": None,
                    "error": pointer_error or missing_pointer_error,
                })
                continue

            detailed_payload: Dict[str, Any]
            try:
                detailed_payload = self.get_video_analysis(vid, analysis_id=analysis_id)
            except Exception as exc:  # noqa: BLE001 - surface unexpected issues to caller
                results.append({
                    "video_id": vid,
                    "mode": mode_label,
                    "status": pointer_status or "failed",
                    "events": [],
                    "analysis_id": analysis_id,
                    "error": pointer_error or str(exc),
                })
                continue

            events = self._parse_api_events(detailed_payload, analysis_type=analysis_type)
            status_value = self._status_from_metadata(detailed_payload.get("metadata", {}))
            if not status_value and isinstance(detailed_payload.get("analysis"), dict):
                status_value = detailed_payload.get("analysis", {}).get("status")
            status_value = (status_value or pointer_status or "completed").lower()
            if status_value not in {"completed", "failed"}:
                status_value = "completed"

            result_entry: Dict[str, Any] = {
                "video_id": vid,
                "analysis_id": analysis_id or self._extract_analysis_id(detailed_payload),
                "mode": mode_label,
                "status": status_value,
            }

            if mode_label == "rapid_review":
                summary_text = self._extract_summary(detailed_payload) or ""
                result_entry["summary"] = summary_text

            result_entry["events"] = events

            if status_value == "failed":
                result_entry.setdefault("error", pointer_error or "Analysis failed")

            results.append(result_entry)

        return {
            "batch_metadata": batch_metadata,
            "results": results,
        }
    #########################


    def _upload_video(
        self,
        file_path: str,
        *,
        folder_id: Optional[str] = None,
        scope: FolderScopeLiteral = "user",
        # ¦ deprecated ------------------------------------------------------
        source: Union[str, VideoSource, None] = None,
     ) -> Dict[str, Any]:
        """
        Upload a video for analysis.
        
        Args:
            file_path: Local path or remote URL of the video.
            folder_id: Optional id of the folder to organize the video.
            source: Deprecated. Ignored by the SDK.
        
        Returns:
            A dictionary with the upload status and video_id.
        
        Raises:
            ValidationError: If the input parameters are invalid.
            VideoUploadError: If the upload fails.
            APIError: If the API returns an error.
            NomadicMLError: For any other errors.
        """
        if source is not None:
            logger.warning("'source' parameter is deprecated and ignored; the SDK infers the source automatically.")
        
        if not file_path:
            raise ValidationError("Must provide file_path")

        # ── determine source type -----------------------------------------
        inferred_source = infer_source(file_path)
        
        # Only support FILE and VIDEO_URL, not SAVED
        if inferred_source == VideoSource.SAVED:
            raise ValidationError("Cannot upload from saved video ID. Use analyze() to analyze existing videos.")

        # Prepare request data ----------------------------------------------
        endpoint = "/api/upload-video"

        form_data: Dict[str, Any] = {
            "source": inferred_source.value,
            "firebase_collection_name": self.client.collection_name,
            "scope": scope,
        }
        if folder_id:
            form_data["folder_id"] = folder_id
        files = None

        if inferred_source == VideoSource.FILE:
            filename = get_filename_from_path(file_path)
            mime_type = get_file_mime_type(file_path)
            with open(file_path, "rb") as f:
                file_content = f.read()
            files = {"file": (filename, file_content, mime_type)}
            logger.info(f"Uploading local file: {filename}")
        elif inferred_source == VideoSource.VIDEO_URL:
            form_data["video_url"] = file_path
            logger.info(f"Uploading by URL: {file_path}")

        # Make the request ---------------------------------------------------
        response = self.client._make_request(
            method="POST",
            endpoint=endpoint,
            data=form_data,
            files=files,
            timeout=self.client.timeout * 20,
        )

        if not (200 <= response.status_code < 300):
            raise VideoUploadError(f"Failed to upload video: {format_error_message(response.json())}")

        logger.info(f"Upload (source={inferred_source.value}) response: {response.json()}")

        return response.json()

    def analyze_video(self, video_id: str, model_id: Optional[str] = "Nomadic-VL-XLarge") -> Dict[str, Any]:
        """
        Start analysis for an uploaded video.
        
        Args:
            video_id: The ID of the video to analyze.
            
        Returns:
            A dictionary with the analysis status.
            
        Raises:
            AnalysisError: If the analysis fails to start.
            APIError: If the API returns an error.
            NomadicMLError: For any other errors.
        """
        endpoint = f"/api/analyze-video/{video_id}"
        
        # Prepare form data with the collection name
        data = {
            "firebase_collection_name": self.client.collection_name,
            "model_id": model_id,
        }
        
        # Make the request
        response = self.client._make_request(
            method="POST",
            endpoint=endpoint,
            data=data,
        )
        
        # Return the parsed JSON response
        return response.json()

    def analyze_video_edge(
        self,
        video_id: str,
        agent_type: AnalysisType,
        *,
        model_id: str = "Nomadic-VL-XLarge",
        concept_ids: Optional[Sequence[str]] = None,
        _config: str = "default",
    ) -> Dict[str, Any]:
        """Start an agent (edge-case) analysis for an uploaded video."""

        if agent_type not in self._AGENT_DEFAULTS:
            supported = ", ".join(sorted(agent.name for agent in self._AGENT_DEFAULTS))
            raise ValueError(f"Unsupported agent type '{agent_type}'. Supported options: {supported}")

        endpoint = f"/api/analyze-video-edge/{video_id}"
        data = self._build_agent_request(
            agent_type,
            model_id=model_id,
            concept_ids=concept_ids,
            _config=_config,
        )

        response = self.client._make_request(
            method="POST",
            endpoint=endpoint,
            data=data,
        )
        return response.json()
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        Get the status of a video analysis.
        
        Args:
            video_id: The ID of the video.
            
        Returns:
            A dictionary with the video status.
            
        Raises:
            APIError: If the API returns an error.
            NomadicMLError: For any other errors.
        """
        endpoint = f"/api/video/{video_id}/status"
        
        # Add the required collection_name parameter
        params = {"firebase_collection_name": self.client.collection_name}
        
        # Make the request
        response = self.client._make_request("GET", endpoint, params=params)
        
        # Return the parsed JSON response
        return response.json()
        
    def wait_for_analysis(
        self,
        video_id: str,
        timeout: int = 2_400, # Default 40 minutes
        poll_interval: int = 5,
        analysis_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Block until the video analysis completes or times out.
        
        Args:
            video_id: The ID of the video to wait for.
            timeout: Maximum time to wait in seconds before raising TimeoutError.
            poll_interval: Time between status checks in seconds.
            analysis_id: Optional analysis ID for new EC analyses stored in separate docs.
            
        Returns:
            A dictionary with the final video status payload.
            
        Raises:
            TimeoutError: If the analysis doesn't complete within the timeout period.
        """
        start_time = time.time()
        
        # For new edge case analyses with analysis_id, we need to poll differently
        if analysis_id:
            while True:
                # Get the full analysis document which includes status
                payload = self.get_video_analysis(video_id, analysis_id=analysis_id)
                # Check if analysis document exists and has status
                if "analysis" in payload and "status" in payload["analysis"]:
                    status = str(payload["analysis"]["status"]).upper()
                else:
                    # Fallback to metadata status for compatibility
                    status = self._status_from_metadata(payload.get("metadata", {})) or "PROCESSING"
                    status = status.upper()
                
                self._print_status_bar(f"{video_id}:{analysis_id}", status=status)
                logger.debug(f"Analysis {analysis_id} for video {video_id} - Status: '{status}'")
                
                if status in {"COMPLETED", "FAILED"}:
                    logger.info(f"Analysis {analysis_id} reached terminal status: {status}.")
                    return payload
                    
                if time.time() - start_time > timeout:
                    msg = f"Analysis {analysis_id} for {video_id} did not complete in {timeout}s. Last status: {status}"
                    logger.error(msg)
                    raise TimeoutError(msg)
                    
                time.sleep(poll_interval)
        else:
            # Legacy behavior for analyses without analysis_id
            while True:
                payload = self.get_video_status(video_id)
                status = str(payload.get("status", "")).upper()
                self._print_status_bar(video_id, status=status)
                logger.debug(f"Video {video_id} - Status: '{status}', payload: '{payload}'")
                
                if status in {"COMPLETED", "FAILED"}:
                    logger.info(f"Video {video_id} reached terminal status: {status}.")
                    return payload
                    
                if time.time() - start_time > timeout:
                    msg = f"Analysis for {video_id} did not complete in {timeout}s. Last status: {status}"
                    logger.error(msg)
                    raise TimeoutError(msg)
                    
                time.sleep(poll_interval)

    def wait_for_analyses(
        self,
        video_ids,
        timeout: int = 4800,
        poll_interval: int = 5
    ) -> dict:
        """
        Wait for multiple video analyses in parallel, with pretty status bars.
        """
        ids = list(video_ids)
        results = {}
        with ThreadPoolExecutor(max_workers=len(ids)) as executor:
            futures = {executor.submit(self.wait_for_analysis, vid, timeout, poll_interval): vid for vid in ids}
            for fut in as_completed(futures):
                vid = futures[fut]
                try:
                    results[vid] = fut.result()
                except Exception as e:
                    results[vid] = e
        return results
    
    def get_video_analysis(self, video_id: str, analysis_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the complete analysis of a video.
        
        Args:
            video_id: The ID of the video.
            analysis_id: Optional analysis ID for new EC analyses stored in separate docs.
            
        Returns:
            The complete video analysis. For new analyses with analysis_id, includes
            both metadata and the analysis document.
            
        Raises:
            APIError: If the API returns an error.
            NomadicMLError: For any other errors.
        """
        if analysis_id:
            # Use the new endpoint for fetching analysis documents
            endpoint = f"/api/videos/{video_id}/analyses/{analysis_id}"
            params = {"firebase_collection_name": self.client.collection_name}
            
            response = self.client._make_request(
                method="GET",
                endpoint=endpoint,
                params=params,
            )
            
            return response.json()
        else:
            # Use the original endpoint for legacy analyses
            endpoint = f"/api/video/{video_id}/analysis"
            params = {"firebase_collection_name": self.client.collection_name}
                    
            response = self.client._make_request(
                method="GET",
                endpoint=endpoint,
                params=params,
            )
            
            return response.json()
    
    def get_video_analyses(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get analyses for multiple videos.
        
        Args:
            video_ids: List of video IDs.
            
        Returns:
            A list of analyses for each video.
            
        Raises:
            APIError: If the API returns an error.
            NomadicMLError: For any other errors.
        """
        analyses = []
        for vid in video_ids:
            analysis = self.get_video_analysis(vid)
            analyses.append(analysis)
        return analyses
    
    def get_detected_events(self, video_id: str) -> List[Dict[str, Any]]:
        """
        Get detected events for a video.

        Args:
            video_id: The ID of the video.

        Returns:
            A list of detected events.

        Raises:
            APIError: If the API returns an error.
            NomadicMLError: For any other errors.
        """
        return self._parse_api_events(self.get_video_analysis(video_id))

    def get_batch_analysis(
        self,
        batch_id: str,
        filter: Optional[Union[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Get the analysis results for a completed batch by batch_id.

        Args:
            batch_id: The ID of the batch to retrieve.
            filter: Filter events by approval status. Can be a single string or list of strings.
                   Valid values: 'approved', 'rejected', 'pending', 'invalid'.
                   Defaults to all statuses if not specified.

        Returns:
            A dictionary with 'batch_metadata' and 'results' keys.
            - batch_metadata: Contains batch_id, batch_viewer_url, batch_type, analysis_type,
                            and configuration details (prompt, category, etc for Ask batches)
            - results: List of per-video analysis dictionaries with filtered events

        Raises:
            NomadicMLError: If batch is not completed or other errors occur.
            ValidationError: If filter contains invalid values.
        """
        # Validate and normalize filter parameter
        if filter is None:
            filter_list = None  # Backend will use default
        elif isinstance(filter, str):
            filter_list = [filter]
        else:
            filter_list = list(filter)

        # Basic validation before sending to backend
        if filter_list is not None:
            valid_filters = {'approved', 'rejected', 'pending', 'invalid'}
            invalid_filters = set(filter_list) - valid_filters
            if invalid_filters:
                raise ValidationError(
                    f"Invalid filter value(s): {', '.join(invalid_filters)}. "
                    f"Must be one of: approved, rejected, pending, invalid"
                )

        # Call the new backend endpoint that handles all the filtering logic
        payload = {"filter": filter_list}

        response = self.client._make_request(
            method="POST",
            endpoint=f"/api/batch/{batch_id}/filter_batch",
            json_data=payload,
        )

        return response.json()

    # ------------------------------------------------------------------
    # Semantic search across multiple videos
    # ------------------------------------------------------------------

    def search(
        self,
        *,
        query: str,
        folder_name: str,
        scope: FolderScopeLiteral = "user",
    ) -> Dict[str, Any]:
        """Search across videos in a folder for a natural language query.

        Args:
            query: Natural language search query.
            folder_name: Human-friendly folder name that the videos belong to.
            scope: Folder scope hint ("user", "org", or "sample").

        Returns:
            Dict containing summary, chain-of-thought entries, matches, and session metadata.

        Raises:
            NomadicMLError: For API errors or failed searches.
        """

        if not query or not query.strip():
            raise NomadicMLError("Search query cannot be empty")
        if not folder_name or not folder_name.strip():
            raise NomadicMLError("Folder name is required for search")

        scope_map = {
            "user": "my",
            "org": "org",
            "sample": "sample",
        }

        session_scope = scope_map.get(scope, "my")

        # 1) Initialize a search session so we can collect reasoning + results from Firestore
        start_payload = {
            "query": query,
            "folder_name": folder_name,
            "scope": session_scope,
        }

        start_resp = self.client._make_request(
            "POST",
            "/api/search-sessions/start",
            json_data=start_payload,
        )
        session_info = start_resp.json()
        session_id = session_info.get("session_id")
        owner_uid = session_info.get("owner_uid")
        session_doc_path = session_info.get("session_doc_path")
        reasoning_trace_path = session_info.get("reasoning_trace_path", session_doc_path)

        if not (session_id and owner_uid and session_doc_path):
            raise NomadicMLError("Failed to initialize search session")

        # 2) Trigger the backend search (writes results into the session document)
        form_data = {
            "query": query,
            "folder": folder_name,
            "session_id": session_id,
            "session_doc_path": session_doc_path,
            "reasoning_trace_path": reasoning_trace_path,
        }
        if session_scope == "sample":
            form_data["is_sample_videos"] = "true"

        # Remove empty values to avoid confusing FastAPI's Form parsing
        form_data = {k: v for k, v in form_data.items() if v}

        self.client._make_request(
            "POST",
            "/api/search",
            params={"folder_collection": session_scope},
            data=form_data,
        )

        # 3) Poll the session document until the search completes
        poll_endpoint = f"/api/search-sessions/{owner_uid}/{session_id}"
        started_at = time.time()
        delay = 1.0
        max_delay = 10.0

        while True:
            session_resp = self.client._make_request("GET", poll_endpoint)
            payload = session_resp.json()
            data = payload.get("data", {})
            status = (data.get("status") or "").lower()

            if status == "completed":
                raw_matches = data.get("matches") or []
                summary = data.get("summary") or ""
                thoughts = data.get("thoughts") or []

                normalized_matches: List[Dict[str, Any]] = []
                for entry in raw_matches:
                    if not isinstance(entry, dict):
                        continue
                    normalized_matches.append({
                        "video_id": entry.get("video_id"),
                        "analysis_id": entry.get("analysis_id"),
                        "event_index": entry.get("event_index"),
                        "similarity": entry.get("similarity"),
                        "reason": entry.get("reason", ""),
                    })

                return {
                    "summary": summary,
                    "thoughts": thoughts,
                    "matches": normalized_matches,
                    "session_id": session_id,
                }

            if status == "failed":
                error_message = data.get("error") or data.get("error_message") or "Search failed"
                raise NomadicMLError(error_message)

            elapsed = time.time() - started_at
            if elapsed > self.client.timeout:
                raise TimeoutError("Timed out waiting for search results")

            time.sleep(delay)
            delay = min(delay * 1.5, max_delay)

    ###############
    # ──────────────── Deprecated Methods ────────────────────────────────────────
    ###############

    def apply_search(self, parent_id: str, query: str,
                    model_id: str = "Nomadic-VL-XLarge") -> Dict[str, Any]:
        """
        DEPRECATED: This method has been removed.
        Use analyze() with analysis_type='rapid_review' instead.
        """
        raise NomadicMLError(
            "apply_search has been deprecated. Use analyze() with analysis_type='rapid_review' instead, "
            "which now supports all video lengths including long videos."
        )


    def _get_analysis_status(self, video_id: str, analysis_id: str) -> Dict[str, Any]:
        """Get the current status of a rapid review analysis."""
        params = {"collection": self.client.collection_name}
        r = self.client._make_request(
            "GET", f"/api/videos/{video_id}/analyses/{analysis_id}/status", params=params
        )
        if r.status_code >= 400:
            raise NomadicMLError(format_error_message(r.json()))
        return r.json()


    def _wait_for_rapid_review(self, video_id: str, analysis_id: str,
                              timeout: int = 3_600, poll_interval: int = 5,
                              is_thumbnail: bool = False) -> Dict[str, Any]:
        """Wait for a rapid review analysis to complete and return the final result."""
        start = time.time()
        while True:
            p = self._get_analysis_status(video_id, analysis_id)
            status = (p.get("status") or "").upper()
            
            # Calculate progress from either chunks ratio or progress field
            if p.get("chunks_completed") and p.get("chunks_total"):
                progress = (p.get("chunks_completed") / p.get("chunks_total")) * 100
            else:
                progress = float(p.get("progress", 0))
            
            self._print_status_bar(f"RapidReview:{analysis_id}",
                        percent=progress)
            
            if status == "COMPLETED":
                # Convert UI events back to RapidReviewEvent format
                ui_events = p.get("events", [])
                converted_events = []
                
                # Handle events that might be in UI format from Firebase
                for event in ui_events:
                    # Check if event is already in UI format (has 'type' and 'time' fields)
                    if isinstance(event, dict) and "type" in event and "time" in event:
                        # Convert from UI format to RapidReviewEvent format
                        converted_event = self._convert_ui_event_to_rapid_review(event)
                        if converted_event:
                            converted_events.append(converted_event)
                    else:
                        # Event might already be in correct format or different format
                        converted_events.append(event)
                
                # Handle answer field - could be string or array
                answer = p.get("answer", "")
                if isinstance(answer, list):
                    # Join array elements into a single string
                    answer = "\n".join(answer)
                
                # Fetch thumbnails if requested and events exist
                if is_thumbnail and converted_events:
                    try:
                        # Get thumbnails for all events
                        thumbnail_urls = self.get_visuals(video_id, analysis_id)
                        # Add thumbnail URLs to events if we got them
                        if thumbnail_urls and len(thumbnail_urls) == len(converted_events):
                            for i, event in enumerate(converted_events):
                                if isinstance(event, dict) and i < len(thumbnail_urls):
                                    event["annotated_thumbnail_url"] = thumbnail_urls[i]
                    except Exception as e:
                        logger.warning(f"Failed to fetch thumbnails: {e}")
                
                # Return the final result in the expected format
                return {
                    "answer": answer,
                    "suggested_events": converted_events,
                    "video_id": video_id,
                    "analysis_id": analysis_id,
                    "status": "completed"
                }
            if status == "FAILED":
                raise NomadicMLError(f"Rapid review analysis failed for {analysis_id}")
            if time.time() - start > timeout:
                raise TimeoutError(f"Rapid review {analysis_id} timed-out after {timeout}s")
            time.sleep(poll_interval)


    def my_videos(self, folder_id: str | None = None) -> List[Dict[str, Any]]:
        params = {
            "firebase_collection_name": self.client.collection_name,
            "folder_collection": self.client.folder_collection_name
        }
        if folder_id:
            params["folder"] = folder_id
        resp = self.client._make_request("GET", "/api/my-videos", params=params)
        return resp.json().get("videos", [])

    def delete_video(self, video_id: str) -> Dict[str, Any]:
        params = {"firebase_collection_name": self.client.collection_name}
        resp = self.client._make_request("DELETE", f"/api/video/{video_id}", params=params)
        return resp.json()
    

    # ─────────────────────── wait until status == UPLOADED ───────────── CHANGED
    def _wait_for_uploaded(self,
                           video_id: str,
                           timeout: int = 1200,
                           initial_delay: int = 15,
                           max_delay: int = 30,
                           multiplier: int = 2) -> None:
        """Block until video upload is finished.

        Handles both single videos and chunked uploads. When ``chunks_total`` is
        present in metadata, this waits until all chunks are reported as
        uploaded; otherwise it waits for ``visual_analysis.status.status`` to become
        ``UPLOADED``.
        """
        delay = initial_delay
        deadline = time.time() + timeout

        while True:
            payload = self.get_video_status(video_id)
            meta = payload.get("metadata", {})

            state = (self._status_from_metadata(meta) or "").upper()
            total = meta.get("chunks_total")
            uploaded = meta.get("chunks_uploaded", 0)

            if isinstance(total, int) and total > 0:
                if uploaded >= total:
                    logger.info(f"Upload completed for video {video_id}")
                    return
            elif state == "UPLOADED":
                logger.info(f"Upload completed for video {video_id}: status={state}")
                return

            if state in ("UPLOADING_FAILED", "FAILED"):
                raise VideoUploadError(f"Upload failed (backend status={state})")
            if time.time() > deadline:
                raise TimeoutError(f"Backend never reached UPLOADED in {timeout}s")

            sleep_for = max(0, delay + random.uniform(-1, 1))
            time.sleep(sleep_for)

            delay = min(delay * multiplier, max_delay)
            
    def upload_and_analyze(self,*args, **kwargs):
        raise NotImplementedError(
            "Deprecated: Use separate upload() and analyze() calls instead. "
            "See documentation for examples: https://docs.nomadicml.com/api-reference/sdk-examples"
        )

    def _status_from_metadata(self, meta: dict) -> Optional[str]:
        """
        Return the processing state stored in the scalar Firestore field
        `visual_analysis.status.status`.
        """
        return meta.get("visual_analysis", {}).get("status", {}).get("status")
    
    def get_visuals(self, video_id: str, analysis_id: str) -> List[str]:
        """
        Get all visual thumbnail URLs from an analysis.
        Automatically generates them if they don't exist.
        
        Args:
            video_id: The ID of the video
            analysis_id: The ID of the analysis
            
        Returns:
            List of thumbnail URLs for all events
        """
        # Call the generate-thumbnails endpoint which will:
        # 1. Check if thumbnails already exist
        # 2. Generate them if they don't
        # 3. Return all events with thumbnail URLs
        logger.info(f"Getting visuals for video {video_id}, analysis {analysis_id}")
        endpoint = f"/api/videos/{video_id}/analyses/{analysis_id}/generate-thumbnails"
        data = {"firebase_collection_name": self.client.collection_name}
        
        response = self.client._make_request(
            method="POST",
            endpoint=endpoint,
            data=data
        )
        
        result = response.json()
        events = result.get("events", [])
        
        if not events:
            logger.warning("No events found in analysis")
            return []
        
        thumbnail_urls = [event.get("annotated_thumbnail_url", "") for event in events]
        # Filter out any empty URLs
        thumbnail_urls = [url for url in thumbnail_urls if url]
        
        logger.info(f"Retrieved {len(thumbnail_urls)} thumbnail URLs")
        return thumbnail_urls
    
    def get_visual(self, video_id: str, analysis_id: str, event_idx: int) -> str:
        """
        Get a single visual thumbnail URL for a specific event.
        Automatically generates thumbnails if needed.

        Args:
            video_id: The ID of the video
            analysis_id: The ID of the analysis
            event_idx: The index of the event (0-based)

        Returns:
            Single thumbnail URL for the specified event

        Raises:
            ValueError: If the event index is out of range
        """
        visuals = self.get_visuals(video_id, analysis_id)

        if not visuals:
            raise ValueError(f"No visuals found for video {video_id}, analysis {analysis_id}")

        if event_idx < 0 or event_idx >= len(visuals):
            raise ValueError(
                f"Event index {event_idx} out of range. "
                f"Valid range: 0-{len(visuals)-1}"
            )

        return visuals[event_idx]

    def create_agent(
        self,
        name: str,
        batch_ids: List[str] = [],
        analysis_ids: List[str] = [],
        wait_for_completion: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a fine-tuned agent using batch analysis data.

        Args:
            batch_ids: List of batch IDs to use as training data
            name: Name for the agent being created
            wait_for_completion: Whether to wait for the optimization job to complete (default: False)

        Raises:
            NomadicMLError: If the API request fails
            AuthenticationError: If user is not an admin
            ValidationError: If any batch has insufficient approved or rejected events

        Example:
            >>> client = NomadicML(api_key="your_api_key")
            >>> result = client.video.create_agent(
            ...     batch_ids=["batch_123", "batch_456"],
            ...     name="My Lane Change Agent",
            ...     wait_for_completion=False
            ... )
            >>> print(f"Agent training job started: {result['job_id']}")
        """
        if not batch_ids and not analysis_ids:
            raise ValueError("At least one batch_id or analysis_id must be provided")

        if not name or not name.strip():
            raise ValueError("Agent name must be provided and cannot be empty")

        payload = {
            "batch_ids": batch_ids,
            "analysis_ids": analysis_ids,
            "name": name,
            "wait_for_completion": wait_for_completion,
        }

        logger.info(f"Creating agent from {len(batch_ids)} batch(es) and {len(analysis_ids)} analysis(es)")

        response = self.client._make_request(
            method="POST",
            endpoint="/api/create-agent",
            json_data=payload,
            timeout=10_800,  # 3 hours
        )

        if not (200 <= response.status_code < 300):
            raise NomadicMLError(
                f"Failed to create agent: {format_error_message(response.json())}"
            )

        result = response.json()
        logger.info(f"Agent training job submitted: {result.get('job_id')}")

        return result
