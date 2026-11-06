# NetSage AI - Human-in-the-Loop Review Standard Operating Procedure (SOP)

## Core Philosophy
NetSage AI enforces mandatory human oversight for all AI-generated network diagnoses and remediation commands.
AI is an assistive copilot, but the human network engineer retains ultimate authority and operational responsibility.

## Human Review Verdict Categories
1. **ACCEPTED (Green)**:
   - AI accurately identified the root cause.
   - Evidence cited directly supports the conclusion without hallucination.
   - Proposed Cisco IOS commands are syntax-valid, safe, and target the correct interface/device.
   - Verification commands are sound.

2. **EDITED (Yellow)**:
   - AI identified the general problem domain, but the specific fix command was inaccurate, incomplete, or targeted the wrong interface name.
   - Human adjusts commands (e.g. adding missing subnet mask, changing interface identifier, or adding safe fallback).
   - Log the edit reason for continuous AI refinement.

3. **REJECTED (Red)**:
   - AI hallucinated a non-existent fault or cited nonexistent show commands.
   - AI missed the true underlying root cause (e.g. diagnosing ACL when cause is missing return route).
   - AI suggested destructive or dangerous commands that would take down production links (e.g. `no switchport` on an unrouted L2 trunk).
   - Require full human override and document failure analysis in Responsible AI Log.

## Review Checklist
- [ ] Does the cited evidence exist verbatim in the show output?
- [ ] Is the OSI layer classification technically accurate?
- [ ] Are the proposed IOS commands non-destructive to adjacent VLANs/subnets?
- [ ] Is there a return route / symmetric path considered?
- [ ] Does the verification test confirm true end-to-end data plane reachability?