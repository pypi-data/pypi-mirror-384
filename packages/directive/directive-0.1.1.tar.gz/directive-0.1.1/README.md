# Directive: Spec‑first approach to working with AI coding agents

Spec first, chat less. 

Increase coding agent accuracy and developer efficiency by replacing ad‑hoc back‑and‑forth with concise, versioned specs that become the canonical history of your work.

Problems this aims to solve:
- **Improving agent accuracy and developer efficiency**: Clear specs reduce ambiguity and rework, speed up iterations, and align expectations between humans and agents.
- **Replacing chatty back‑and‑forth with upfront, versioned specs**: Author concise specs first to avoid prompt drift; keep a single source of truth that onboards collaborators quickly.
- **Specs as durable, reviewable artifacts and canonical history**: Spec → Impact → TDR live in the repo, capturing decisions and enabling traceability; Spec→Test mapping turns requirements into verification.

How it works (brief): Work is gated by explicit review checkpoints — **Spec → Impact → TDR** — with no code before approval. After approval, follow strict TDD with Spec→Test mapping. Everything lives in‑repo as plain files that agents can access directly, with optional MCP server integration for enhanced IDE features. See the supporting background in [Research & Rationale](#research--rationale).

> **Note**: Directive is a *way of working* with agents, not a rigid standard. The templates, workflow, and rules are starting points designed to be customized for your team's practices. Think of it as best-practice scaffolding that you adapt to fit your specific needs — whether that's simplifying steps, adding domain-specific checks, or adjusting terminology. The goal is to give agents clear, consistent context that matches how you actually work.

## Quickstart

- Install (using uv):
  - In a project: `uv add directive` (adds to `pyproject.toml` and `uv.lock`)
- Initialize defaults in your repo:
  - `uv run directive init` (non-destructive; creates `directive/` with AOP, Context, and templates)
    - You'll be prompted: "Add recommended Cursor Project Rules? (Y/n)". If you accept (default Yes), it will create `.cursor/rules/directive-core-protocol.mdc` with the core workflow rules.
- (Optional) Configure MCP server for advanced IDE integration:
  - The MCP server is optional and can be set up manually if needed (see "Using with Cursor" section below)
  - Command: `uv run directive mcp serve` (stdio)
  - Tools are auto-discovered via `tools/list`; the agent will fetch Spec/Impact/TDR templates and context automatically.
- (Optional) Inspect a bundle directly:
  - `uv run directive bundle spec_template.md` (prints a JSON bundle to stdout)

### Using with Cursor (or any AI coding assistant)

1. Install and initialize:
   - `uv add directive`
   - `uv run directive init`
2. Accept Cursor Project Rules when prompted (recommended):
   - Creates `.cursor/rules/directive-core-protocol.mdc` which tells agents to follow the Directive workflow
   - This is usually all you need — the directive files are plain text that agents can read directly

### Optional: MCP Server (probably not needed)

The MCP server provides programmatic access to templates and context files. **Most users won't need this** — agents work fine reading the `directive/` folder directly.

If you want to set it up anyway (works with Cursor or any MCP-compatible tool):

1. Create or update `.cursor/mcp.json` (or your IDE's equivalent):
```json
{
  "mcpServers": {
    "Directive": {
      "type": "stdio",
      "command": "/usr/bin/env",
      "args": ["-S", "uv", "run", "-q", "-m", "directive.cli", "mcp", "serve"],
      "transport": "stdio"
    }
  }
}
```

2. The server exposes these tools:
   - `directive/templates.spec`: Spec bundle (AOP, Agent Context, Spec template)
   - `directive/templates.impact`: Impact bundle
   - `directive/templates.tdr`: TDR bundle
   - `directive/files.get`: Read any file under `directive/`
   - `directive/files.list`: List all files under `directive/`

## Workflow

The Agent Operating Procedure (`/directive/reference/agent_operating_procedure.md`) is a concise, enforceable checklist that defines the Spec → Impact → TDR → Implementation flow and its review gates.

To use it in your project, simply include the `/directive/reference/` directory in your agent's context (contains `agent_operating_procedure.md`, `agent_context.md`, and templates). Agents can read these files directly — no special tooling required.

Step 1 — Customize Agent Context
- Tailor `/directive/reference/agent_context.md` to your project (languages, tooling, conventions, security, testing). Refer to `agent_operating_procedure.md` for the end‑to‑end flow.

Step 2 — Spec (behavior/UX‑only)
- Define desired behavior, interfaces, user outcomes, and clear acceptance criteria. Save as `/directive/specs/<feature>/spec.md` (template: `/directive/reference/templates/spec_template.md`).

Step 3 — Impact Analysis (approve before TDR)
- Identify modules/packages touched, contract changes (APIs/events/schemas/migrations), risks, and observability needs. Save as `/directive/specs/<feature>/impact.md` (template: `/directive/reference/templates/impact_template.md`).

Step 4 — Technical Design Review (TDR) (approve before coding)
- Decide interfaces and behavior. Include a brief Codebase Map, data contracts, error handling, observability, rollout, and Spec→Test mapping. Save as `/directive/specs/<feature>/tdr.md` (template: `/directive/reference/templates/tdr_template.md`).

Step 5 — Start implementation (after TDR approval)
- Begin coding guided by the TDR and your `agent_context.md`. Use tests to validate behavior and keep CI green.

Gates: Spec → Impact → TDR → Implementation (no code before TDR approval).
 
## Research & Rationale

This framework is grounded in current best practices for **spec‑driven development** with AI coding agents. Below is a distilled summary of the sources we align to and the principles that inform the workflow.

---

### Key Practices from the Field

### 1. Make the Spec the Source of Truth
- Specs live in the repo, not in ephemeral chats.  
- They drive planning, tasks, and validation.  
- GitHub’s **Spec Kit** formalizes this into a 4-phase loop: **Specify → Plan → Tasks → Implement**.  
- Specs aren’t static — they are executable artifacts that evolve with the codebase.  
🔗 [Spec Kit (GitHub Blog)](https://github.blog/news-insights/product-news/spec-kit/)

---

### 2. Separate the Stable “What” from the Flexible “How”
- Capture **what** the system must do in product terms (user outcomes, interfaces, acceptance criteria).  
- Keep **how** it is built flexible and expressed later in technical design docs.  
- Example: Kiro’s approach outputs `requirements.md`, `design.md`, and `tasks.md` separately.  
🔗 [Kiro: Spec-First Development](https://kirorun.notion.site/Kiro-Spec-First-Development-Docs)

---

### 3. Tie Every Requirement to a Test (“Executable Specs”)
- Every spec clause must map to a test, often written in **Given–When–Then** (BDD style).  
- Track **spec coverage** (all spec items tested) in addition to code coverage.  
- This ensures agents are judged against explicit requirements, not guesses.  
🔗 [Executable Specifications & BDD (Cucumber)](https://cucumber.io/docs/bdd/)

---

### 4. Use the Agent to Draft the Spec, Humans to Edit
- Approaches like **“Vibe Specs”** let the LLM propose the first draft through Q&A.  
- Humans then critique, clarify, and cut scope creep.  
- The refined spec becomes the north star for implementation.  
🔗 [Vibe Spec Method](https://vibespec.org/)

---

### 5. Practice “Context Engineering,” Not Just Prompting
- Agents perform better when given **durable, file-based context packs**:  
  - Rules/conventions  
  - Example code patterns  
  - Data contracts and schemas  
  - Documentation links  
- Repos that include a **global rules file** plus examples see much higher fidelity.  
🔗 [Context Engineering (GitHub Copilot best practices)](https://github.blog/ai-and-ml/context-engineering-for-agents/)

---

### 6. Choose Method by Risk/Complexity; Enforce Verification
- For low-risk features: lightweight specs may suffice.  
- For high-risk or complex builds: follow **Spec-Then-Code**, with rigorous review gates.  
- Use **multi-AI cross-review** or human checkpoints where the blast radius is large.  
🔗 [Spec-Then-Code Methodology](https://www.spec.dev/spec-then-code)

---

### 7. Industry is Moving Toward Templates
- Beyond open-source tools, groups like **TM Forum** have published formal **AI Agent Specification Templates** for enterprise contexts.  
- Standardization is arriving, which signals the importance of shared spec formats.  
🔗 [TM Forum AI Agent Specification Template](https://www.tmforum.org/)

---

### 8. A Pragmatic Solo/Dev Flow Works Today
- A repeatable loop many developers use:  
  1. Brainstorm a spec  
  2. Generate a step-by-step plan  
  3. Execute with a codegen agent in **small, testable chunks**  
  4. Keep artifacts checked into the repo (`spec.md`, `prompt_plan.md`, `todo.md`).  
🔗 [Solo Dev Spec Loop (Indie Hackers)](https://www.indiehackers.com/post/spec-driven-ai-development)

---

### Takeaway
- Specs must be **concise, testable, and versioned**.  
- AI agents thrive when specs are paired with **context packs** and a **TDD-first workflow**.  
- The winning approach is not over-specifying implementation, but rigorously specifying **outcomes, contracts, and tests**.


