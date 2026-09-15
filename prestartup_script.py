"""
node_load_markers - prestartup_script.py

Wraps ComfyUI's custom node loader (nodes.load_custom_node) so the
console clearly shows which node is currently loading: a START/END
marker around each node, and a [node_name] tag on every line printed
while that node loads.

The END marker for a node is NOT printed immediately - it's held back
until the NEXT node's START is about to print (or the process exits).
This way, if a node writes something from a background thread shortly
after its own import call returns, that output still tends to land
visually inside the correct block instead of appearing after the
next node's START.
"""

import sys
import time
import atexit


class _TaggingStream:
    """Prefixes every line with a [node_name] tag."""

    def __init__(self, original, tag):
        self._original = original
        self._tag = tag
        self._at_line_start = True

    def write(self, s):
        if not s:
            return
        out = []
        for ch in s:
            if self._at_line_start and ch != "\n":
                out.append(f"[{self._tag}] ")
                self._at_line_start = False
            out.append(ch)
            if ch == "\n":
                self._at_line_start = True
        self._original.write("".join(out))

    def flush(self):
        self._original.flush()

    def __getattr__(self, item):
        return getattr(self._original, item)


try:
    import nodes

    if not getattr(nodes, "_node_load_markers_patched", False):
        _original_load_custom_node = nodes.load_custom_node
        _pending_end = {"line": None}

        def _flush_pending_end():
            if _pending_end["line"] is not None:
                print(_pending_end["line"])
                sys.stdout.flush()
                _pending_end["line"] = None

        atexit.register(_flush_pending_end)

        def _patched_load_custom_node(module_path, *args, **kwargs):
            name = getattr(module_path, "name", str(module_path))
            tag = name.rstrip("\\/").split("\\")[-1].split("/")[-1]

            # flush the previous node's pending END line before this
            # node starts writing to the console
            _flush_pending_end()

            print(f"\n===== START: {name} =====")
            sys.stdout.flush()
            sys.stderr.flush()

            old_stdout, old_stderr = sys.stdout, sys.stderr
            sys.stdout = _TaggingStream(old_stdout, tag)
            sys.stderr = _TaggingStream(old_stderr, tag)

            start = time.time()
            try:
                result = _original_load_custom_node(module_path, *args, **kwargs)
                elapsed = time.time() - start
                status = "OK" if result is not False else "FAILED (returned False)"
                sys.stdout, sys.stderr = old_stdout, old_stderr
                _pending_end["line"] = f"===== END: {name} [{status}, {elapsed:.2f}s] =====\n"
                return result
            except Exception as e:
                elapsed = time.time() - start
                sys.stdout, sys.stderr = old_stdout, old_stderr
                _pending_end["line"] = f"===== END: {name} [EXCEPTION: {e}, {elapsed:.2f}s] =====\n"
                raise
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr

        nodes.load_custom_node = _patched_load_custom_node
        nodes._node_load_markers_patched = True
        print("[node_load_markers] load_custom_node patched - line tagging + deferred end markers active")
    else:
        print("[node_load_markers] already patched, skipping")

except Exception as e:
    print(f"[node_load_markers] could not patch nodes.load_custom_node: {e}")
