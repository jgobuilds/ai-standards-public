# Brand & visual identity (house lens)

The visual counterpart to [`naming-standard.md`](naming-standard.md): that file
governs what we *call* things, this one governs what they *look like*. Any output
an agent generates that a human will see — an HTML page, a dashboard, a report, a
chart, a slide, a diagram — is rendered in the org's identity, not in a model's
default styling.

This lens is the reusable **method and token contract**. It carries no real
palette on purpose, so the framework stays org-neutral and no one's identity is
baked into it.

## Where the values live

Real token **values** live in a private instance overlay (for this org,
`<org>-instance/brand/brand-tokens.css`), loaded at onboarding — never in
this framework. [`brand-tokens.css`](brand-tokens.css) here is the neutral
**contract**: the variable names plus obvious placeholders. An instance overrides
the values by variable name; the method below is what stays constant.

## Rules for generated output (org-agnostic — these are the standard)

- **Use tokens, don't invent color.** Pull from the loaded token set; if you need
  a shade that isn't there, tint an existing token, don't add a new hue.
- **Charts follow one fixed categorical order** (defined in the token set).
  Sequential scales tint one hue; diverging scales run two.
- **Contrast is a gate, not a preference.** Body text and chart marks meet WCAG
  AA. Keep palettes colorblind-safe — never color as the only signal; add shape
  or a label.
- **Light and dark both work.** Map every token; don't ship a light-only artifact
  into a dark shell.
- **Restraint.** One accent job per color. Generous white space, few weights.
- **Typography** is set by the token set (`--brand-font-head`, `--brand-font-body`);
  the neutral default is `system-ui`.

## How this plugs into onboarding

An agent coming up to speed loads three things before it produces anything:
**architecture** (what's running), **standards** (the review lenses here, incl.
`change-safety` and `pii-controls`), and **brand** (this lens + the loaded token
set — from the private instance overlay if present, else the neutral contract).
Outputs are then tailored to all three: built to standard, named in house style,
rendered in the loaded palette. A repo wires this in by adding `brand` to its
`.engineering-standard/config.yml` lenses and pointing its onboarding at the
tokens.
