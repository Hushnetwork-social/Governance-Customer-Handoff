# Governance Customer Handoff

Public-safe source contracts and checker inputs for FEAT-166, the governance/customer handoff
audit pack that proposes `RDY-DIM-010 8 -> 9`.

This repository is intentionally narrow. It publishes schemas, generic responsibility-domain
contracts, non-claim boundaries, external-prerequisite routing contracts, sanitized examples,
package manifests, hash references, and reviewer-readable summaries for governance/customer
handoff validation. It does not publish customer legal documents, customer checklist answers,
authority names, signoff records, external auditor notes, voter material, trustee material,
restricted reviewer payloads, credentials, private paths, or customer-specific governance details.

## Repository Role

- Feature: `FEAT-166`
- Parent readiness blocker: `RDY-BLOCK-INTERNAL_AUDIT_95_DIM010-001`
- Target dimension: `RDY-DIM-010`
- Score movement: proposal-only `8 -> 9`
- Default branch: `main`

FEAT-140, FEAT-149, FEAT-156, and FEAT-157 through FEAT-165 already provide upstream evidence and
boundary inputs. FEAT-166 must not replay their accepted score movements or claim final readiness
promotion. This repository supports the next proposal-only movement by defining a deterministic,
public-safe handoff package that separates Hush technical proof, customer governance
responsibility, external legal/public prerequisites, auditor review, and promotion-owner action.

## Layout

```text
schemas/
  governance-customer-handoff-source.schema.json
  governance-customer-handoff-package-manifest.schema.json
catalogs/
  responsibility-domain-catalog.json
  non-claim-catalog.json
  external-prerequisite-routing-catalog.json
  result-code-catalog.json
examples/
  release-baseline/
    governance-customer-handoff-source.json
  negative/
    governance-customer-handoff-negative-fixtures.json
packages/
  governance-customer-handoff/<handoff-run-id>/
```

Generated packages are expected under
`packages/governance-customer-handoff/<handoff-run-id>/` after the promoter/checker is
implemented. Until then, the schema files define the public contract surface.

## Public Boundary

Allowed public material:

- Stable ids, branch names, commit hashes, manifest hashes, artifact hashes, and generated-at
  times.
- Generic responsibility-domain catalogs, non-claim catalogs, external-prerequisite routing
  catalogs, checklist section ids, sanitized examples, and expected result codes.
- Public-safe summaries, package manifests, no-payload restricted evidence refs, and non-claim
  wording.
- Negative fixtures that use redacted placeholders rather than real restricted material.

Restricted material that must not be committed here:

- Secrets, credentials, tokens, private keys, or signing material.
- Customer legal documents, legal analysis, governing documents, notice records, meeting minutes,
  quorum/proxy records, authority names, signoff records, checklist answers, or customer-specific
  governance decisions.
- External auditor notes, public authority correspondence, certification records, or unrestricted
  reviewer packs.
- Voter material, trustee threshold material, ballot choices, receipt capabilities, vote secrets,
  witnesses, private randomness, or accepted-to-published mappings.
- Private HushDocuments paths, restricted reviewer indexes, provider details, local workstation
  paths, support exports, private findings, or restricted payloads.

When restricted evidence is needed, public artifacts may reference only an opaque restricted
evidence id, expected hash, visibility marker, and no-payload note. The restricted payload itself
must remain in the approved private reviewer location.

## Validation Contract

The checker must fail closed when:

- `RDY-REG-v0.1.7` or `RDY-DIM-010 8 -> 9` currentness is missing, stale, or mismatched.
- FEAT-140, FEAT-149, FEAT-156, or FEAT-157 through FEAT-165 refs are missing, stale, mismatched,
  superseded, blocked, or unknown.
- The responsibility matrix does not separate Hush technical work, customer governance
  responsibility, external authority prerequisites, external auditor review, and promotion-owner
  action.
- Non-claim boundaries are missing or the package claims legal sufficiency, full AGM management,
  certification, external audit acceptance, public/state readiness, production rollout approval,
  customer governance decisions, or final readiness-register mutation.
- Public outputs contain restricted customer, legal, governance, voter, trustee, auditor,
  private-path, credential, or reviewer material.
- Public-only validation depends on private repositories, private paths, credentials, or live
  private services.
- The package claims direct readiness-register mutation or proposes any score movement other than
  proposal-only `RDY-DIM-010 8 -> 9`.

## Non-Claims

This repository does not certify legal sufficiency, customer governance correctness, AGM
management, certification, public/state election readiness, external audit acceptance, production
rollout approval, or final readiness-register mutation. It only provides public-safe inputs and
outputs for deterministic validation of the FEAT-166 evidence package.
