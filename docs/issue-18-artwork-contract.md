# Artwork proxy candidate — benni_media#18

Owner: https://github.com/Levtos/benni_media/issues/18 (`agent:codex`).

Read-only HA snapshots on 2026-09-07 show Apple-Music artwork as a private HTTP MA-imageproxy URL, whereas working radio artwork is HTTPS. Both supply HA's relative `entity_picture_local` media-player proxy; neither supplies `media_image_url` as a state attribute. No `image://` artwork was observed. Addresses, IDs and query values are deliberately omitted.

The former candidate contract omitted the already resolved local HA proxy. This patch adds it after existing player candidates and before classifier artwork, retaining all prior ordering and deduplication. No invented proxy, resolver, credentials, source arbitration or service call. HA owns the image transport/authentication; the browser tries candidates in order.

Primary contract: https://github.com/home-assistant/core/blob/2026.9.1/homeassistant/components/media_player/__init__.py (`media_image_local`, `MediaPlayerImageView`; picture attributes are explicitly unrecorded).

Regression coverage: observed Apple-Music format and local proxy; observed radio HTTPS order; existing MA priority/deduplication; no-artwork input. Full suite: 156 tests. Ruff E/F/B excluding E501, compileall and diff check pass. Pre-existing full-Ruff findings are outside scope. Runtime image URLs must not be copied into logs or diagnostic exports.

Companion cockpit release v0.7.6 handles unknown schemes, fallback and safe load diagnostics. Install State v0.14.5 plus the cockpit release for Benni's live artwork/radio/track-change acceptance. Exact prior browser-network failure is not observed; no Live claim or HA operation by the agent.
