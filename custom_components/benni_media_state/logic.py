"""HA-freie Ableitungs-Engine für benni_media_state (L1 Context-Feeder).

Strikt HA-frei und voll testbar (keine homeassistant-Imports, keine relativen
Imports). Leitet aus Roh-Quellen einen Media-Context ab — entscheidet NICHTS.

Step-1-Scaffold: nur Signatur-Form + stabile Defaults. Der echte Body wird in
Step 2 aus bennis_toolbox/custom_components/bennis_toolbox/modules/
benni_media_context/logic.py extrahiert.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DEFAULT_CONTEXT = "idle"


@dataclass(frozen=True)
class Inputs:
    """Snapshot der Roh-Quellen für eine Ableitung. None = unknown.

    Vorläufig — das Feld-Set wird in Step 2/3 an benni_media_context angeglichen.
    """

    media_players: tuple[str, ...] = ()                 # beobachtete entity_ids
    player_states: dict[str, str] = field(default_factory=dict)
    title_classifier: str | None = None
    headset: str | None = None
    # TODO(step2): um die echten Roh-Inputs aus benni_media_context erweitern


@dataclass
class MediaState:
    """Abgeleiteter Media-Context. Spiegelt das Entity-Roster (vorläufig)."""

    context: str = DEFAULT_CONTEXT
    subcontext: str | None = None
    device: str | None = None
    gaming_source: str | None = None
    gaming_platform: str | None = None
    headset_active: bool = False
    entertainment_active: bool = False
    active_reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "context": self.context,
            "subcontext": self.subcontext,
            "device": self.device,
            "gaming_source": self.gaming_source,
            "gaming_platform": self.gaming_platform,
            "headset_active": self.headset_active,
            "entertainment_active": self.entertainment_active,
            "active_reasons": list(self.active_reasons),
        }


def decide(inputs: Inputs) -> MediaState:
    """Leitet den Media-Context aus den Roh-Quellen ab. Entscheidet keine Aktion.

    Step 1: liefert stabile Defaults, damit der Feeder lädt und Panel/Entities
    eine Payload haben. Noch kein Verhalten.
    """
    # TODO(step2): decide()-Body aus benni_media_context/logic.py extrahieren
    # TODO(step3-lastenheft): B2 — gaming nur bei classifier-Enum >= 1 (Gate in detect_gaming)
    # TODO(step3-lastenheft): Quiet/Private-Schichtgrenze (Detection bleibt ggf. in media_state)
    return MediaState()
