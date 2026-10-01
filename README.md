# node_load_markers

A single `prestartup_script.py` that wraps ComfyUI's custom node loader
(`nodes.load_custom_node`) so the console clearly shows which node is
currently loading — including a START/END marker around each node and
a `[node_name]` tag on every line printed while that node loads. This
makes it much easier to spot which custom node is slow, noisy, or
crashing on startup.

> The code in this package was written by Claude (Anthropic).

## Why

By default, ComfyUI's startup log interleaves output from dozens of
custom nodes with no clear boundaries, so a crash or a slow import is
hard to attribute to a specific node. This script solves that without
touching any of your existing custom node folders or their git repos.

## Installation

1. Copy this whole folder, unchanged, into your ComfyUI `custom_nodes`
   directory:

   ```
   ComfyUI/custom_nodes/node_load_markers/
   ├── __init__.py
   └── prestartup_script.py
   ```

   or clone this in `custom_nodes` directory:

   ```
   git clone https://github.com/mykeehu/node_load_markers
   ```

3. Restart ComfyUI.

That's it — no further configuration. ComfyUI automatically runs every
`prestartup_script.py` it finds in a direct subfolder of `custom_nodes`
*before* it starts loading the actual custom nodes, which is what lets
this script patch the loader in time.

The `__init__.py` is required too: ComfyUI also tries to import every
subfolder of `custom_nodes` as a regular node package, and without an
`__init__.py` that import fails with a `FileNotFoundError`. The one
included here is intentionally empty (no `NODE_CLASS_MAPPINGS`) — it
only exists to prevent that error.

## What it does

Every custom node's loading is wrapped like this:

```
===== START: some_custom_node =====
[some_custom_node] ... anything that node itself prints ...
===== END: some_custom_node [OK, 0.42s] =====
```

On failure:

```
===== START: broken_node =====
[broken_node] ...
===== END: broken_node [EXCEPTION: <error message>, 0.10s] =====
```

Two refinements are built in:

- **Line tagging.** While a node is loading, its stdout/stderr output
  is wrapped so every line gets a `[node_name]` prefix. This keeps
  output attributed correctly even if the node's own logging is
  buffered or slightly delayed relative to a plain `print()`.
- **Deferred END marker.** The END line for a node is not printed
  immediately — it's held back until either the *next* node's START
  is about to print, or ComfyUI is shutting down (via `atexit`). This
  keeps any trailing output that lands slightly after a node's own
  import call returns (e.g. from a background thread doing lazy
  initialization) visually inside that node's block instead of
  appearing to belong to the next one.

## Known limitation

Because the END marker is deferred until the next node's START, the
very last node loaded in a session will not show its END line during
normal operation — it only gets flushed at process exit (which you
typically won't see in the live console). This is a cosmetic
trade-off, not a bug: everything up to the second-to-last node is
fully bracketed.

## Notes

- This does not modify any other custom node's files or git repo —
  they remain fully updatable via git/ComfyUI-Manager as normal.
- If a future ComfyUI version changes the signature of
  `nodes.load_custom_node`, only this one file needs adjusting.
