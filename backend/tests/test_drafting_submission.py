"""
Tests for Drafting Agent and Submission Agent.
Uses mocked Gemini and STUB integration clients.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.base import AgentInput
from agents.drafting import DraftingAgent
from agents.submission import SubmissionAgent, MILESTONES


def _base_drafting_input(bundled: bool = False) -> dict:
    crowd = {
        "is_bundled": bundled,
        "member_count": 11 if bundled else 1,
        "cluster_id": "cluster-abc" if bundled else None,
        "aggregated_description": "Multiple potholes reported by residents" if bundled else None,
    }
    return {
        "complaint_id": "cmp-test-001",
        "issue_type": "pothole",
        "severity": 4,
        "description": "Large pothole near MSRIT gate",
        "location": {
            "ward_number": 95, "ward_name": "Malleshwaram",
            "zone": "West", "address": "Near MSRIT, Bengaluru",
        },
        "routing": {
            "primary_agency": {"name": "BBMP", "department": "Roads"},
            "twitter_handle": "@BBMPCOMM",
            "ward_officer": {"name": "Ramesh Kumar", "email": "ward95@bbmp.gov.in", "phone": "+919900000095"},
        },
        "crowd_validation": crowd,
        "user_name": "Ojasvi Poonia",
        "user_email": "test@example.com",
    }


# --- Drafting Agent Tests ---

@pytest.mark.asyncio
async def test_drafting_generates_all_outputs() -> None:
    """All 6 outputs are generated."""
    agent = DraftingAgent()
    with patch("agents.drafting.generate_text", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = [
            "<p>Dear Officer Ramesh Kumar, formal email body</p>",
            "ಆತ್ಮೀಯ ಅಧಿಕಾರಿ ರಮೇಶ್ ಕುಮಾರ್",
            "@BBMPCOMM pothole in Ward 95 #FixBangalore",
            "Namaste Ramesh Kumar, WhatsApp message",
            "RTI Application under Karnataka RTI Act",
        ]
        result = await agent.execute(AgentInput(data=_base_drafting_input()))

    assert result.success
    assert result.data["email_subject"]
    assert result.data["email_body_en"]
    assert result.data["email_body_kn"]
    assert result.data["tweet_text"]
    assert result.data["whatsapp_text"]
    assert result.data["rti_template"]


@pytest.mark.asyncio
async def test_drafting_bundled_subject_differs() -> None:
    """Bundled complaint has 'Joint' in subject; non-bundled does not."""
    agent = DraftingAgent()
    with patch("agents.drafting.generate_text", new_callable=AsyncMock, return_value="mock content"):
        bundled = await agent.execute(AgentInput(data=_base_drafting_input(bundled=True)))
        standalone = await agent.execute(AgentInput(data=_base_drafting_input(bundled=False)))

    assert "Joint" in bundled.data["email_subject"]
    assert "11 Verified Residents" in bundled.data["email_subject"]
    assert "Joint" not in standalone.data["email_subject"]


@pytest.mark.asyncio
async def test_drafting_tweet_fits_280() -> None:
    """Tweet text is always <= 280 chars."""
    agent = DraftingAgent()
    with patch("agents.drafting.generate_text", new_callable=AsyncMock, return_value="A" * 500):
        result = await agent.execute(AgentInput(data=_base_drafting_input()))
    assert len(result.data["tweet_text"]) <= 280


@pytest.mark.asyncio
async def test_drafting_includes_citation() -> None:
    """Email prompt includes Karnataka Municipal Corp Act citation for potholes."""
    agent = DraftingAgent()
    with patch("agents.drafting.generate_text", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "Section 256 formal email"
        result = await agent.execute(AgentInput(data=_base_drafting_input()))
    # The prompt sent to Gemini should include the citation
    call_args = mock_gen.call_args_list[0][0][0]
    assert "Section 256" in call_args


# --- Submission Agent Tests ---

@pytest.mark.asyncio
async def test_submission_stub_mode() -> None:
    """All channels return stub mode when no credentials set."""
    agent = SubmissionAgent()
    inp = {
        "complaint_id": "cmp-001",
        "drafting": {
            "email_subject": "Test", "email_body_en": "Body",
            "email_body_kn": "", "tweet_text": "Tweet",
            "whatsapp_text": "WhatsApp",
        },
        "routing": {
            "twitter_handle": "@BBMPCOMM",
            "ward_officer": {"email": "test@bbmp.gov.in", "phone": "+919900000095"},
        },
        "crowd_validation": {"is_bundled": False, "member_count": 1, "cluster_id": None},
        "user_email": "citizen@gmail.com",
    }

    with patch("agents.submission.get_supabase") as mock_sb:
        mock_table = MagicMock()
        mock_table.insert.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.return_value.table.return_value = mock_table

        result = await agent.execute(AgentInput(data=inp))

    assert result.success
    assert result.data["status"] in ("sent", "partial_failure")
    channels = result.data["submitted_channels"]
    assert len(channels) == 3
    modes = {c["channel"]: c["mode"] for c in channels}
    assert modes["whatsapp"] == "stub"


@pytest.mark.asyncio
async def test_submission_suppression_non_milestone() -> None:
    """Complaint joining cluster at size 4 (not a milestone) is suppressed."""
    agent = SubmissionAgent()
    inp = {
        "complaint_id": "cmp-002",
        "drafting": {"tweet_text": "T", "email_subject": "S", "email_body_en": "B", "whatsapp_text": "W"},
        "routing": {"ward_officer": {}, "twitter_handle": "@BBMPCOMM"},
        "crowd_validation": {"is_bundled": True, "member_count": 4, "cluster_id": "cluster-xyz"},
        "user_email": None,
    }

    result = await agent.execute(AgentInput(data=inp))

    assert result.success
    assert result.data["status"] == "suppressed"
    assert "Not a milestone" in result.data["suppression_reason"]
    assert result.data["next_milestone"] == 5


@pytest.mark.asyncio
async def test_submission_sends_at_milestone() -> None:
    """Complaint pushing cluster to size 5 (milestone) sends."""
    agent = SubmissionAgent()
    inp = {
        "complaint_id": "cmp-003",
        "drafting": {"tweet_text": "T", "email_subject": "S", "email_body_en": "B", "email_body_kn": "", "whatsapp_text": "W"},
        "routing": {"ward_officer": {"email": "test@bbmp.gov.in", "phone": "+91"}, "twitter_handle": "@BBMPCOMM"},
        "crowd_validation": {"is_bundled": True, "member_count": 5, "cluster_id": "cluster-xyz"},
        "user_email": "citizen@gmail.com",
    }

    with patch("agents.submission.get_supabase") as mock_sb:
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{"last_notified_at_size": 3}]
        )
        mock_table.insert.return_value.execute.return_value = MagicMock(data=[])
        mock_table.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.return_value.table.return_value = mock_table

        result = await agent.execute(AgentInput(data=inp))

    assert result.success
    assert result.data["status"] in ("sent", "partial_failure")
    assert len(result.data["submitted_channels"]) == 3


@pytest.mark.asyncio
async def test_submission_standalone_always_sends() -> None:
    """Non-bundled (standalone) complaints always send."""
    agent = SubmissionAgent()
    inp = {
        "complaint_id": "cmp-004",
        "drafting": {"tweet_text": "T", "email_subject": "S", "email_body_en": "B", "email_body_kn": "", "whatsapp_text": "W"},
        "routing": {"ward_officer": {"email": "w@bbmp.gov.in"}, "twitter_handle": "@BBMPCOMM"},
        "crowd_validation": {"is_bundled": False, "member_count": 1, "cluster_id": None},
        "user_email": None,
    }

    with patch("agents.submission.get_supabase") as mock_sb:
        mock_table = MagicMock()
        mock_table.insert.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.return_value.table.return_value = mock_table

        result = await agent.execute(AgentInput(data=inp))

    assert result.success
    assert result.data["status"] in ("sent", "partial_failure")


@pytest.mark.asyncio
async def test_submission_partial_failure() -> None:
    """If Twitter fails but Gmail succeeds, status is partial_failure."""
    agent = SubmissionAgent()
    inp = {
        "complaint_id": "cmp-005",
        "drafting": {"tweet_text": "T", "email_subject": "S", "email_body_en": "B", "email_body_kn": "", "whatsapp_text": "W"},
        "routing": {"ward_officer": {"email": "w@bbmp.gov.in"}, "twitter_handle": "@BBMPCOMM"},
        "crowd_validation": {"is_bundled": False, "member_count": 1, "cluster_id": None},
        "user_email": None,
    }

    from integrations.contracts import DeliveryResult, DeliveryStatus
    failed_tweet = DeliveryResult(channel="twitter", status=DeliveryStatus.FAILED, attempts=1, elapsed_ms=100, error="rate_limited")

    with patch("agents.submission.twitter_client") as mock_tw:
        mock_tw.send = AsyncMock(return_value=failed_tweet)
        with patch("agents.submission.get_supabase") as mock_sb:
            mock_table = MagicMock()
            mock_table.insert.return_value.execute.return_value = MagicMock(data=[])
            mock_sb.return_value.table.return_value = mock_table

            result = await agent.execute(AgentInput(data=inp))

    assert result.success
    assert result.data["status"] == "partial_failure"
    tw_ch = next(c for c in result.data["submitted_channels"] if c["channel"] == "twitter")
    assert tw_ch["status"] == "failed"
