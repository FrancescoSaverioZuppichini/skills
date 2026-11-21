---
name: unslop
description: Review and clean code against strict simplicity rules — short verb+noun names, simple DB queries inline, one data type from the ORM or schema, config as one schema with defaults, small pure single-job functions and files, no wrappers, utils dumps or Java-style layers, speed by design, tests on the real code. Use for EVERY code review, before calling any change done, and whenever asked to audit, refactor, simplify or "unslop" code.
---

# Unslop

Code is written to be read and audited by a person: plain names, short functions, the data as it is
stored, nothing clever. This skill is the review that keeps it that way. It works in any project; the
project's AGENTS.md / README says which checks to run.

The shape to aim for is a file like this one. Its options are one schema with defaults at the top, then
small pure functions with one job each, in the order they're called, then a single export:

```ts
export const searchOptionsSchema = z.object({
	limit: z.number().int().min(1).max(100).default(5),
	lexicalThreshold: z.number().min(0).max(1).default(0.7),
})
export type SearchOptions = z.input<typeof searchOptionsSchema>

function tokenize(input: string) { … }
function lexicalScore(queryWords: Set<string>, text: string) { … }
function lexicalSearch<T>(queryWords: Set<string>, items: SearchItem<T>[]) { … }

export async function search<T>(query: string, items: SearchItem<T>[], options: SearchOptions = {}) {
	const parsed = searchOptionsSchema.parse(options)
	…
}
```

## How to run a review

If the project has a shape doc (for example `.agents/docs/shape.md`), review against its checklist too; where
it is more specific than this skill (e.g. modules as namespaces), it wins.

1. Read every file in scope completely. Never review from excerpts or a diff alone.
2. Walk the rules below file by file. Write each finding as one line:
   `path:line: rule broken. The fix.`
3. Fix them. Run the project's checks (lint, typecheck, tests) and anything its AGENTS.md lists.
4. Report the lines of code before and after for the files in scope, against a budget set before you
   start. Bloat is the main finding: comment walls, wrappers, retyped data, duplicated helpers, hand-kept
   form state, ports of UI kits copied whole. A module that doesn't shrink isn't done; redo it.

## 1. Names: verb + noun, short, the same words everywhere

- Functions are `verb` or `verbNoun`; two words is normal and three is the limit. The noun is the
  data: `createTag`, `listEntries`, `search`, `tokenize`, `reflow`.
- Data operations (queries, actions, jobs, routes, logs) use one small set of verbs, and never a
  synonym (`fetch`, `modify`, `run`, `insert`, `emit`, `queue`, `rescan`, `forget`):

  | Verb | Use |
  |---|---|
  | `get` | one thing by id or key, or a derived value |
  | `list` | many, paginated or not |
  | `create` | a new row or resource |
  | `update` | change fields of an existing one |
  | `remove` | delete, disconnect, take away; the default destructive verb |
  | `delete` | only a hard delete where the product already says "delete" |
  | `set` | replace one relation or value |
  | `toggle` | flip a two-state switch |
  | `sync` | pull from an outside source and reconcile |
  | `scan` | search sources for candidates |
  | `process` | run a multi-step pipeline over existing data |
  | `send` | deliver a message, notification, or push |
  | `refresh` | renew an expiring token or cache |
  | `trigger` | start a job without waiting for it |
  | `test` | check that a connection or path works |

  The client keeps `load` (fetch into its state) and `save` (write out). Engines, UI, the disk and workers use
  the plain domain verb for what they do (`draw`, `pack`, `reflow`, `layout.place`, `select`, `zoom`,
  `move`, `rename`, `disk.trash`, `disk.stat`, `images.read`, `run`, `watch`), and so does a read
  named for the user's action (`folders.open`), never a synonym of a verb above. `is` / `has` start booleans.
- Log and event names are `{domain}.{verb}.{status}` with the same verbs, or the plain domain verb of
  the operation that failed or ran (`layout.undo.failed`: the undo of a disk call;
  `library.watch.failed`): `node.update.failed`, `folder.scan.completed`, never `preview.failed` or
  `upload.write.failed`.
- The file is the context. Inside `lib/disk.ts` a function is `move`, not `moveFileOnDisk`. A domain
  module exports one namespace and call sites read `module.verb()`; what stays a bare export
  (actions, routes, components, the engine, a function named as its file, the runner `run`, a
  worker's `index.ts`) still reads right bare.
- Components are the noun of what they show (`Inspector`, `Toolbar`, `TreeRow`). Files are plain nouns
  for one job (`search.ts`, `canvas.ts`, `images.ts`).
- Generic layers speak generic words. An engine (geometry, layout, hit testing, a renderer's loop)
  knows only its own concepts, e.g. *node* and *group* (a node that holds nodes, open or collapsed).
  It never names a domain kind: `getFolderSize` in geometry is `getGroupSize`, `isOpenFolder` in
  layout is `isOpen`, and `FRAME_HEADER` is `GROUP.header`. The domain → engine mapping lives in one
  place (`isGroup(node)`).
- When a client function and a server action would share a name, the action keeps the data verb
  (`createFolder`). The client function is named for what the user did (`newFolder`). Never bolt on a
  preposition to dodge the clash.

| Slop (real names from past reviews) | Why it is slop | Correct |
|---|---|---|
| `placeBatch(store, count, at)` | says nothing; it only sized squares and called `packAround` | inline `packAround(squares, at)` at the call sites |
| `createFolderIn`, `renameNodeTo` | a preposition to dodge a name clash | `newFolder`, `rename` (client) vs `createFolder`, `renameNode` (server) |
| `moveNodesToFolder` | narrates the arguments | `moveNodes` |
| `createCanvasRenderer`, `attachCanvasGestures` in `canvas/` | repeats the module name | `createRenderer`, `attachInput` |
| `moveFileOnDisk` in `lib/disk.ts` | repeats the module | `disk.move` |
| `drainThumbnailQueue`, `generateThumbnail`, `writeThumbnailSizes`, `renderImageThumbnails` | four names for one job | `work`, `images.read`, `videos.read` |
| `insertEntryNode`, `getThumbState`, `isInSync` | noise words (Entry, State, In) | the INSERT inline, `media.getThumb`, `diff` |
| `getCanvasItems`, `isNodeDimmed`, `getSelectionSet` | prefix noise | `layout`, `isDimmed`, `isSelected` |
| `FileTreeHoverHighlight`, `useHighlightTarget` | narrates | `Highlight`, `useHighlight` |
| `settleFolders`, `refreshFolder`, `emitNodes`, `queueFiles`, `rescanLibrary`, `saveNodes` (server) | coined words or synonyms; the name hides the operation | `layout.update`, `scan`, the publish in `layout.update`, the row set `pending`, `scanLibrary`, `updateNodes` |

## 2. Database: simple queries inline, functions only for hard ones

- A simple query is written where it's used, even if it appears 2–3 times:
  `const [folder] = await db.select().from(nodes).where(eq(nodes.id, folderId))`.
- A function in the data layer is only for a query that's hard to get right: recursive CTEs, locked
  transactions, upserts, multi-step reads.
- No one-liner wrappers: `getRow`, `listRows`, `updateNode`, `selectNodes()`, `getNames(id)`,
  `listUILibraries()`.
- In frameworks with server actions, every export of a `"use server"` file is a public endpoint. Export
  actions only; a background job exported from there can be called by anyone.

```ts
// SLOP: the reader has to jump to a wrapper around one select
async function getNames(folderId: string) {
	const children = await db.select({ name: nodes.name }).from(nodes).where(eq(nodes.parentId, folderId))
	return new Set(children.map((child) => child.name))
}
// CORRECT: the query where it's needed
const siblings = await db.select({ name: nodes.name }).from(nodes).where(eq(nodes.parentId, parent.id))
```

## 3. One data type, straight from the ORM or the schema

- A row is the ORM's inferred type (`typeof table.$inferSelect`). Input and config are
  `z.infer<typeof schema>`. At a boundary, use `Pick<>` / `Omit<>` of those.
- Banned:
  - hand-written shapes that retype a row: `NodeUI`, `FileNode`, `FolderData`, `UILibrary`;
  - converters that only reshape: `toNode(row)`, `toUILibrary(row)`;
  - parallel structures that mirror the data: a `stacks` map next to `nodes`.
- No state massage. The client shows the row as stored. A derived value the UI needs is stored on
  the row, or computed by one pure function where it's drawn. If the UI needs a different shape, the
  data model is wrong: fix the model, don't map the rows.

## 4. Config is one schema with defaults

The schema holds each value's limits and default. The type is `z.infer`, the defaults are
`schema.parse({})`, and a settings form is `useForm` with `zodResolver(schema)` on the same schema. Labels
live on the fields with `.meta({ label, hint })`.

```ts
// SLOP: a table, a helper that builds a schema from it, a key list, a defaults object, loose constants
export const CANVAS_SETTINGS = { renderDistance: { label, min, max, default: 1, format }, … }
const setting = ({ min, max, default: fallback }) => z.number().transform(…).catch(fallback)
export const CANVAS_SETTING_KEYS = Object.keys(CANVAS_SETTINGS)
export const RENDER_MARGIN = 1
// CORRECT
export const renderSettingsSchema = z.object({
	margin: z.number().min(0).max(4).default(1).meta({ label: "Render distance", hint: "Screens past each edge" }),
})
export type RenderSettings = z.infer<typeof renderSettingsSchema>
```

Internal tuning numbers (batch sizes, how many run at once) are one named constant next to the code
that uses them. Anything a person would want to change is config. Fixed design numbers are grouped
into a dict per job (`GRID = { cell, gap }`), not scattered as loose constants.

## 5. Small pure functions, one job each, no wrappers

- Write a function when it has a job you can name. Never write one that only forwards, renames or
  bundles two calls. Banned:
  - a function that wraps another in a transaction and nothing else;
  - `close()` that only calls `onClose()`;
  - `zoomReset()` that only calls `zoomBy()`;
  - `queuePendingThumbnails(nodes)` that only filters and forwards.
- No classes, services, managers, registries, proxies, or "write-through layers" over an API you
  already have.
- Pure where possible: input → output. Only the state owner (the store) changes state.
- No `utils` dumps. `utils.ts` holds the framework's helper (`cn`) only. Use the standard libraries
  (date-fns for dates and durations). A helper lives in the file that uses it until a second file
  needs it.
- No duplicates: one icon map, one menu item, one constant. Three copies of `KIND_ICONS` is a
  finding.

## 6. Files: one job, readable top to bottom

- A file reads like the shape at the top: config and types, then small functions in call order, then
  the export.
- A file doing several jobs gets split into a folder of plain-named single-job files. Real cases:
  - a data file doing reads + sync + placement + layout became `folders.ts`, `layout.ts` and the
    scans worker (`workers/scans/scan.ts`);
  - a store mixing camera glides, search reads and uploads with its edits became `store/camera.ts`,
    `store/search.ts` and `store/uploads.ts`, each the one owner of its private state, beside the one
    store in `store/index.ts`.
- An action reads top to bottom as what happens:

```ts
export async function createFolder(parentId: string, name: string): Promise<ActionResponse<Node>> {
	try {
		const id = crypto.randomUUID()
		await layout.update((tx) => folders.create(tx, parentId, { id, name }))
		const [folder] = await db.select().from(nodes).where(eq(nodes.id, id))
		return { data: folder, error: null }
	} catch (error) {
		return fail(error, "folder.create.failed")
	}
}
```

## 7. React: small components, derived state, no hand-kept forms

- One component, one job, and a file is a small number of them. Length is not the measure: split a
  component when it shows two separate things, each with its own state, never to make it shorter.
  Render logic stays in the component that renders it; moving a few lines into `lib/` or the store
  only so the file is smaller (or so a test can import them) is the slop this skill removes.
- Derive, don't sync. A value computable from props or the store is computed in render. Never copy it
  into state, never sync it with an effect, never `setState` during render to catch up.
- Effects only sync with the outside world (subscriptions, listeners, timers, the DOM). Data comes from
  the server or the store, not from an effect that fetches into local state.
- Forms are `useForm` with `zodResolver` on the input schema. No `useState` per field, no hand-written
  validation, no `buildInput()` that re-parses what the form already has.
- Read shared state with selectors (`useStore((state) => state.x)`). Don't drill props or copy the
  store into context.
- No `useCallback` / `useMemo` / `React.memo` unless a measured problem needs it.
- Don't port a UI kit wholesale (animated highlights, measuring refs, private contexts) when CSS or the
  design system's component does it. Use shadcn components as they are.
- Shared pieces live once: an icon map or a menu item written in 3 files is a finding.

## 8. Comments say why and how, briefly

One plain-English comment above a tricky part: why it's done this way, and how the trick works. Use
the project's comment prefix if it has one. No narration of obvious lines, no parameter essays, no
comment walls over simple code.

## 9. Speed is designed in, not hoped for

- **Graphics:** the work per frame scales with what's on screen, not with the data. This is level of
  detail:
  - a tile a few pixels wide is one flat rect in its colour, with no texture and no request;
  - a tiny group is one rect, and its children aren't walked or loaded;
  - cull whole subtrees off screen;
  - batch flat shapes into one draw call.
- **Data:** read what is shown, one level at a time. Batch reads and merges. No N+1, no O(n²), no
  whole-tree work for one node. In Next.js, reads are GET routes, since server actions run one at a time
  per client.
- Measure before saying it's fast: request count, payload, query plans (`EXPLAIN ANALYZE`), frame time.

## 10. Tests drive the real code on real data

- Tests run the app's own code (store, actions, route handlers) against a copy of real data. No
  made-up fixtures that only prove the maths.
- Call the real handlers. Never build a shim that re-implements the code under test, such as a fetch
  mock that copies a route's query.
- Import a check as a function. Don't spawn a script and compare its stdout.
- Prove each test by breaking the code it guards once; a test that never failed proves nothing.
- One test file per job, with shared setup in one file. Drop tests that repeat another.
