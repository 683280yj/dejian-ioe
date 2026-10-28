# 筹策官网服务卡片 Design QA

- Source visual truth: current-turn Browser comments 1–3 on `https://cc.idky.tech/#case` (annotated mobile captures at a `390 × 844` CSS viewport).
- Implementation: local preview `http://127.0.0.1:8765/#services`.
- Implementation screenshots:
  - `output/design-qa/service-card-1-mobile.png`
  - `output/design-qa/service-card-2-mobile.png`
  - `output/design-qa/service-card-3-mobile.png`
- Source attachment pixels: `752 × 1344` for each annotated capture, displayed at approximately 2× density with browser chrome and surrounding sections.
- Implementation screenshot pixels: `346 × 368`, `346 × 369`, `346 × 369`, captured at device scale factor 1 from the card content region.
- Comparison normalization: component-region comparison at the same `390px` CSS viewport; browser chrome, sticky navigation, annotation markers and surrounding sections were excluded from fidelity judgments.
- State: service cards at rest; mobile and desktop responsive layouts.

## Full-view comparison evidence

The source captures show the card links occupying the same vertical space as the last line of body copy, with the underlined link text visually colliding with the paragraph. The second card also uses an abstract `⌁` glyph that does not communicate replenishment. The revised implementation gives every card a normal document-flow footer with a 27px copy-to-action gap and a 52px-high action control. At `1440px`, all three cards render at an equal `370px` height. At `320px`, the document remains `320px` wide with no horizontal overflow.

## Focused region comparison evidence

- Card 01: body copy and “查看功能详情” no longer overlap; warehouse icon now communicates inventory.
- Card 02: the abstract glyph is replaced by the project’s replenishment icon; “查看补货逻辑” is a full-width action with a clear arrow affordance.
- Card 03: body copy and “查看交付方式” no longer overlap; role/permission shield icon matches the card content.

## Required fidelity surfaces

- Fonts and typography: existing CSans/CSerif families, weights, line heights and hierarchy are preserved. Button text remains 14px bold and readable.
- Spacing and layout rhythm: copy-to-action spacing is consistently 27px on mobile; icons are 58px containers with 28px assets; desktop cards have equal height.
- Colors and visual tokens: existing wine, warm gold, paper and ink tokens are retained. New controls use the existing border and paper palette.
- Image quality and asset fidelity: text glyphs were replaced by project-owned SVG assets based on the existing licensed icon set; no placeholder or CSS-drawn icon remains.
- Copy and content: card body copy and destinations are unchanged; action labels are clarified to “查看功能详情 / 查看补货逻辑 / 查看交付方式”.

## Comparison history

### Pass 1

- P1: mobile action links overlap body copy because they are absolutely positioned inside cards with insufficient height.
- P2: abstract service glyphs do not communicate inventory, replenishment or permissions.

Fixes applied:

- Converted cards to flex-column layout and kept actions in normal document flow.
- Added consistent 48px-minimum action controls and 27px mobile separation.
- Replaced all three text glyphs with licensed/project-owned business icons.

### Pass 2

- Verified at 390px and 320px mobile widths and at 1440px desktop width.
- Verified the “查看交付方式” anchor interaction.
- Browser console: no warnings or errors.
- No remaining P0/P1/P2 findings.

final result: passed
