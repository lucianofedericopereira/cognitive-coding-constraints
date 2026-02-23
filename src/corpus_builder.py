# -----------------------------------------------------------------------------
# Author:  Luciano Federico Pereira
# ORCID:   https://orcid.org/0009-0002-4591-6568
# Paper:   Empirical Validation of Cognitive-Derived Coding Constraints and
#          Tokenization Asymmetries in LLM-Assisted Software Engineering
# Repo:    https://github.com/lucianofedericopereira/cognitive-coding-constraints
# License: LGPL-2.1
# -----------------------------------------------------------------------------

"""
corpus_builder.py — Experiment 1: corpus construction.

Loads the 40-identifier seed set from data/seed_identifiers.csv,
generates four notation variants for each semantic form, and writes
the 200-identifier extended corpus to data/extended_corpus.csv.

The 160 additional identifiers (beyond the 40 seeds) are sourced from
manually curated enterprise event catalogs representative of AWS
EventBridge, Kafka, and Laravel conventions; they are embedded here
as a static list so the corpus is fully reproducible without network
access.
"""

import re
import pandas as pd
from utils import SEED_CSV, CORPUS_CSV, get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Extended identifiers (160 items across 7 domains)
# ---------------------------------------------------------------------------
EXTENDED_IDENTIFIERS = [
    # order_management (20)
    ("order payment pending", "order_management"),
    ("order payment confirmed", "order_management"),
    ("order fulfillment started", "order_management"),
    ("order fulfillment completed", "order_management"),
    ("order return requested", "order_management"),
    ("order return approved", "order_management"),
    ("order return rejected", "order_management"),
    ("order discount applied", "order_management"),
    ("order tax calculated", "order_management"),
    ("order address updated", "order_management"),
    ("order priority escalated", "order_management"),
    ("order split requested", "order_management"),
    ("order merged", "order_management"),
    ("order archived", "order_management"),
    ("order review submitted", "order_management"),
    ("order review approved", "order_management"),
    ("order subscription created", "order_management"),
    ("order subscription cancelled", "order_management"),
    ("order backordered", "order_management"),
    ("order hold placed", "order_management"),
    ("order hold released", "order_management"),
    ("order flagged for review", "order_management"),
    ("order tax exemption applied", "order_management"),
    # payment (20 → 23)
    ("payment disputed", "payment"),
    ("payment dispute resolved", "payment"),
    ("payment authorization requested", "payment"),
    ("payment authorization declined", "payment"),
    ("payment capture succeeded", "payment"),
    ("payment capture failed", "payment"),
    ("payment void initiated", "payment"),
    ("payment void completed", "payment"),
    ("payment currency converted", "payment"),
    ("payment fraud flag raised", "payment"),
    ("payment fraud cleared", "payment"),
    ("payment plan created", "payment"),
    ("payment plan payment made", "payment"),
    ("payment plan defaulted", "payment"),
    ("payment gateway timeout", "payment"),
    ("payment gateway switched", "payment"),
    ("payment receipt generated", "payment"),
    ("payment tax withheld", "payment"),
    ("payment batch submitted", "payment"),
    ("payment batch settled", "payment"),
    ("payment link created", "payment"),
    ("payment link expired", "payment"),
    ("payment link used", "payment"),
    # inventory (20)
    ("inventory threshold breached", "inventory"),
    ("inventory snapshot taken", "inventory"),
    ("inventory transfer initiated", "inventory"),
    ("inventory transfer completed", "inventory"),
    ("inventory damage reported", "inventory"),
    ("inventory audit started", "inventory"),
    ("inventory audit completed", "inventory"),
    ("inventory location changed", "inventory"),
    ("inventory batch received", "inventory"),
    ("inventory batch rejected", "inventory"),
    ("inventory expiry alert triggered", "inventory"),
    ("inventory category updated", "inventory"),
    ("inventory supplier changed", "inventory"),
    ("inventory cost updated", "inventory"),
    ("inventory item quarantined", "inventory"),
    ("inventory item released", "inventory"),
    ("inventory cycle count started", "inventory"),
    ("inventory cycle count completed", "inventory"),
    ("inventory write off recorded", "inventory"),
    ("inventory forecast updated", "inventory"),
    ("inventory bin reassigned", "inventory"),
    ("inventory shrinkage recorded", "inventory"),
    ("inventory return processed", "inventory"),
    # user_auth (20)
    ("user email verified", "user_auth"),
    ("user two factor enabled", "user_auth"),
    ("user two factor disabled", "user_auth"),
    ("user session started", "user_auth"),
    ("user session expired", "user_auth"),
    ("user token refreshed", "user_auth"),
    ("user token revoked", "user_auth"),
    ("user profile updated", "user_auth"),
    ("user permission granted", "user_auth"),
    ("user permission revoked", "user_auth"),
    ("user account locked", "user_auth"),
    ("user account unlocked", "user_auth"),
    ("user oauth linked", "user_auth"),
    ("user oauth unlinked", "user_auth"),
    ("user deletion requested", "user_auth"),
    ("user deletion completed", "user_auth"),
    ("user consent recorded", "user_auth"),
    ("user consent withdrawn", "user_auth"),
    ("user api key created", "user_auth"),
    ("user api key revoked", "user_auth"),
    ("user avatar updated", "user_auth"),
    ("user language preference set", "user_auth"),
    ("user timezone updated", "user_auth"),
    # notification (20)
    ("notification scheduled", "notification"),
    ("notification cancelled", "notification"),
    ("notification bounced", "notification"),
    ("notification clicked", "notification"),
    ("notification unsubscribed", "notification"),
    ("notification template created", "notification"),
    ("notification template updated", "notification"),
    ("notification channel added", "notification"),
    ("notification channel removed", "notification"),
    ("notification batch queued", "notification"),
    ("notification batch dispatched", "notification"),
    ("notification rate limit reached", "notification"),
    ("notification retry attempted", "notification"),
    ("notification retry exhausted", "notification"),
    ("notification digest generated", "notification"),
    ("notification digest sent", "notification"),
    ("notification priority escalated", "notification"),
    ("notification suppressed", "notification"),
    ("notification opted in", "notification"),
    ("notification opted out", "notification"),
    ("notification webhook triggered", "notification"),
    ("notification sms delivered", "notification"),
    ("notification push delivered", "notification"),
    # shipping (20)
    ("shipment label generated", "shipping"),
    ("shipment pickup scheduled", "shipping"),
    ("shipment picked up", "shipping"),
    ("shipment in transit", "shipping"),
    ("shipment out for delivery", "shipping"),
    ("shipment delivered", "shipping"),
    ("shipment failed delivery", "shipping"),
    ("shipment rescheduled", "shipping"),
    ("shipment address corrected", "shipping"),
    ("shipment carrier changed", "shipping"),
    ("shipment weight updated", "shipping"),
    ("shipment dimensions updated", "shipping"),
    ("shipment customs cleared", "shipping"),
    ("shipment customs held", "shipping"),
    ("shipment insurance claimed", "shipping"),
    ("shipment loss reported", "shipping"),
    ("shipment return initiated", "shipping"),
    ("shipment return received", "shipping"),
    ("shipment consolidation completed", "shipping"),
    ("shipment route optimized", "shipping"),
    ("shipment signature collected", "shipping"),
    ("shipment proof of delivery uploaded", "shipping"),
    # analytics (20)
    ("analytics goal completed", "analytics"),
    ("analytics dashboard created", "analytics"),
    ("analytics dashboard deleted", "analytics"),
    ("analytics cohort defined", "analytics"),
    ("analytics cohort archived", "analytics"),
    ("analytics ab test started", "analytics"),
    ("analytics ab test completed", "analytics"),
    ("analytics anomaly detected", "analytics"),
    ("analytics alert triggered", "analytics"),
    ("analytics alert resolved", "analytics"),
    ("analytics data ingested", "analytics"),
    ("analytics pipeline failed", "analytics"),
    ("analytics model retrained", "analytics"),
    ("analytics model deployed", "analytics"),
    ("analytics retention calculated", "analytics"),
    ("analytics churn predicted", "analytics"),
    ("analytics attribution updated", "analytics"),
    ("analytics session recorded", "analytics"),
    ("analytics heatmap generated", "analytics"),
    ("analytics tag fired", "analytics"),
    ("analytics conversion recorded", "analytics"),
    ("analytics experiment assigned", "analytics"),
    ("analytics metric threshold exceeded", "analytics"),
]

# ---------------------------------------------------------------------------
# Notation converters
# ---------------------------------------------------------------------------

def to_dot(semantic: str) -> str:
    """'order created' → 'order.created'"""
    return semantic.strip().replace(" ", ".")


def to_camel(semantic: str) -> str:
    """'order created' → 'orderCreated'"""
    words = semantic.strip().split()
    return words[0] + "".join(w.capitalize() for w in words[1:])


def to_snake(semantic: str) -> str:
    """'order created' → 'order_created'"""
    return semantic.strip().replace(" ", "_")


def to_kebab(semantic: str) -> str:
    """'order created' → 'order-created'"""
    return semantic.strip().replace(" ", "-")


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_corpus() -> pd.DataFrame:
    log.info("Loading seed identifiers from %s", SEED_CSV)
    seed_df = pd.read_csv(SEED_CSV)

    extended_rows = [
        {"semantic_form": sf, "domain": domain}
        for sf, domain in EXTENDED_IDENTIFIERS
    ]
    extended_df = pd.DataFrame(extended_rows)

    combined = pd.concat([seed_df[["semantic_form", "domain"]], extended_df], ignore_index=True)
    combined["id"] = range(1, len(combined) + 1)

    combined["dot"] = combined["semantic_form"].apply(to_dot)
    combined["camelCase"] = combined["semantic_form"].apply(to_camel)
    combined["snake_case"] = combined["semantic_form"].apply(to_snake)
    combined["kebab_case"] = combined["semantic_form"].apply(to_kebab)

    combined = combined[["id", "semantic_form", "domain", "dot", "camelCase", "snake_case", "kebab_case"]]

    log.info("Corpus built: %d identifiers", len(combined))
    combined.to_csv(CORPUS_CSV, index=False)
    log.info("Written to %s", CORPUS_CSV)
    return combined


if __name__ == "__main__":
    build_corpus()