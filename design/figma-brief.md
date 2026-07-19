# Codex Speed Doctor Figma Brief

## Goal

Design a polished GitHub project page and README visual system for **Codex Speed Doctor**, a local-first diagnostic CLI for slow Codex startup.

Positioning line:

> Find why Codex feels slow before you clean anything.

Tone: engineering-led, precise, calm, trustworthy, and quietly playful. The
engineer investigates evidence while Doraemon represents the right reversible
tool—not a magic cleanup button.

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

Use a refined Japanese editorial illustration system:

- warm ivory washi-paper background with subtle blue atmosphere
- Doraemon sky blue, white, red, and yellow accents with deep indigo ink
- sumi-like linework and watercolor texture in generated illustrations
- precise information hierarchy and generous breathing room
- rounded future-gadget details used sparingly
- no long text baked into AI-generated images; labels remain real HTML/Figma text
- pair every illustration with a title, explanation, accessible alt text, and caption

## Palette

| Role | Hex |
| --- | --- |
| Ink | `#17324d` |
| Muted text | `#496174` |
| Subtle text | `#6c7f8d` |
| Paper | `#fffaf0` |
| Panel | `#fffdf7` |
| Line | `#d8e3df` |
| Teal | `#187e9d` |
| Cyan | `#149bd7` |
| Blue | `#1167a8` |
| Red | `#e54b4b` |
| Yellow | `#f3c84b` |
| Green | `#16a34a` |
| Amber | `#d97706` |
| Danger | `#dc2626` |

## Typography

Use a distinctive editorial pairing:

- headings: Iowan Old Style / Hiragino Mincho / Yu Mincho
- body: Avenir Next / Hiragino Sans / Yu Gothic

- Hero H1: 56-64 px desktop, 36 px mobile, strong weight
- Section H2: 32-36 px desktop, 28 px mobile
- Body: 16-18 px, line height 1.6
- Code: SF Mono / Consolas / Liberation Mono
- restrained negative tracking is allowed on large Latin headings only

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

3. **v0.5.0 Release Story**
   - Source path confinement
   - Filesystem/database agreement
   - Fail-closed process blockers
   - Regression-tested safety

4. **Command Panel**
   - Terminal-style command block
   - Show source run and JSON mode
   - Keep command text selectable

5. **Local State Map**
   - Use `docs/assets/local-state-map.png`
   - Add real text callouts for sessions, logs, plugins, skills, model cache

6. **Handoff Before Archive**
   - Five-step flow: Diagnose, Handoff, Archive, Index, Restore
   - Use `docs/assets/handoff-archive-flow.png`

7. **Safety Boundary**
   - Safety checklist beside or above `docs/assets/safety-boundary.png`
   - Explicitly state no automatic cleanup and no credential file readout

## Components

- Card radius: 18 px
- Buttons: pill shape, 44 px minimum height
- Language switch buttons: compact segmented control, active language clearly filled
- Section bands: full-width, not floating page cards
- Image frames: single border, one accurate explanatory caption, no nested cards
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

Doraemon is a third-party fictional character. Keep an unaffiliated-project
disclaimer in the README, and do not imply endorsement or ownership.

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
