# Containment comparison

Compared exact upstream production source at `6a5f15a` with a snapshot of the current working production source, using the reviewer containment probe plus isolated generic stroke and large/rotated direct cases. Both copies use the workspace Cargo.lock and identical dependencies. All six offline, locked probe runs passed.

The only upstream instrumentation is inside `cfg(test)`: the image-update failure knob and the probe module. Current production source was not edited. The command stream, vertex buffer, complete atlas entries, atlas allocator state, target, and state-stack depth are compared.

For Swash generic-only scenarios, every present `uses_subpixel_positioning` value was checked to be false before removing that new private field from the Debug text. No other fields or differences were normalized. Non-Swash traces receive no normalization.

default: 28/30 checked scenarios identical; restore exceptions: 8, 8b.
default-swash: 10/10 checked scenarios identical; restore exceptions: none.
swash-only: 9/9 checked scenarios identical; restore exceptions: none.

Unexpected checked differences: none.
Workspace source files changed after snapshot: none.
Workspace source files added after snapshot: none.

The two non-Swash exceptions both still return `FontSizeTooLargeForAtlas`. Their atlas state and vertices are unchanged. The differences are the restored target (screen in scenario 8, original image in scenario 8b) and the corresponding SetRenderTarget command before the subsequent rectangle draw. The saved diffs contain no other changes.

Per-scenario SHA-256 hashes and classifications are in comparison.json. Full traces, test logs, exact commands, and unified diffs are retained alongside this report. Native Swash fill scenarios are recorded but excluded from the generic-only equality verdict because the authorized outline positioning/cache behavior changes there.
