# License and compliance obligations

Working reference for Job 4. **Not legal advice** — this identifies the real
questions and the traps. Where money, copyleft, or personal data are involved,
point counsel at the specifics.

The controlling question is almost never "is it open source?" It is **what does
using it this way oblige us to do, and can we live with that?**

---

## Software licenses

### Permissive — MIT, BSD, ISC

Do almost anything, including folding into closed-source commercial products,
keeping your own source private, and relicensing the result.

**Obligation:** preserve the copyright line and license text. Ship a `NOTICE` or
`THIRD-PARTY-LICENSES` file. This is a real obligation, routinely forgotten, and
trivially satisfiable.

**Verdict:** clear for nearly all commercial use.

### Apache-2.0

Permissive, but more legally comprehensive than MIT. Adds an **express patent
grant** (a genuine benefit to you), a **trademark clause**, and a requirement to
**document changes** to the files you modify.

**Trap:** Apache-2.0 is compatible with GPLv3 but **not GPLv2** — GPLv2 does not
accept the patent clause. If both are in the dependency tree, that is a real
conflict, not a technicality.

**Verdict:** clear, with attribution, change documentation, and NOTICE handling.

### GPL (v2, v3) — copyleft

Free to use, but derivative or combined works distributed to others must be
released under the same license.

**The trap that causes the most damage: copyleft propagates.** Your MIT project
plus one GPL dependency means the *entire distributed work* falls under GPL —
you didn't write the GPL code, you merely depended on it. Check the whole
transitive tree, not just direct dependencies.

**Distribution is the trigger.** Purely internal use generally does not trigger
disclosure. Historically this let SaaS operators run modified GPL code on their
servers for millions of users without any source obligation, because nothing was
"distributed."

**Verdict:** fine for internal tooling; a deliberate strategic choice for a
distributed product; usually a replace-it for a proprietary commercial product.

### AGPL — network copyleft

Written specifically to close the SaaS gap above. **Section 13 adds a network
interaction trigger:** if you modify an AGPL program and let users interact with
it over a network, you must offer them the corresponding source at no charge.

**Verdict:** for a web product this is the most consequential license in the
tree. Either accept releasing your source, or replace the dependency. Discover
this before building on it, not after.

### Proprietary, dual-licensed, "source available"

Read the actual terms; "open" in the marketing copy means nothing. Watch for
per-seat limits, revenue thresholds that flip you into a paid tier, field-of-use
restrictions, and BSL-style licenses that convert to open only after a delay.

---

## Data and content licenses

Data is where "free sources only" projects most often go wrong, because a
dataset can be free to *access* and still be unusable commercially.

### Public domain — US federal government works

Generally free of copyright and usable without restriction, commercially
included. USGS, NRCS, FEMA, NOAA, USDA and similar produce data in this
category.

**Verdict:** the safe core. Where a public-domain substitute exists for a
restrictively licensed source, prefer it and say so.

### CC0

Rights waived as far as possible. Effectively public domain. Attribution is
courteous, not required.

### CC-BY

Commercial use fine; attribution required in the form the licensor specifies.
Cheap to comply with — build attribution into the UI, not just a buried page.

### CC-BY-SA

Attribution plus share-alike: adaptations must carry the same license. Assess
whether your output counts as an adaptation before relying on it.

### CC-BY-NC — non-commercial

**Blocks commercial use entirely.** Fine for research, journalism, and personal
projects; the moment money is involved you need a separate agreement with the
rights holder.

**This is the single most common trap in a "free sources only" project.** NC
data is free to download and unusable in a product you charge for — including,
in most readings, a free product monetized by ads, referrals, or lead-gen.
Identify NC sources early and either license them properly or design around them.

### ODbL — Open Database License

Used by OpenStreetMap and datasets derived from it.

**Commercial use is explicitly permitted** — ODbL excludes no field of endeavour.
The complexity is share-alike, and it turns on a distinction worth getting right:

- A **Derivative Database** is created when you adapt, modify, enhance, correct,
  or extend the data. If you make it available to others, it must remain under
  ODbL.
- A **Produced Work** is something generated *from* the database — a map image,
  a report, a rendered plan. **You may license a Produced Work on any terms you
  like**, but you must, on request, offer recipients either the derived database
  under ODbL or the means to recreate it.

**Verdict:** usable commercially, including in a closed product, provided you
keep the derived database offerable and attribute properly. Misreading Produced
Work as Derivative Database — or vice versa — is the classic OSM-derived error.

### Sui generis database rights

In the EU and UK, a database can be protected independently of copyright in its
contents. A dataset whose individual facts are unprotectable may still be
protected as a compilation. Relevant when substantially extracting from a
European source.

### Scraped and ToS-governed sources

Scraping sits in genuinely unsettled territory and varies by jurisdiction.
Independent of copyright, a site's terms of service create contractual exposure,
and technical countermeasures may implicate anti-circumvention rules.

**Practical posture:** prefer a published bulk download or documented API over
scraping. Where scraping is the only route, read the ToS, respect `robots.txt`
and rate limits, and record the decision and its rationale in the register.
Never assume "it's publicly visible" settles the question — it doesn't.

### Academic, institutional, and non-profit datasets

Frequently free for non-commercial use with commercial terms available on
request, and frequently silent on licensing altogether. **Silence is not
permission.** Email and ask; a written yes costs one message and removes the
risk entirely.

### Proprietary scales, taxonomies, and indices

Rating systems, scoring scales, and curated taxonomies are often copyrighted or
trademarked even when widely cited in public literature. Cite freely; do not
embed one in a product without checking.

---

## Beyond licensing

Licensing is only one compliance axis. Also check:

**Personal data.** GDPR, CCPA and equivalents attach duties regardless of how the
data was licensed — lawful basis, minimization, retention limits, deletion
rights. Location data tied to a residence, health data, financial data, and
anything about minors raise the stakes sharply.

**Aggregation sensitivity.** Individually innocuous fields can become sensitive
when combined against an identifiable person or address. The compiled record can
be more regulated than any of its inputs.

**Sector regulation** applying to your customer even if not to you — financial
advice, medical claims, housing, employment, insurance.

**Claim substantiation.** Advertising standards apply to accuracy, performance,
and comparative claims. This is where Job 5 messaging meets Job 4 clearance:
never let a tagline assert something the dossier can't support.

**Trademark**, covered in the naming playbook.

---

## The register

Output of Job 4. One row per source, no exceptions.

| Source | What it gives us | License | Obligation | Commercial OK? | Verdict |
|---|---|---|---|---|---|

Verdicts: **clear** · **clear with obligation** (name it) · **needs a license**
(name who to ask) · **replace** (name the substitute).

Close with the questions worth putting to actual counsel. A short, specific list
is far more useful to a lawyer — and far cheaper — than a general request to
review the project.
