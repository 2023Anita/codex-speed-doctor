# Codex Speed Doctor Figma Brief

## Goal

Design a polished GitHub project page and README visual system for **Codex Speed Doctor**, a local-first diagnostic CLI for slow Codex startup.

Positioning line:

> Find why Codex feels slow before you clean anything.

Tone: clinical, precise, calm, trustworthy. Treat Codex slowness like a local-state health check.

## Audience

- Developers using Codex Desktop or CLI
- Users with large local sessions, many skills/plugins, or confusing startup stalls
- Maintainers who want a safe first diagnostic step before cleanup

## Frames

- Desktop GitHub Pages: `1440 x 1600`
- Tablet: `834 x 1194`
- Mobile: `390 x 1200`
- README image crops: keep the 16:9 assets readable at GitHub markdown width

## Visual Direction

Use a medical diagnostic interface style:

- bright clinical background
- blue, teal, cyan, and white as primary colors
- small amber/red accents only for warnings
- precise panels, thin dividers, soft shadows
- no official brand marks or fake app logos
- no text baked into AI-generated images; labels should be real HTML/Figma text layers

## Palette

| Role | Hex |
| --- | --- |
| Ink | `#0f172a` |
| Muted text | `#475569` |
| Subtle text | `#64748b` |
| Paper | `#f8fbfd` |
| Panel | `#ffffff` |
| Line | `#d9e7ef` |
| Teal | `#0f766e` |
| Cyan | `#0891b2` |
| Blue | `#1d4ed8` |
| Green | `#16a34a` |
| Amber | `#d97706` |
| Danger | `#dc2626` |

## Typography

Use system UI or Inter.

- Hero H1: 56-64 px desktop, 36 px mobile, strong weight
- Section H2: 32-36 px desktop, 28 px mobile
- Body: 16-18 px, line height 1.6
- Code: SF Mono / Consolas / Liberation Mono
- Do not use negative letter spacing

## Page Structure

1. **Hero**
   - Full-bleed image background using `docs/assets/hero-codex-diagnostic.png`
   - Overlay text, not a floating card
   - Language switcher for 中文 / English / 日本語 / 한국어
   - Primary CTA: Open README
   - Secondary CTAs: Safety boundary, Troubleshooting

2. **Trust Strip**
   - Four compact cards:
     - Read-only
     - Pseudonymous
     - Handoff-first
     - Backup-aware

3. **Command Panel**
   - Terminal-style command block
   - Show source run and JSON mode
   - Keep command text selectable

4. **Local State Map**
   - Use `docs/assets/local-state-map.png`
   - Add real text callouts for sessions, logs, plugins, skills, model cache

5. **Handoff Before Archive**
   - Five-step flow: Diagnose, Handoff, Archive, Index, Restore
   - Use `docs/assets/handoff-archive-flow.png`

6. **Safety Boundary**
   - Safety checklist beside or above `docs/assets/safety-boundary.png`
   - Explicitly state no automatic cleanup and no credential file readout

## Components

- Card radius: 8 px maximum
- Buttons: 8 px radius, 44 px minimum height
- Language switch buttons: compact segmented control, active language clearly filled
- Section bands: full-width, not floating page cards
- Image frames: single border, one caption, no nested cards
- Terminal panel: dark code area with light top chrome

## Localization

The GitHub Pages page must support seamless in-page switching between:

- 中文
- English
- 日本語
- 한국어

Rules:

- Do not reload the page when switching languages.
- Persist the selected language locally.
- Translate all visible page copy, image alt text, and metadata description.
- Keep command snippets unchanged except for comments when needed.
- Keep generated images text-light; all important labels should remain editable UI text.

## Image Assets

Use these exact project assets:

- `docs/assets/hero-codex-diagnostic.png`
- `docs/assets/local-state-map.png`
- `docs/assets/handoff-archive-flow.png`
- `docs/assets/safety-boundary.png`

Do not place important labels inside the images. Add labels as editable Figma text or HTML.

## Safety Copy Requirements

Include these ideas exactly, but phrase them naturally:

- default report is read-only
- no automatic cleanup
- no session moves
- no worktree archive
- no `config.toml` rewrite
- no `auth.json` read or output
- raw paths and raw session filenames are opt-in through `--details`

## Export Notes

- Export final screenshots as PNG for README if needed.
- Keep all exported images free of private paths, real session names, credential material, and official logos.
- Prefer `/docs` as the GitHub Pages source.
