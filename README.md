# Late-Bound Fairness Interfaces for Finite-State Reconfiguration

This directory is a standalone, standard-library-only artifact for the paper. It
checks task-based weakly fair termination in declared finite transition systems,
constructs open and closed boundary summaries, emits positive or negative
certificates, and validates the implementation through structurally different
summary, whole-graph, raw-semantics, and transfer checks.

The artifact is not a Byzantine protocol implementation, deployment benchmark,
proof-assistant development, or source-code model extractor. Its guarantees apply
only to the supplied finite JSON semantics: fixed task identities, exact ports,
sealed interiors, additive port wiring, and weak fairness. A synthetic refinement
fixture and an exhaustive tiny-model family exercise the paper's sufficient
transfer rule; neither is a refinement of a real protocol.

## One-command reproduction

From this directory:

```bash
python3 reproduce.py --output reproduced
```

The output directory must not already exist unless `--resume` is explicitly
selected. A clean run executes 22 unit-test methods and 19 bounded campaign chunks
sequentially. It writes retained inputs, raw CSV/JSON rows, certificates,
per-command logs, and `summary.json`. Before accepting the run, the controller
checks the exact suite inventory, all deterministic totals, all command exit
codes, and the 22-test receipt. Expected deterministic totals are:

- 244,828 producer/checker verdict cases;
- 310,463 direct summary-oracle comparisons;
- 65,635 exhaustive two-module binding cases within that summary total;
- 244,824 complete whole-graph product-oracle comparisons and four declared
  budget exclusions;
- 2,500 parser-independent raw-semantics comparisons;
- 22,186 tiny concrete/abstract relation candidates, of which 1,358 satisfy the
  transfer checker and induce 2,116 checked liveness implications;
- one accepted 29-state-to-15-state refinement-condition instance, five rejected
  obligation mutations, and one rejected deadlock-totalization regression;
- 210,088 nonlive verdicts, a fixture count rather than a population estimate;
- zero summary, verdict, certificate, transfer, normalization, or oracle
  mismatches.

The retained clean run recorded 66.095382 seconds wall time, 75.520377 child CPU
seconds, 1.277129 controller CPU seconds, 103,084 KiB peak child RSS, and 92,960
KiB peak controller RSS. The two RSS values are separate process maxima, not a
simultaneous sum. Only one scientific child ran at a time.

## Focused commands

```bash
python3 tests/test_core.py
python3 src/cli.py synthesize inputs/role-reset.json role-reset.cert.json
python3 src/cli.py check inputs/role-reset.json role-reset.cert.json
python3 src/cli.py synthesize inputs/role-reset.json role-reset-finite.cert.json --finite-changes
python3 src/cli.py bind inputs/late-binding-family.json bound-interface.json
python3 src/campaign.py binding --out binding-check
python3 src/campaign.py refinement --out refinement-check
python3 src/campaign.py transfer --out transfer-check
python3 src/campaign.py raw --out raw-check
```

`VALID` means that the checker recomputed the normalized graph and boundary
summary and validated the supplied certificate. It does not establish that an
external protocol was abstracted faithfully.

## Directory guide

- `src/model.py`: strict schema, normalization, enabledness, and deadlock order.
- `src/producer.py`: graph-search summary and certificate synthesis.
- `src/checker.py`: snapshot-elimination summary and certificate validation.
- `src/interfaces.py`: open module export, ownership checks, associative raw
  interface join, and one-shot post-wiring closure.
- `src/summary_oracle.py`: direct first-return mask-product summary construction,
  independent of the search and elimination implementations.
- `src/oracle.py`: bounded whole-graph state-by-color-mask oracle and the
  strong-fairness negative control.
- `src/raw_oracle.py`: bounded raw weak-service/justice oracle that bypasses
  `model.parse` and justice-color normalization.
- `src/refinement.py`: finite checker for abstraction-transfer obligations,
  including semantic stutters at true non-goal deadlocks.
- `src/fixtures.py`: named fixtures, including the scheduler-expanded refinement.
- `src/campaign.py`: deterministic exhaustive/generated campaigns.
- `tests/test_core.py`: 22 contract, algebra, separation, reference, refinement,
  and corruption tests.
- `inputs/`: named scientific fixtures.
- `results/`: retained clean inputs, raw rows, certificates, command logs, and
  resource records.
- `proofs/core-argument.md`: proof obligations and declared boundaries.
- `docs/model-format.md`: input, output, interface-algebra, oracle, and refinement
  contracts.
- `docs/theorem-code-map.md`: theorem-to-code, test, result, and trust-boundary
  crosswalk.
- `docs/source-boundaries.md`: 12+5+5 literature calibration and closest-work delta.
- `reference_audit.csv`: one verified bibliographic record per cited BibTeX key.
- `claim_evidence_ledger.csv`: claim-to-proof/check mapping.
- `external_resources.csv`: scholarly and publisher source inventory.

## Trust boundary

The producer and checker implement different summary algorithms but share the
finite model semantics and parser. The direct summary oracle reconstructs
first-return masks without importing either summary implementation. The
whole-graph oracle avoids ports and summaries but shares normalization. The raw
oracle independently reads the bounded model dictionary and evaluates weak
fairness through enabled-set intersection and service-set union, so the 2,500-case
raw campaign also tests parsing/normalization-sensitive verdicts. All paths still
implement the same mathematical specification and are not independent human
proofs.

The refinement checker validates a supplied finite relation and the transfer
campaign exhausts a small family; neither derives an abstraction from source
code. Agreement is strong finite implementation evidence, not a machine-checked
general theorem, independent review, or evidence about an unprovided protocol.
