# Issue Log

## Project

AI Systems & Intelligent Automation

## Logging Rule

This file tracks actual technical issues, cleanup decisions, unresolved architecture questions, and validation findings related to the 2026 migration + refactor stream.

---

## ISSUE-2026-04-03-001

**Title:** Legacy company-specific naming and metadata present in active extension structure  
**Status:** Resolved in current baseline  
**Type:** Architecture / metadata cleanup

### Description

The inherited working structure still contained external company-facing naming, references, and extension metadata not suitable for the current BIM3DNA / WBSO-aligned repository baseline.

### Impact

- misleading project identity
- poor separation between legacy origin and current active work
- risk of confusion in pyRevit-visible UI labels and metadata
- weak traceability for WBSO evidence

### Action Taken

- cleaned extension metadata
- removed outside company-facing references from active baseline
- renamed active metadata toward AI Systems & Intelligent Automation scope
- aligned repository identity with BIM3DNA / WBSO direction

### Follow-up

Confirm pyRevit loads and displays the cleaned baseline correctly.

---

## ISSUE-2026-04-03-002

**Title:** Legacy toolbar/button structure contained obsolete or off-scope content  
**Status:** Partially resolved  
**Type:** Structural cleanup / scope reduction

### Description

The inherited structure contained multiple development buttons, experimental toolbar items, and company-specific panel content that no longer fit the intended 2026 project scope.

### Impact

- architecture clutter
- unclear active entry points
- difficult evidence tracking
- increased risk of maintaining dead code paths

### Action Taken

- reviewed keep / delete / rename / archive decisions
- reduced active structure to a cleaner baseline
- retained only components considered relevant enough for further review

### Remaining Work

- validate whether any retained helper/support code still depends on removed bundles
- continue reviewing retained scripts for final architecture fit

---

## ISSUE-2026-04-03-003

**Title:** Legacy provenance could be lost during migration  
**Status:** Mitigated  
**Type:** Traceability / evidence integrity

### Description

The project builds on prior legacy AI-agent and pyRevit work. Without explicit migration notes, retained components could appear as unexplained new work, while deleted components could lose provenance.

### Impact

- weak evidence trail
- difficult WBSO explanation of what was genuinely done in 2026
- risk of mixing legacy source lineage with current implementation work

### Action Taken

- introduced `legacy_migration_map.md`
- defined the repository as the 2026 migration + refactor + active development stream
- established the rule that legacy work is source lineage only, while current renaming/refactor/validation work is the active 2026 stream

### Remaining Work

Keep updating migration mapping whenever a retained component is:

- newly classified
- renamed materially
- deleted from the active baseline
- moved into current architecture

---

## ISSUE-2026-04-03-004

**Title:** No repo-local WBSO evidence structure existed for this project baseline  
**Status:** Resolved in current baseline  
**Type:** Documentation / process

### Description

Before the current setup, the repository did not yet contain a dedicated repo-local WBSO layer comparable to the one created for the Image Scanner project.

### Impact

- weak session-by-session evidence capture
- harder Codex-assisted documentation upkeep
- separation between code and evidence not yet established

### Action Taken

Created:

- `WBSO/Technical_Notes/`
- `WBSO/Testing_Validation/`
- `WBSO/Data_Models/`

Added baseline files for:

- architecture notes
- issue logging
- evidence reference
- migration mapping
- pyRevit refactor notes
- test planning
- validation summary
- experiment logging
- provider/model tracking

---

## ISSUE-2026-04-03-005

**Title:** pyRevit loading behavior not yet revalidated after baseline cleanup  
**Status:** Resolved  
**Type:** Validation / runtime

### Resolution

A runtime validation was executed after correcting the custom extension directory and rearranging the repository structure.

### What Was Confirmed

- pyRevit discovered the cleaned extension
- the AI tab became visible in Revit
- the active button/script became visible in the tab
- the current baseline is runtime-valid at discovery/UI level

### Residual Note

This issue is resolved for extension discovery and UI loading. Feature-level AI behavior still requires separate testing.

---

## ISSUE-2026-04-03-006

**Title:** Retained service/provider folders still need architectural classification  
**Status:** Open  
**Type:** Architecture / module boundary

### Description

Folders such as `Model_Service/` and `Openai_Server/` remain in the cleaned repository, but their final role in the modular architecture is not yet fully defined.

### Impact

- unclear separation of responsibilities
- potential duplication between service, provider, and orchestration logic
- future refactor complexity if left ambiguous

### Next Action

During the next pass:

- classify each retained module
- identify whether it should be kept, merged, renamed, or split
- update `architecture_notes.md` and `provider_strategy.md`

---

## ISSUE-2026-04-03-007

**Title:** Root utility scripts may not yet belong to a stable architecture boundary  
**Status:** Open  
**Type:** Code organization

### Description

Some scripts still exist at repository root or in partially transitional locations.

### Impact

- reduced clarity of active architecture
- difficult validation scope
- weaker long-term maintainability

### Next Action

Review root-level scripts one-by-one and classify them as:

- keep
- move
- refactor
- delete

---

## Current Open Issues Summary

- pyRevit loading behavior still needs validation
- retained service/provider candidates need classification
- root utility scripts need final architectural review
- next pass should confirm minimal operational baseline

## ISSUE-2026-04-03-008

**Title:** pyRevit custom extension directory required corrected path after repo rearrangement  
**Status:** Resolved  
**Type:** Runtime configuration / pathing

### Description

After cleanup/refactor, the extension did not load until the correct working directory was added to pyRevit custom extension directories.

### Impact

- extension initially not visible
- runtime validation blocked until correct path and structure alignment were established

### Action Taken

- rearranged folders/files into a pyRevit-loadable structure
- configured the correct custom extension directory in pyRevit
- refreshed pyRevit

### Result

The extension loaded successfully and the AI tab became visible.

---

## ISSUE-2026-04-03-010

**Title:** Initial UI launch behavior of AI button required validation  
**Status:** Resolved  
**Type:** Runtime / UI validation

### Description

Even after the tab and button became visible, it still needed to be confirmed whether clicking the active AI button actually launched the intended interface without immediate runtime failure.

### Action Taken

- clicked the active AI button in Revit
- observed script startup behavior directly inside pyRevit/Revit

### Result

- the chat/UI window opened successfully
- no immediate runtime errors were observed during launch

### Remaining Scope

This resolves initial UI launch validation only. It does not yet confirm correctness of:

- provider calls
- chat processing
- generated commands
- downstream Revit action execution

---

## ISSUE-2026-04-03-009

**Title:** Current nested / working repo structure is operational but may remain suboptimal for long-term clarity  
**Status:** Open  
**Type:** Repository structure / maintainability

### Description

The current repository layout now works with pyRevit and should not be changed immediately. However, it may later benefit from further normalization for clarity and maintainability.

### Current Position

Keep as-is for now because the structure is validated and functional.

### Next Action

Review only in a later dedicated refactor pass, not during the current validated baseline milestone.
