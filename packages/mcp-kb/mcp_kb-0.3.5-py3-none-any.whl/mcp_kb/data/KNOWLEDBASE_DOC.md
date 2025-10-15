# LLM Operating Manual — MCP Knowledge Base (`mcp-kb`)

You are connected to a **local, text-only knowledge base**. Your job is to **search, read, create, update, and soft-delete** UTF‑8 text files under a single root directory while respecting safety rules below. Use the provided MCP tools exactly as specified.

---

## Ground Rules (enforced by the server)

- **Paths are relative only.** Absolute paths are rejected. No `..` traversal.
- **Protected folder:** `.data/` is read‑only. Do not write there.  
- **Soft delete sentinel:** Files marked with `_DELETE_` in the name are considered deleted. Do not read/write them.
- **Text files only.** Binary-ish files are ignored by scans. Treat this KB as UTF‑8 text storage.
- **Concurrency:** Writes are serialized per file; still prefer read‑verify‑write sequences.

Constants (baked into the server):
- Protected folder: `.data`
- Documentation file name: `KNOWLEDBASE_DOC.md`
- Delete sentinel: `_DELETE_`

---

## Tools You Can Call

All tool names and parameter contracts are stable. Stick to these shapes.

### `create_file(path: str, content: str, tags?: list[str]) -> str`
- Create or **overwrite** a text file at `path` with `content`.
- Optional `tags` lets you seed explicit metadata.
- `path` must be **relative** and **outside** `.data/`.

### `read_file(path: str, start_line?: int, end_line?: int) -> { path, start_line, end_line, content }`
- Read full file or a 1‑based inclusive slice.  
- If both bounds omitted ⇒ full file. If one bound omitted ⇒ server fills it.

### `append_file(path: str, content: str, tags?: list[str]) -> str`
- Append text. If file is missing, it will be **created**.
- Optional `tags` replaces the explicit tag list for the document (useful when a major edit changes categorisation).

### `regex_replace(path: str, pattern: str, replacement: str) -> { replacements: int }`
- Multiline regex (`re.MULTILINE`). Returns count. Always `read_file` afterwards to verify.

### `delete(path: str) -> str`
- **Soft delete**: renames `name.ext` to `name_DELETE_.ext`. Use when content is obsolete.

### `search(query: str, limit: int = 5) -> [{ path, line, context: string[] }]`
- Returns up to `limit` matches with short context.
- If Chroma mirroring is active, results are **semantic** first; otherwise plain scan.
- `limit` must be **> 0**.

### `overview() -> str`
- A deterministic `tree`-like view of active files under root (skips deleted and binaries). At the end, a **Tags** section lists every unique tag known to the metadata catalogue.
- Use this only if necessary, and dont try to find content by file titles unless normal search is not fruitful.

### `documentation() -> str`
- Returns this manual.

### `add_tags(path: str, tags: list[str]) -> str`
- Merge cleaned `tags` into the document’s explicit metadata list. Duplicates and blank values are ignored.
- Fails if the file does not exist or `tags` is empty.

### `remove_tags(path: str, tags: list[str]) -> str`
- Remove the supplied `tags` from the explicit metadata list. Missing labels are silently skipped.
- Use this to retire stale labels without editing the main document body.

### `list_files_by_tags(tags: str | list[str], match_mode: Literal["any","all"]="any") -> [{ path, matched_tags, match_count, all_tags, explicit_tags }]`
- Accepts either a single tag or a list of tags. Tags are trimmed; blanks are rejected.
- `match_mode="any"` lists files containing **at least one** tag (sorted by match count, descending).
- `match_mode="all"` limits results to files containing **every** supplied tag.
- Use this to audit coverage or discover related documents quickly.

---

## How to Work Effectively

### 1) Discover
- Call `overview()` to understand the tree.
- Use this for overview only and where to place knowledge, dont find concent by file titles unless normal search is not fruitfull.

### 2) Locate Content
- Prefer `search("keywords", limit=5)` to find candidate files/snippets.
  - Examine each `{path, line, context}`. The `context` is a short window around the hit.
  - If results look thin, **increase `limit`** (e.g., 10–20) before broadening the query.

### 3) Read Precisely
- Use `read_file(path)` for the full file when structure matters.
- If the file is large but you know the region, use `read_file(path, start_line, end_line)` to minimize tokens.

### 4) Create New Knowledge
- Pick a **descriptive relative path** (folders based on topic, kebab‑case names).
  - Example: `architecture/decision-records/adr-2025-10-06-edge-cache.md`
- Call `create_file(path, content, tags=[...])` to capture initial tags (team, area, status, etc.).
- Keep the **title as the first Markdown heading** so search has context.
- Link related files with **relative Markdown links**.

### 5) Update Safely
- For small edits:  
  1) `read_file(...)` to confirm current state.  
  2) `regex_replace(path, pattern, replacement)` for targeted changes.  
  3) `read_file(...)` again to verify.
- For additive changes: `append_file(path, "\n...", tags=[...])` when you need to refresh explicit tags.
- Use `add_tags` / `remove_tags` when you only need to adjust metadata labels without touching the document body.

### 6) Deletion Policy
- Use `delete(path)` to **soft-delete**. Do not operate on files that already include `_DELETE_` in their name.

---

## Search Semantics (important)

- When Chroma ingestion is **enabled**, `search()` uses semantic ranking first and returns the **best slice per file** (the ingestor extracts one representative match per document chunk/file). If no obvious line match is found, you may get a **top-of-file preview** — then call `read_file()` to confirm.
- When Chroma is **not** enabled, `search()` scans files literally and returns all matches up to `limit`.
- Always **validate** by fetching the file segment with `read_file()` before making edits.

---

## Parameter Contracts and Gotchas

- `path` must be **relative** (e.g., `notes/today.md`). Absolute paths are rejected.
- Do **not** write into `.data/` (protected). Reads are allowed there.
- Line numbers in `read_file` are **1‑based** and the interval is **inclusive**.
- `regex_replace` uses Python’s `re.MULTILINE`. Validate your pattern; avoid overly broad substitutions.
- `append_file` will create a file if missing (useful for logs/progress notes).

---

## Typical Recipes

**Find → Read → Edit**
1. `search("beta feature toggle", limit=10)`
2. Pick a result: `read_file("features/toggles.md", 40, 80)`
3. Adjust: `regex_replace("features/toggles.md", "^Status:.*$", "Status: Enabled")`
4. Verify: `read_file("features/toggles.md")` (check the `Status:` header)

**Add a new doc**
1. `create_file("ops/runbooks/cache-invalidation.md", "# Cache Invalidation\n\n…", tags=["ops", "runbook"])`
2. Optionally link it from an index: `append_file("ops/README.md", "\n- [Cache Invalidation](runbooks/cache-invalidation.md)", tags=["ops"])`

**Re-tag an existing doc without editing content**
1. `add_tags("ops/runbooks/cache-invalidation.md", ["critical"])`
2. `remove_tags("ops/runbooks/cache-invalidation.md", ["runbook"])`
3. `list_files_by_tags(["ops", "critical"], match_mode="all")` to confirm the new combination appears exactly once.

**Find docs by tag combination**
1. `list_files_by_tags(["adr", "status:accepted"], match_mode="all")`
2. Open the returned paths (highest `match_count` first) to review the relevant documents.

**Soft delete an obsolete note**
1. `delete("notes/old-incident.md")`

---

## Error Recovery

- **"Absolute paths are not permitted"** → Use a **relative** path.
- **"Writes are not allowed inside the protected folder '.data'"** → Choose a different folder (e.g., `docs/`).
- **"File 'X' does not exist"** on delete → Confirm with `overview()` or `search()`. Only existing non‑deleted files can be soft‑deleted.
- **No search hits** → Widen keywords, increase `limit`, or pivot to `overview()` to eyeball likely locations.

---

## Things You Should Not Do

- Do not fabricate file contents or paths. Always confirm with `overview()`, `search()`, and `read_file()`.
- Do not operate on files that include `_DELETE_` in their name.
- Do not attempt to talk directly to Chroma; you only use `search()`. Indexing is handled automatically after writes.
- Do not write binary or non‑UTF‑8 content.

---

## Performance Hints

- Prefer `search()` + targeted `read_file()` slices over reading entire large files.
- Keep `limit` modest (5–10) unless you must broaden the search.
- Batch edits in one file using a single `regex_replace` when safe (then verify).

---

You now have the minimal contract to operate this KB safely and efficiently.
