#!/usr/bin/env python3
"""Validate the FEAT-166 public governance customer handoff package."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_PACKAGE = Path(
    "packages/governance-customer-handoff/FEAT166-GOVERNANCE-CUSTOMER-HANDOFF-20260603-001"
)

FORBIDDEN_MARKERS = [
    "PrivateServer_ElectronicVoting",
    "hush-documents/",
    "C:\\",
    "/Users/",
    "/home/",
    "BEGIN PRIVATE KEY",
    "aws_access_key_id",
    "aws_secret_access_key",
    "credential=",
    "password=",
    "client_secret",
    "private_key",
    "customerChecklistAnswer",
    "customerLegalDocument",
    "rawRestrictedPayload",
    "externalAuditorNote",
    "authorityName",
    "signoffRecord",
    '"directRegisterMutation": true',
    '"canonicalRegisterMutationPerformed": true',
    '"payloadPublished": true',
    '"customerAnswersPublished": true',
    '"privateCheckoutRequired": true',
    '"credentialRequired": true',
]

REQUIRED_ARTIFACT_REFS = {
    "governance-customer-handoff-package.json",
    "readiness/governance-customer-handoff-readiness-fragment.json",
    "readiness/governance-customer-handoff-score-proposal.json",
    "handoff/governance-customer-handoff-downstream-handoff.json",
    "restricted/restricted-evidence-index.schema-note.md",
}

REQUIRED_VALIDATION_REFS = {
    "validation/readiness-baseline-currentness-summary.json",
    "validation/upstream-evidence-currentness-summary.json",
    "validation/responsibility-matrix-summary.json",
    "validation/non-claim-boundary-summary.json",
    "validation/external-prerequisite-routing-summary.json",
    "validation/customer-checklist-boundary-summary.json",
    "validation/public-only-validation-summary.json",
    "validation/no-secret-scan-result.json",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, default=DEFAULT_PACKAGE)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    package_root = (repo_root / args.package_root).resolve()
    errors: list[str] = []

    if not package_root.is_dir():
        return report([f"package root does not exist: {package_root}"])

    loaded = load_json_files(package_root, errors)
    validate_manifest(package_root, loaded, errors)
    validate_package_index(loaded, errors)
    validate_public_boundary(loaded, errors)
    validate_readiness_outputs(loaded, errors)
    scan_public_files(package_root, errors)

    if errors:
        return report(errors)

    print(f"Validated FEAT-166 public package: {package_root.relative_to(repo_root)}")
    print(f"JSON files parsed: {len(loaded)}")
    return 0


def load_json_files(package_root: Path, errors: list[str]) -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    for path in sorted(package_root.rglob("*.json")):
        rel = path.relative_to(package_root).as_posix()
        try:
            loaded[rel] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}: invalid JSON: {exc}")
    return loaded


def validate_manifest(package_root: Path, loaded: dict[str, Any], errors: list[str]) -> None:
    manifest = require_object(loaded, "governance-customer-handoff-manifest.json", errors)
    if not manifest:
        return

    if manifest.get("schemaVersion") != "governance-customer-handoff-package-manifest/v1":
        errors.append("manifest schemaVersion is not governance-customer-handoff-package-manifest/v1")
    if manifest.get("featureId") != "FEAT-166":
        errors.append("manifest featureId must be FEAT-166")

    ref_groups = [
        ("sourceRef", [manifest.get("sourceRef")]),
        ("artifactRefs", manifest.get("artifactRefs")),
        ("validationRefs", manifest.get("validationRefs")),
        ("handoffRefs", manifest.get("handoffRefs")),
        ("readinessProposal.proposalRef", [manifest.get("readinessProposal", {}).get("proposalRef")]),
    ]
    for group_name, refs in ref_groups:
        if not isinstance(refs, list) or not refs:
            errors.append(f"manifest {group_name} is missing or empty")
            continue
        validate_artifact_refs(package_root, group_name, refs, errors)

    artifact_paths = paths_from_refs(manifest.get("artifactRefs"))
    validation_paths = paths_from_refs(manifest.get("validationRefs"))
    missing_artifacts = sorted(REQUIRED_ARTIFACT_REFS - artifact_paths)
    missing_validations = sorted(REQUIRED_VALIDATION_REFS - validation_paths)
    if missing_artifacts:
        errors.append(f"manifest missing artifact refs: {', '.join(missing_artifacts)}")
    if missing_validations:
        errors.append(f"manifest missing validation refs: {', '.join(missing_validations)}")

    readiness = manifest.get("readinessProposal")
    if not isinstance(readiness, dict):
        errors.append("manifest readinessProposal is missing")
    else:
        if readiness.get("dimension") != "RDY-DIM-010":
            errors.append("manifest readinessProposal dimension must be RDY-DIM-010")
        if readiness.get("movement") != "8 -> 9":
            errors.append("manifest readinessProposal movement must be 8 -> 9")
        if readiness.get("directRegisterMutation") is not False:
            errors.append("manifest readinessProposal must not mutate the register")

    restricted_refs = manifest.get("restrictedEvidenceRefs")
    if not isinstance(restricted_refs, list) or not restricted_refs:
        errors.append("manifest restrictedEvidenceRefs is missing or empty")
    else:
        for index, ref in enumerate(restricted_refs):
            if not isinstance(ref, dict):
                errors.append(f"restrictedEvidenceRefs[{index}] is not an object")
                continue
            if ref.get("visibility") != "restricted-ref-only":
                errors.append(f"restrictedEvidenceRefs[{index}] must be restricted-ref-only")
            if ref.get("payloadPublished") is not False:
                errors.append(f"restrictedEvidenceRefs[{index}] must set payloadPublished=false")


def validate_artifact_refs(
    package_root: Path, group_name: str, refs: list[Any], errors: list[str]
) -> None:
    for index, entry in enumerate(refs):
        if not isinstance(entry, dict):
            errors.append(f"manifest {group_name}[{index}] is not an object")
            continue
        path_value = entry.get("path")
        expected_hash = entry.get("sha256")
        visibility = entry.get("visibility")
        if not isinstance(path_value, str) or not isinstance(expected_hash, str):
            errors.append(f"manifest {group_name}[{index}] is missing path or sha256")
            continue
        if visibility not in {"public", "restricted-ref-only"}:
            errors.append(f"manifest {group_name}[{index}] has invalid visibility")
        artifact_path = package_root / path_value
        if not artifact_path.is_file():
            errors.append(f"manifest {group_name}[{index}] artifact missing: {path_value}")
            continue
        observed_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        if observed_hash != expected_hash:
            errors.append(
                f"manifest hash mismatch for {path_value}: expected {expected_hash}, observed {observed_hash}"
            )


def validate_package_index(loaded: dict[str, Any], errors: list[str]) -> None:
    package = require_object(loaded, "governance-customer-handoff-package.json", errors)
    if not package:
        return
    if package.get("schemaVersion") != "governance-customer-handoff-package/v1":
        errors.append("package schemaVersion is not governance-customer-handoff-package/v1")
    if package.get("status") != "accepted":
        errors.append("package status must be accepted")
    if package.get("publicOnlyValidation") is not True:
        errors.append("package publicOnlyValidation must be true")

    score = package.get("scoreProposal")
    if not isinstance(score, dict) or score.get("movement") != "8 -> 9":
        errors.append("package scoreProposal movement must be 8 -> 9")
    elif score.get("directRegisterMutation") is not False or score.get("proposalOnly") is not True:
        errors.append("package scoreProposal must be proposal-only and non-mutating")

    for key, required_path in [
        ("readinessArtifacts", "readiness/governance-customer-handoff-score-proposal.json"),
        ("handoffArtifacts", "handoff/governance-customer-handoff-downstream-handoff.json"),
    ]:
        value = package.get(key)
        if not isinstance(value, list) or required_path not in value:
            errors.append(f"package {key} must include {required_path}")


def validate_public_boundary(loaded: dict[str, Any], errors: list[str]) -> None:
    no_secret = require_object(loaded, "validation/no-secret-scan-result.json", errors)
    if no_secret:
        if no_secret.get("status") != "accepted":
            errors.append("no-secret scan status must be accepted")
        for key in ["findingCount", "privatePathFindingCount", "payloadFindingCount"]:
            if no_secret.get(key) != 0:
                errors.append(f"no-secret scan {key} must be 0")

    public_only = require_object(loaded, "validation/public-only-validation-summary.json", errors)
    if public_only:
        for key in ["privateCheckoutRequired", "credentialRequired", "privatePayloadPublished"]:
            if public_only.get(key) is not False:
                errors.append(f"public-only summary must set {key}=false")
        if public_only.get("directRegisterMutation") is not False:
            errors.append("public-only summary must set directRegisterMutation=false")
        if public_only.get("customerAnswersPublished") is not False:
            errors.append("public-only summary must set customerAnswersPublished=false")


def validate_readiness_outputs(loaded: dict[str, Any], errors: list[str]) -> None:
    readiness = require_object(
        loaded, "readiness/governance-customer-handoff-readiness-fragment.json", errors
    )
    if readiness:
        validate_score_shape("readiness fragment", readiness, errors)
        if readiness.get("status") != "accepted_candidate":
            errors.append("readiness fragment status must be accepted_candidate")

    score = require_object(
        loaded, "readiness/governance-customer-handoff-score-proposal.json", errors
    )
    if score:
        validate_score_shape("score proposal", score, errors)
        if score.get("status") != "proposal_only":
            errors.append("score proposal status must be proposal_only")
        if score.get("canonicalRegisterMutationPerformed") is not False:
            errors.append("score proposal must set canonicalRegisterMutationPerformed=false")

    handoff = require_object(
        loaded, "handoff/governance-customer-handoff-downstream-handoff.json", errors
    )
    if handoff:
        if handoff.get("status") != "handoff_ready":
            errors.append("downstream handoff status must be handoff_ready")
        targets = handoff.get("downstreamTargets")
        if not isinstance(targets, list) or len(targets) != 4:
            errors.append("downstream handoff must define exactly four downstream targets")
        elif any(
            not isinstance(target, dict)
            or target.get("directRegisterMutationAllowed") is not False
            or target.get("payloadPublished") is not False
            for target in targets
        ):
            errors.append("downstream targets must be non-mutating and no-payload")
        validate_non_claims("downstream handoff", handoff, errors)


def validate_score_shape(label: str, obj: dict[str, Any], errors: list[str]) -> None:
    if obj.get("dimension") != "RDY-DIM-010":
        errors.append(f"{label} dimension must be RDY-DIM-010")
    if obj.get("movement") != "8 -> 9":
        errors.append(f"{label} movement must be 8 -> 9")
    if obj.get("currentScore") != 8 or obj.get("proposedScore") != 9:
        errors.append(f"{label} score range must be 8 -> 9")
    if obj.get("proposalOnly") is not True:
        errors.append(f"{label} must be proposal-only")
    if obj.get("directRegisterMutation") is not False:
        errors.append(f"{label} must set directRegisterMutation=false")
    validate_non_claims(label, obj, errors)


def validate_non_claims(label: str, obj: dict[str, Any], errors: list[str]) -> None:
    non_claims = obj.get("nonClaims")
    if not isinstance(non_claims, dict):
        errors.append(f"{label} nonClaims is missing")
        return
    for key in [
        "legalSufficiencyClaimed",
        "agmManagementClaimed",
        "certificationClaimed",
        "externalAuditAcceptanceClaimed",
        "publicStateReadinessClaimed",
        "productionRolloutApprovalClaimed",
        "customerGovernanceDecisionClaimed",
        "directReadinessRegisterMutationClaimed",
    ]:
        if non_claims.get(key) is not False:
            errors.append(f"{label} nonClaims must set {key}=false")


def scan_public_files(package_root: Path, errors: list[str]) -> None:
    for path in sorted(package_root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(package_root).parts
        if "schemas" in rel_parts or rel_parts[:2] == ("examples", "negative"):
            continue
        rel = path.relative_to(package_root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        lower = text.lower()
        for marker in FORBIDDEN_MARKERS:
            if marker.lower() in lower:
                errors.append(f"{rel}: forbidden public marker found: {marker}")


def require_object(loaded: dict[str, Any], path: str, errors: list[str]) -> dict[str, Any]:
    value = loaded.get(path)
    if not isinstance(value, dict):
        errors.append(f"{path} is missing or not a JSON object")
        return {}
    return value


def paths_from_refs(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {
        entry.get("path")
        for entry in value
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    }


def report(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
