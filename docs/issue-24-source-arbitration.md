# Source arbitration — issue #24

The 2026-09-07 consolidated issue supersedes the unconditional paused/idle
streaming rule in the issue-21 note. Media State owns the downstream context,
device and subcontext. No Policy/Apply source arbitration is added.

- Apple TV playing bypasses TV-only startup. A recognized current LG input
  identifies the foreground; PlayStation 5 can win before its native player
  has reported on. No device service is called by State.
- Paused/idle can retain an existing stream only with Apple OTT foreground
  and confirmed TV power. A candidate alone is not confirmed TV power.
- On explicit source loss with TV still active, the last recognized source
  is retained for exactly 5 seconds from the loss event. A new recognized
  source replaces it immediately; TV off cancels it. Expiry has its own
  callback, even if no more source events arrive. Invalid unrecognized
  inputs do not receive grace. An available unchanged input is read as current
  HA evidence; no new time-to-live for unchanged attributes is introduced.
- The 20-second TV-only startup and 50-W fallback remain separate. A deadline
  callback now also completes startup without depending on another event.
- Authoritative inputs and explicit TV off use the configured short debounce
  without subsequent event rearming (default 2 seconds).
- PS5 enum 3 consumes the preemptible-grind meaning specified in
  Title_classifier#83 and keeps the existing downstream `gaming_grind` audio
  contract. No classifier catalog, title-specific rule or classifier release
  is part of this change.

`source_arbitration` on the existing context sensor contains selected source,
foreground, last valid foreground, grace active/elapsed/remaining/expired,
reason, degraded and overlap conflict. Timer diagnostics are snapshots at
computation time; expiry is published automatically.

Bindings continue to resolve options, then data, then profile prefill. The
existing LAN prefill is not a migration and does not override a saved native
binding. No change is based on the superseded frozen-player claim in #15.

Tests cover the pure decisions and actual coordinator callbacks with fake HA
states and a deterministic clock. Production bindings and acoustic behavior
remain Benni's Live gate. No HA reload, installation or device action occurs.
