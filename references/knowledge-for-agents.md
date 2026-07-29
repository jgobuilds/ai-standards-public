# Knowledge an agent can actually use (house lens)

How to store a body of knowledge so an agent finds the right part of it, cheaply,
and does not confidently quote something that stopped being true.

The short answer, which is also the counterintuitive one: **human-readable
Markdown is the source of truth, with a thin machine-readable index generated on
top of it** — not an opaque machine-only format. What follows is why, and the
three things that turn a pile of Markdown into something navigable.

## 1. Markdown for knowledge, structured formats for records

Split by the *shape* of the information, not by who reads it:

| Shape | Format | Why |
|---|---|---|
| Knowledge, procedures, reasoning context | **Markdown** | models parse headings/lists/tables natively, and it costs roughly 40–60% fewer tokens than the same content in JSON, whose braces and quotes carry no meaning |
| Strict schemas, config, records with fields, deterministic tool output | **JSON / YAML** | the shape *is* the contract, and something validates it |

The mistake worth naming: "machine-readable but not human-readable" usually makes
retrieval **worse**. A model is a reasoning engine trained on human prose, not a
database. And human readability is load-bearing for a second reason — if a
maintainer cannot scan the source and see what it says, it will drift, and
nobody will notice.

Google's Open Knowledge Format (June 2026) formalises the same shape:
Markdown files with YAML frontmatter, cross-linked into a graph, plus an index
for navigation.

## 2. Findability: agentic search first, retrieval infrastructure only when it earns it

The old default was: embed everything into a vector store, retrieve top-k chunks.
That has largely been displaced for corpora of ordinary size by **agentic
search** — the agent keeps lightweight identifiers (paths, IDs, queries) and
loads content on demand with find/grep/open, the way a person reads a codebase.
Anthropic named this "just-in-time context loading"; Claude Code dropped
RAG-plus-vector-DB for it, because the index adds staleness, security surface and
operational cost that plain filesystem search does not.

The honest caveat: this is **scale-dependent**. At large scale, production
converges on hybrid retrieval. So the rule is a ladder, not a doctrine:

1. **Filesystem + grep over well-named, well-ID'd Markdown.** Start here. For a
   corpus in the hundreds of atoms this is usually the whole answer.
2. **Keyword index** when grep gets slow or the vocabulary diverges from the
   words people search with.
3. **Vector/semantic** as an *additional layer* when neither of the above finds
   things people expect it to — never as the first move, and never alone.

Do not skip to 3. A vector store you did not need is a second copy of your
knowledge with no time dimension (see §4) and no obvious failure mode.

## 3. Progressive disclosure: a catalog, then the detail

Give the agent a compact map to read first — one line per atom, a couple of
hundred tokens — so it decides what to pull before pulling anything. Then it
descends.

**Be honest about what this buys.** A controlled ablation found that a capable
agent often does not read the index at all: it infers where a page must be from
the question and opens it directly. Measured savings were meaningful (roughly a
third to over half) but quality was *non-inferior*, not better. So:

> The catalog is a **cost** optimisation, not a quality one. Descriptive file
> names, clean headings and predictable paths do as much work as the index — and
> they help even when the index is skipped.

Which means: spend the effort on naming and structure first, generate the
catalog second, and never let the catalog become a thing maintained by hand.
Generate it from the same source the machine index comes from, or it will drift
and be worse than nothing.

Both the machine index and the catalog are **generated artifacts**, and the
drift failure that lens describes applies with extra force here: a stale index
is not merely wrong, it is *believed*. Mark them generated, regenerate in the
build, and gate drift in CI — see `generated-artifacts.md`.

For a public site, the same idea has a name: `llms.txt` at the site root — a
curated plain-text roadmap that states facts directly, without the marketing
scaffolding a model would have to see past.

## 4. Freshness is a field, not a vibe

The failure mode that bites hardest is **staleness**, and retrieval by similarity
is structurally blind to it: a six-month-old fact and yesterday's are equally
"similar" to a query, so a superseded fact is returned with full confidence. That
is a silent wrong answer, which is the expensive kind.

- **Every atom carries a `last_verified` date.** Not "created", not "modified by
  a formatter" — the date a human or a check last confirmed it is still true.
- **Supersede, never rewrite.** Mark the old fact superseded and point at what
  replaced it. Rewriting history destroys the ability to answer "was this true
  when we said it?"
- **Stale is a warning, not a deletion.** Past a threshold, the catalog says so
  and the agent can weigh it. Silently dropping old facts is how a corpus
  quietly loses its long tail.

## 5. Relationships: IDs and cross-links are enough

Stable IDs plus `[ID]` cross-references make a Markdown bundle a graph at
almost no cost, and a build that **fails on an unresolved reference** keeps it
honest — a dangling citation is a broken promise in a corpus whose value is that
every claim traces to a source.

Full GraphRAG is genuinely stronger for multi-hop questions, and genuinely
expensive: graph construction is often prohibitive for a corpus that changes.
Reserve it for dense, relationship-heavy bodies of knowledge, and only after
IDs-plus-links has demonstrably run out.

## The checklist

- [ ] Knowledge is Markdown; only records and config are JSON/YAML.
- [ ] Every atom has a **stable ID** and cross-references resolve, enforced by a build.
- [ ] A **machine index** (ID → file + anchor + summary) is generated, never hand-written.
- [ ] A **navigational catalog** — one line per atom — is generated from that same index.
- [ ] Every atom carries **`last_verified`**; superseded facts are marked, not deleted.
- [ ] Retrieval starts at filesystem + grep. Anything more is justified by a measured failure, and stated as one.
- [ ] The index and catalog are marked generated and gated for drift (`generated-artifacts.md`).
- [ ] File names and headings are descriptive enough that an agent can guess the path — because it often will, instead of reading the index.

## Worked example

The enablement-kit suite in this workspace is this architecture: a Markdown
knowledge base as the source of truth, `[ID]` cross-references, a generated
`kit.json` machine index resolving every ID to a file and anchor, a generated
`CATALOG.md` navigational map, `last_verified` frontmatter, and a build that
fails CI on an unresolved reference.
