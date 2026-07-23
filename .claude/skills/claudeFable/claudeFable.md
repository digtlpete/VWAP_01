\# claudeFable.md

Rules for running Claude Fable 5 in this project. Read this file before starting any session. Every rule below is compiled from Anthropic's Fable 5 prompting documentation and measured production workloads.

\---

\#\# Cost context

\- Input tokens: $10 per million  
\- Output tokens: $50 per million  
\- Output is 5x more expensive than input  
\- Cost of a session is decided by how much you write, not how much you read

\---

\#\# 1\. Scope discipline

Do not add features, refactor, or introduce abstractions beyond what the task requires.

\- Stay inside the file, function, or module named in the request  
\- Do not tidy adjacent code, do not rename things, do not reformat  
\- Do not add error handling that was not asked for  
\- Do not create git branches, backups, or defensive commits without being asked  
\- Do not draft follow-up work (emails, PR descriptions, docs) unless requested

If the task boundary is unclear, ask one question and stop. Do not fill the gap with plausible-looking work.

\---

\#\# 2\. Effort sizing

Use the lowest effort level that holds quality on this task.

\- Default to \`high\` for most work  
\- Use \`xhigh\` only for genuinely capability-sensitive tasks (novel algorithm design, cross-repo refactors, hard debugging)  
\- Drop to \`medium\` or \`low\` for routine work: single-file edits, simple bug fixes, documentation, mechanical transforms  
\- If a task completes but takes longer than necessary, the effort was too high — reduce it next time

Low-effort Fable 5 already exceeds prior-model xhigh performance. Do not pay for reasoning depth this task does not need.

\---

\#\# 3\. Cache the stable prefix

Keep the top of every prompt byte-stable so prompt caching applies.

\- System prompt, tool definitions, and reference docs go at the top and never change mid-session  
\- Minimum cacheable block is 512 tokens  
\- Any edit above the cache point invalidates every token below it  
\- Freeze the top of the context; edit only below the seal

Cached input tokens bill at $1 per million instead of $10 — a 90% discount on every repeated read.

\---

\#\# 4\. Cap the output

Every response has a hard token budget.

\- Set \`max\_tokens\` explicitly on every call  
\- Ask for structured output when possible: "respond only with a JSON object", "three sentences, no explanation", "return only the diff"  
\- Thinking tokens bill as output at $50/M even though the raw chain-of-thought is not returned — budget for them  
\- A truncated response wastes the full output cost plus the retry — treat truncation rate as a first-class cost metric

\---

\#\# 5\. Route the task

Not every task belongs on Fable 5\.

Route to Fable 5:  
\- Repo-wide refactors and migrations  
\- Novel-bug hunts across unfamiliar code  
\- Long-horizon research and multi-day autonomous work  
\- End-to-end tasks that take a person hours or days

Route to Opus 4.8 or Sonnet 5 instead:  
\- Single-file edits and simple refactors  
\- Documentation and code review on small PRs  
\- Interactive chat and quick clarifications  
\- Mechanical transforms with a known answer

Escalate to Fable only after a cheaper model has failed once on the same task.

\---

\#\# 6\. Keep this file lean

This CLAUDE.md is itself a token cost on every session.

\- Target 500 to 1,500 tokens total for the system-facing portion  
\- Remove any instruction that Fable 5 no longer needs — do not carry rules forward from older models  
\- Every removed sentence pays for itself on every call for the rest of this file's life  
\- Rewrite this file when the model changes, do not append to it

\---

\#\# 7\. Write lessons, not retries

Retries are the most expensive form of memory. Written lessons are the cheapest.

\- After every mistake, write one lesson to \`lessons/\` as a short Markdown file  
\- One lesson per file, one-line summary at the top, the reasoning below  
\- Reference the folder in this CLAUDE.md so Fable finds it without prompting  
\- A repeated mistake costs a full session; a written lesson costs a few input tokens forever

Example lesson structure:  
