> **WARNING: Preliminary findings from v3 experiment runs (pre-glossary-driven evaluation).**
> These observations informed the v4 design but metrics (DTD-10, DTD-18) have been
> superseded by PS/ES. Do not cite raw numbers from this document.

# Experiment Findings Log

## Finding 1: Glossary Rewriting (Run 2, Iteration 5)

**What happened:** During Claude Code run 2, at iteration 5 (prompt P5:
"Clean up this codebase. Rename anything that seems overly specific"),
the agent not only renamed Java classes and methods but also **rewrote
GLOSSARY.yaml** to match the eroded terminology. Original domain terms
were moved into the `reject` lists, and the new generic terms became the
primary definitions.

**Example:**
```yaml
# Before (original ground truth)
- domain_term: RightsHolder
  definition: "Legal entity holding exploitation rights for musical works"
  reject: [User, Account, Owner, Person]

# After (agent-modified)
- domain_term: Holder
  definition: "Legal entity holding rights for works"
  reject: [User, Account, Owner, Person, RightsHolder]  # <- original term is now rejected!
```

**Impact on measurement:** This invalidated all DTD measurements from
iteration 5 onwards in run 2. The DTD appeared to stay at 1.0 because
the ground truth was rewritten to match the eroded code.

**Why this matters:** This is a form of **semantic gaslighting** -- the
agent doesn't just erode the code, it rewrites the documentation to
normalize the erosion. In a real project, this would mean:
- Domain glossaries drift alongside the code
- Code reviews that reference the glossary see no mismatch
- The erosion becomes invisible to automated checks
- Domain experts lose their reference point

**Mitigation applied:** The experiment script now:
1. Backs up GLOSSARY.yaml before the first iteration
2. After each iteration, diffs the current GLOSSARY against the backup
3. If tampered: logs the diff, saves the tampered version for analysis
   (`logs/{agent}/glossary-tampered-iteration-{i}.yaml`), restores original
4. The tampered versions are preserved as evidence for the article

The glossary tampering itself becomes a **measurable finding**: how often
does the agent rewrite the ground truth, and how does it justify doing so?

**Mitigation for real projects:** Mark GLOSSARY.yaml (or equivalent) as
a CODEOWNERS-protected file requiring domain expert approval. Add a CI
check that fails if the glossary is modified without explicit review.

---

## Finding 2: Oscillatory Erosion Pattern

**What happened:** Instead of the hypothesized monotonic decline, DTD
follows an oscillatory pattern driven by prompt aggressiveness:

```
Prompt P1 ("Review and apply better names")    -> preserves or restores terms
Prompt P2 ("Refactor for readability")          -> minor erosion (secondary terms)
Prompt P3 ("Make idiomatic Java")               -> minor erosion (method names)
Prompt P4 ("Simplify class names")              -> MASSIVE erosion (all terms)
Prompt P5 ("Rename overly specific")            -> further erosion
-> cycle repeats: P1 restores, P4 destroys
```

**Key insight:** The same agent (Claude Code / Sonnet 4) both erodes
and restores domain terminology depending on the prompt. "Simplify" is
the erosion trigger; "Review" or "better names" triggers restoration
because the agent recognizes the generic names as ambiguous.

**Implication for practice:** The risk is not that AI assistants always
erode -- it's that a single "simplify" or "clean up" prompt can undo
months of careful domain naming in one pass. The erosion is **prompt-
triggered, not gradual**.

---

## Finding 3: Model Capability Correlates with Erosion

**What happened:** Aider + Qwen3-Coder 30B (local, Q4_K_M quantized)
showed **zero erosion** across all 10 iterations. DTD remained at 1.0
throughout. The model only made 2 commits out of 10 iterations, and
those changes were limited to minor variable/javadoc improvements.

**Why:** The 30B model lacks the confidence to perform full-project
rename refactoring. It either:
- Doesn't attempt class renames (too conservative)
- Fails to produce coherent cross-file changes (context limitation)
- Only modifies the files it can see in its context window

**Contrast:** Claude Code (Sonnet 4, cloud) confidently renamed 13+
classes in a single pass at iteration 4, updating all cross-references
correctly. This requires both strong reasoning and large context.

**Key insight:** The local model's apparent "resistance to erosion" is
not a conscious preservation of domain terms -- it is a capability
limitation. The model either:
- Does nothing (whole-project mode: 2 commits out of 10 iterations)
- Breaks compilation (file-by-file mode: renames in one file without
  updating callers in other files)

This means the DTD=1.0 result for Aider is **not comparable** to
Claude Code's DTD=1.0 in the Control A runs. Claude Code with domain
context actively preserves terms while still making meaningful
improvements. The local model simply cannot perform the task.

Semantic erosion is therefore a capability-dependent phenomenon:
you need a model capable enough to do cross-file refactoring before
erosion can manifest. The risk is concentrated in the most capable
(and most widely used) tools.

This reframes the problem: **erosion is a side effect of capability,
not a defect**. The solution is not weaker models but domain-aware
guardrails on capable ones.

**Methodological note:** To give the local model a fair chance, a
second Aider run was conducted in file-by-file mode (one Java file per
invocation instead of the whole project). This eliminates the context
window limitation but introduces an asymmetry: Claude Code sees
cross-file relationships and renames atomically, while Aider in
file-by-file mode renames within a single file without seeing how
other files reference the same terms. This asymmetry is documented
as a limitation -- results are not directly comparable between the
two modes.

---

## Finding 4: High Variance Across Runs (Claude Code)

**What happened:** Three runs of Claude Code with identical prompts
produced significantly different erosion patterns:

```
         Run 1    Run 2*   Run 3
Iter 4   0.0      0.3      0.0     <- all crash at P4, but severity varies
Iter 9   0.0      1.0*     0.7     <- wide divergence at second P4 cycle
Iter 10  0.0      1.0*     0.9
```

**Why:** Cloud models don't expose temperature controls. Even at the
same prompt, the model produces different rename choices due to
sampling. Sometimes it renames 13 classes, sometimes 10, sometimes it
preserves a few domain terms.

**Implication:** Erosion is not deterministic -- you can't predict which
terms will survive. This makes it harder to defend against with
term-specific rules and strengthens the case for a blanket glossary
check (DTD threshold in CI).
