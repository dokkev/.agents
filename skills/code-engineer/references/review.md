# Code Review

Load this reference only when the user explicitly asks for a code review,
inspection, issue search, or assessment. Review is read-only unless fixes are
also requested.

## Core Contract

Review the code against the repository's existing contracts instead of creating
a separate review rulebook.

1. Establish the exact diff, files, subsystem, or behavior under review.
2. Read the closest repository instructions and only the references relevant to
   that code. Use `general-code-guidline.md` when structural simplicity or
   over-engineering is part of the review.
3. Check whether the implementation follows those references in actual runtime
   behavior, ownership, safety, numerical behavior, and code structure.
4. Report only concrete violations, defects, or meaningful risks supported by
   the code. Do not invent findings to satisfy a checklist.

Follow the closest repository or task policy for review independence. Never call
an author's self-review independent review.

Do not turn implementation review into architecture redesign, testing, or broad
validation unless the user requested those modes too.

## Findings

For each actionable finding, give:

- file and precise location;
- the violated repository contract or reference;
- the concrete consequence or realistic failure path;
- the smallest useful correction direction.

Prioritize correctness, hardware safety, numerical validity, ownership, and
functionally meaningful maintainability issues. Do not report formatting,
ceremony, speculative scalability, or generic commercial-code preferences as
findings unless an applicable repository contract requires them.

If no actionable finding is supported, say so directly.
