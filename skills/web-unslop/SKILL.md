---
name: web-unslop
description: "Strict frontend anti-slop workflow for building, reviewing, or redesigning web apps, SaaS dashboards, landing pages, analytics screens, billing/pricing pages, creation forms, modals, and AI-generated UI. Use when Codex must polish a frontend, remove vibe-coded design tells, make software look professional, audit UX quality, or turn a functional prototype into intentional product UI."
---

# Web Unslop

Use this as a shipping gate, not a mood board. The goal is to remove AI-looking UI tells and make the product feel designed around real user tasks.

If editing code, fix the issues. If reviewing, report only concrete failures with the screen/area and exact correction.

## Audit Loop

- [ ] Render the UI before judging it. Use desktop around 1440px wide and mobile around 390px wide.
- [ ] Identify the product type, primary user, and primary workflow before changing visuals.
- [ ] List the actual screens present: app shell, dashboard, list/table, analytics, billing, pricing, creation flow, settings, landing page.
- [ ] Search the code for slop tells: emoji, `bg-gradient`, `gradient`, `rounded-full`, fake initials, placeholder stats, duplicate KPI components, fake cards, unused buttons, lorem/demo copy, generic feature icons.
- [ ] Remove or merge before adding. Most vibe-coded UI is too many equal-weight boxes.
- [ ] Make one focused pass per page type below.
- [ ] Re-render desktop and mobile. Do not call it done from code inspection alone.

## Instant Fail Tells

- [ ] No emoji as interface icons. Replace with the existing icon system; use Lucide only if the app has no standard.
- [ ] No random rainbow accents. Use neutral surfaces, one brand accent, semantic status colors, and data colors only where they carry information.
- [ ] No gradient profile circles with initials. Use a real avatar, account card, or account menu.
- [ ] No repeated KPI strips. If the same metric block appears on multiple pages, keep it only where it answers the page's main question.
- [ ] No dead cards. Delete any card that does not inform, navigate, compare, configure, or trigger an action.
- [ ] No button clutter. Collapse secondary repeated row/card actions into an overflow menu.
- [ ] No decorative feature icon grid on product landing pages. Show product UI, screenshots, data views, or concrete workflow visuals.
- [ ] No one-note palette. Scan CSS colors; if the page reads as one hue family with random tints, rebalance it.
- [ ] No nested card stacks. Use sections, rows, tabs, tables, split layouts, or modals instead.
- [ ] No hero-scale typography inside dashboards, sidebars, cards, modals, or compact tools.

## App Shell

- [ ] Sidebar navigation is left-aligned, compact, and task-based.
- [ ] Sidebar does not contain dashboard metrics, random counters, or links that belong inside a page.
- [ ] Account controls live as an account card/menu, preferably near the bottom of the sidebar or top-right app chrome.
- [ ] Settings, billing, usage, account, and team admin are grouped instead of scattered.
- [ ] Active navigation state is obvious without shouting.
- [ ] Spacing is tightened before adding more containers.
- [ ] The app shell supports more pages later without becoming a junk drawer.

## Cards, Rows, And Lists

- [ ] A card has one purpose. If it has three unrelated jobs, split or redesign it.
- [ ] Primary row data is placed for scanning: name/title left, important number/status right, secondary metadata between.
- [ ] Dates are not given visual priority unless recency is the main decision.
- [ ] Repeated actions use a three-dot menu unless one action is dominant.
- [ ] Chips collapse to icons only when the icon is recognizable and faster to scan.
- [ ] Icons add metadata or state. They are not confetti.
- [ ] KPI cards include trend, comparison, limit, or next action. A naked number is usually weak.
- [ ] Use microcharts for trends instead of colored icon boxes.

## Creation Flows

- [ ] Use a modal or focused panel when a flyout wastes space or cannot fit the real form.
- [ ] Keep required fields visible and advanced options collapsed by default.
- [ ] Include fields real users expect for the object being created.
- [ ] For URL/link tools, check for destination URL, slug, custom domain, title/card preview, description, tags, expiration, password/access control, UTM, and advanced options.
- [ ] Domain switching and object type switching are first-class controls, not hidden afterthoughts.
- [ ] The primary action is singular and obvious.
- [ ] Success, error, loading, disabled, and empty states exist.
- [ ] The flow can accept future fields without becoming cramped.

## Dashboard

- [ ] The dashboard answers "what changed and what needs attention?"
- [ ] Dashboard metrics are not copied onto custom domains, teams, settings, or billing pages.
- [ ] Use color through charts, statuses, deltas, and thresholds instead of decorative buttons.
- [ ] Show fewer, better KPIs with trend/context.
- [ ] Add microcharts only where trend matters.
- [ ] If a metric has no likely user action, remove it or move it to analytics.

## Analytics

- [ ] Analytics gets its own screen when users need comparison, segmentation, geography, timelines, attribution, or per-item breakdowns.
- [ ] Remove duplicate KPI strips from the top if the chart/table below already explains the data.
- [ ] Put actions near the data they affect: export, copy, filter, date range, split/compare, and item selection.
- [ ] Add aggregate vs individual toggles when users compare links, campaigns, projects, or resources.
- [ ] Replace generic bar charts when richer structure is obvious: map plus ranked list, trend plus breakdown, table plus sparkline.
- [ ] Use icon/color metadata in rows only when it helps identify source, region, device, campaign, or status.
- [ ] Empty analytics explains what must happen before data appears.

## Billing, Usage, And Pricing

- [ ] Billing and usage are tabbed or clearly separated when they contain plan, invoices, limits, payment method, and usage.
- [ ] Delete any billing card that does not perform a billing task.
- [ ] Usage uses charts/progress that explain consumption against limits.
- [ ] Pricing has three or four plans unless there is a real business reason for more.
- [ ] Plan hierarchy is price first, value second, name third.
- [ ] Discounts are explicit and not hidden in confusing plan order.
- [ ] The current plan shows what the next plan unlocks.
- [ ] Enterprise is named and shaped like enterprise when limits imply enterprise use.
- [ ] Billing email, payment method, invoice access, plan status, and upgrade/downgrade paths are visible where relevant.
- [ ] Decorative plan badges, icons, and filler bullets are removed.

## Landing Pages

- [ ] First viewport shows the product, not just copy and abstract shapes.
- [ ] Hero visual is a real or convincing product state: dashboard screenshot, analytics view, link/card stack, protected flow, pricing state, or workflow preview.
- [ ] Generic feature icons are replaced with concrete product visuals.
- [ ] The hero establishes trust through product clarity, not visual noise.
- [ ] Supporting sections prove the workflow with UI states, outcomes, screenshots, metrics, integrations, or social proof.
- [ ] Presentation is polished before adding sections. Landing pages convert through clarity and trust, not length.
- [ ] Mobile hero still reveals the product and does not bury the actual UI below vague marketing copy.

## Visual Quality

- [ ] Hierarchy passes the squint test: the most important thing still wins when details blur.
- [ ] Text fits every button, chip, card, sidebar item, and mobile container.
- [ ] Radius, shadows, borders, spacing, and typography are consistent with the existing system.
- [ ] Dense SaaS/product UI stays quiet and operational. Do not make dashboards feel like marketing pages.
- [ ] Color contrast works for text, icons, controls, charts, and disabled states.
- [ ] Charts have labels, units, empty states, and hover/legend behavior when relevant.
- [ ] Icons share stroke weight, size, and optical alignment.
- [ ] Loading, empty, error, and success states look designed, not bolted on.

## Final Output Gate

- [ ] Say what changed in concrete product terms, not "made it cleaner."
- [ ] Mention any remaining slop only if it still exists.
- [ ] Do not claim the UI is polished until rendered screenshots were checked.
- [ ] If the user asked for implementation, leave the code changed, not just reviewed.
