"""Pure post-processing policies; no LLM calls are made here."""


POLICIES = ("converted_then_original", "three_tier")


def rerank(candidate, clicked, converted, top_k, policy):
    ids, scores = candidate["item_ids"], candidate["scores"]
    clicked, converted = set(clicked), set(converted)
    if not converted <= clicked <= set(ids):
        raise ValueError("Behavior sets violate candidate/click/conversion nesting")
    if policy not in POLICIES:
        raise ValueError(f"Unknown policy: {policy}")
    def tier(item):
        if item in converted:
            return 0
        if policy == "three_tier" and item in clicked:
            return 1
        return 2 if policy == "three_tier" else 1
    order = sorted(range(len(ids)), key=lambda index: (tier(ids[index]), -scores[index], index))
    return [ids[index] for index in order[:top_k]]


def all_rankings(candidate, actions, top_k):
    ids = candidate["item_ids"]
    clicked, converted = actions["clicked_item_ids"], actions["converted_item_ids"]
    clicked_set = set(clicked)
    click_order = sorted(range(len(ids)), key=lambda index: (
        0 if ids[index] in clicked_set else 1, -candidate["scores"][index], index))
    return {"sampled_baseline": ids[:top_k],
            "click_only": [ids[index] for index in click_order[:top_k]],
            "converted_then_original": rerank(candidate, clicked, converted, top_k,
                                                "converted_then_original"),
            "three_tier": rerank(candidate, clicked, converted, top_k, "three_tier")}
