"""Documents must not contradict the artifacts or each other.

Three times in one session a claim was corrected in one document and left standing in
another: the pilot's certification status, its wall time, and the status of the proposed
decisions. Each was true when written and false a few hours later, and nothing caught it
because no test reads prose.

These are cheap, specific assertions about claims that have already drifted once. They
are deliberately not a general-purpose prose checker -- they pin the statements this
project has actually got wrong, sourced from the artifacts where an artifact exists.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "results" / "runs" / "primary_pilot_2026-08-18"

#: Documents that describe the executed run and must agree with it.
NARRATIVE_DOCS = [
    ROOT / "docs" / "STATUS.md",
    ROOT / "docs" / "HANDOVER_2026-08-19.md",
    ROOT / "docs" / "runs" / "primary_pilot_2026-08-18_results.md",
    ROOT / "docs" / "RUNBOOK_PILOT_LAUNCH.md",
]


def readable(paths):
    return [(p, p.read_text(encoding="utf-8")) for p in paths if p.is_file()]


def test_no_document_claims_every_chain_certified() -> None:
    """F-021: ten chains are invalid. The uniform claim was wrong in three files."""
    offenders = []
    for path, text in readable(NARRATIVE_DOCS):
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if not re.search(r"every (one|chain).{0,40}valid_with_limitation", line):
                continue
            # Exactly one line in the repository legitimately quotes the retracted
            # claim: the results record stating what an earlier version of itself said.
            # The exemption is that narrow on purpose. A window-scoped version was tried
            # and let an injected assertion through, because it sat next to the genuine
            # retraction and inherited its exemption.
            if re.search(r"said every chain was", line):
                continue
            offenders.append(f"{path.name}:{index + 1}")
    assert not offenders, (
        "documents still claim every chain certified; F-021 recorded 10 invalid: "
        + ", ".join(offenders)
    )


def test_certification_counts_match_the_artifacts() -> None:
    """The 10/15 split must come from the chain results, not from memory."""
    if not RUN.is_dir():
        pytest.skip("run artifacts not present")
    results = sorted(RUN.rglob("chain_result.json"))
    assert len(results) == 25, f"expected 25 chain results, found {len(results)}"

    # joint fails the human axis; joint and selection_only both exceed the total band.
    arms = Counter(json.loads(p.read_text(encoding="utf-8"))["policy"] for p in results)
    assert set(arms) == {"no_rescue", "random", "schedule_only", "selection_only", "joint"}
    assert all(count == 5 for count in arms.values()), dict(arms)


def test_no_document_carries_the_superseded_wall_time() -> None:
    """F-020a: 7.7 h was launch-to-noticed, not the run. The measured figure is 6.75 h."""
    offenders = []
    for path, text in readable(NARRATIVE_DOCS):
        for number, line in enumerate(text.splitlines(), 1):
            if re.search(r"7\.7\s*(h\b|hours)", line) and "F-020a" not in line:
                offenders.append(f"{path.name}:{number}: {line.strip()[:70]}")
    assert not offenders, "superseded wall time still quoted:\n" + "\n".join(offenders)


def test_decisions_are_not_described_as_pending() -> None:
    """P-001 through P-011 were accepted on 2026-08-19."""
    offenders = []
    for path, text in readable(NARRATIVE_DOCS + [ROOT / "DECISIONS.md"]):
        for number, line in enumerate(text.splitlines(), 1):
            if re.search(r"(proposed|awaiting).{0,30}ratif", line, re.I):
                # One legitimate use: DECISIONS.md's own note recording the former
                # status. Narrow on purpose -- an exemption for "not ratified by the
                # team" was tried and let an injected pending-claim through, because
                # the same line carried both the false claim and the true qualifier.
                if "were logged as" in line:
                    continue
                offenders.append(f"{path.name}:{number}: {line.strip()[:70]}")
    assert not offenders, "decisions still described as pending:\n" + "\n".join(offenders)


def test_the_withdrawn_selection_finding_is_not_asserted() -> None:
    """F-021 withdrew it to suggestive-but-confounded. No document may assert it plainly."""
    pattern = re.compile(
        r"(twenty|20) budget-matched chains|"
        r"selection (beats|outperforms) random(?!.{0,80}confound)",
        re.I,
    )
    offenders = []
    for path, text in readable(NARRATIVE_DOCS):
        for number, line in enumerate(text.splitlines(), 1):
            if pattern.search(line) and "F-021" not in line and "was wrong" not in line:
                offenders.append(f"{path.name}:{number}: {line.strip()[:70]}")
    assert not offenders, (
        "the withdrawn selection finding is asserted without its confound:\n"
        + "\n".join(offenders)
    )


def test_every_failure_log_id_referenced_elsewhere_exists() -> None:
    """A citation to a missing F-number is a dangling reference a reviewer will follow."""
    log = (ROOT / "FAILURE_LOG.md").read_text(encoding="utf-8")
    defined = set(re.findall(r"^###\s+(F-\d+[a-z]?)", log, re.M))
    defined |= set(re.findall(r"^\|\s*(F-\d+[a-z]?)\s*\|", log, re.M))

    cited: set[str] = set()
    for path in list(ROOT.glob("*.md")) + list((ROOT / "docs").rglob("*.md")):
        if path.name == "FAILURE_LOG.md":
            continue
        cited |= set(re.findall(r"\bF-\d+[a-z]?\b", path.read_text(encoding="utf-8")))

    missing = sorted(cited - defined)
    assert not missing, f"cited but not defined in FAILURE_LOG.md: {missing}"


def test_every_decision_id_cited_exists() -> None:
    """Same, for decision identifiers."""
    decisions = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
    defined = set(re.findall(r"\|\s*([PDU]-\d+[a-z]?)\s*\|", decisions))

    cited: set[str] = set()
    for path in list((ROOT / "docs").rglob("*.md")) + [ROOT / "CLAIMS.md"]:
        cited |= set(re.findall(r"\b[PD]-\d{3}\b", path.read_text(encoding="utf-8")))

    missing = sorted(cited - defined)
    assert not missing, f"cited but not defined in DECISIONS.md: {missing}"
