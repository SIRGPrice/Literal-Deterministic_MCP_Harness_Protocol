# Advanced Examples

The `examples/advanced/` directory contains high-complexity fixtures designed to show the upper end of what the Literal protocol can govern.

These are not toy demos. They model domains where an autonomous tool call can affect people, money, physical systems, or legal evidence.

## What to look for

Across the examples, watch for these protocol features working together:

- **Dense catalogs** with many actions, aliases, states, parameters, groups, and scenarios.
- **Strict parameter spaces** using `values`, `range`, and `required` where appropriate.
- **Scenario runbooks** that encode the safe sequence rather than asking the model to improvise.
- **Policy boundaries** that deny entire categories of action.
- **Confirmation gates** for irreversible, costly, physical, or regulated operations.
- **Traces** that make every decision reviewable after the fact.

## Run all advanced examples

```bash
python examples/advanced/run.py
```

The runner loads every catalog and policy, then smoke-tests a read-only call, a denied call, and a confirmation-gated call for each domain.

## Example 1: Hospital Command Center

Path: [`examples/advanced/hospital-command-center/`](../examples/advanced/hospital-command-center/README.md)

This catalog coordinates:

- Emergency Department intake;
- ICU capacity;
- isolation ward posture;
- radiology CT backlog;
- ambulance bay routing;
- hospital incident command.

It also includes an explicit `Clinical Authority Boundary` capability whose only purpose is to make forbidden clinical actions visible and auditable.

### Protocol behavior demonstrated

- `fuzzy_cutoff: 0.78` keeps routing strict.
- `mass_casualty_intake` runs a multi-step command scenario.
- `infectious_surge_containment` coordinates ED, isolation, EMS, and command.
- `create_prescription`, `discharge_patient`, and `override_clinician` are denied.
- Incident channels and unit lockdowns require confirmation.

### Why it matters

A generic agent can be told to coordinate a hospital. Literal shows which parts of that coordination are safe automation and which are human authority boundaries.

## Example 2: Fintech Risk Operations

Path: [`examples/advanced/fintech-risk-ops/`](../examples/advanced/fintech-risk-ops/README.md)

This catalog coordinates:

- EU card ledger;
- US ACH rail;
- chargeback desk;
- AML review queue;
- treasury vault;
- tenant control plane.

### Protocol behavior demonstrated

- Tenant IDs are constrained to known tenants.
- Refund amounts are bounded by numeric ranges.
- Treasury wires and large refunds require confirmation.
- Ledger deletion is denied outright.
- Fraud and chargeback scenarios create evidence packs without moving funds autonomously.

### Why it matters

Financial copilots should help analysts move faster without granting the model unrestricted money movement. Literal turns that into a concrete executable contract.

## Example 3: Critical Infrastructure Grid

Path: [`examples/advanced/critical-infrastructure-grid/`](../examples/advanced/critical-infrastructure-grid/README.md)

This catalog coordinates:

- battery fleet dispatch;
- hospital feeder protection;
- EV charging demand response;
- solar inverter modes;
- physical breaker control;
- downtown microgrid islanding.

### Protocol behavior demonstrated

- `fuzzy_cutoff: 0.82` for a physical-control domain.
- Breaker open/close operations require confirmation.
- Protection bypass is denied.
- Hospital feeder shedding is denied.
- Microgrid islanding is scenario-driven and traceable.

### Why it matters

This is the edge case for agent safety: physical action. Literal keeps the model in the planning/orchestration lane and forces the high-risk action through explicit policy.

## Reading the examples

A useful review pattern:

1. Open the catalog and identify the blast radius: every action the agent could possibly request.
2. Open the policy and identify the red lines: deny and confirmations.
3. Open the scenarios and ask whether the sequence matches your runbook.
4. Run the example and inspect the traces.
5. Change one policy rule and rerun the same input to see deterministic replay.

## Design takeaway

The protocol scales because complexity lives in data:

- catalog for vocabulary and structure;
- policy for governance;
- scenarios for deterministic operating procedures;
- traces for evidence.

The runtime remains the same whether the domain is a smart office or a hospital command center.
