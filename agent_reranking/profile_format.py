"""Render stored profile evidence into the established natural-language protocol."""


AGE_LABELS = {
    "1": "Under 18", "18": "18-24", "25": "25-34", "35": "35-44",
    "45": "45-49", "50": "50-55", "56": "56+",
}
GENDER_LABELS = {"F": "female", "M": "male"}
OCCUPATION_LABELS = {
    "0": "other or not specified", "1": "academic/educator", "2": "artist",
    "3": "clerical/admin", "4": "college/grad student", "5": "customer service",
    "6": "doctor/health care", "7": "executive/managerial", "8": "farmer",
    "9": "homemaker", "10": "K-12 student", "11": "lawyer", "12": "programmer",
    "13": "retired", "14": "sales/marketing", "15": "scientist",
    "16": "self-employed", "17": "technician/engineer",
    "18": "tradesman/craftsman", "19": "unemployed", "20": "writer",
}

TRAIT_LABELS = {
    "activity": {1: "infrequent viewer", 2: "occasional viewer", 3: "movie enthusiast"},
    "conformity": {1: "dedicated follower", 2: "balanced evaluator", 3: "independent critic"},
    "diversity": {1: "selective viewer", 2: "niche explorer", 3: "broad explorer"},
}
TRAIT_DESCRIPTIONS = {
    "activity": {
        1: "low movie-interaction frequency", 2: "moderate movie-interaction frequency",
        3: "high movie-interaction frequency"},
    "conformity": {
        1: "ratings usually stay close to average item ratings",
        2: "ratings show a moderate departure from average item ratings",
        3: "ratings often depart from average item ratings"},
    "diversity": {
        1: "genre choices are concentrated", 2: "genre choices show moderate breadth",
        3: "genre choices span a broad range"},
}


def natural_demographics(value):
    """Map ML-1M codes while leaving already rendered labels unchanged."""
    result = dict(value)
    result["age"] = AGE_LABELS.get(str(value.get("age", "")), value.get("age", "unknown"))
    result["gender"] = GENDER_LABELS.get(
        str(value.get("gender", "")), value.get("gender", "unknown"))
    result["occupation"] = OCCUPATION_LABELS.get(
        str(value.get("occupation", "")), value.get("occupation", "unknown"))
    return result


def labeled_social_traits(traits):
    """Attach the exact pre-migration Agent4Rec-inspired labels to stored levels."""
    result = {}
    for name in ("activity", "conformity", "diversity"):
        row = dict(traits[name])
        level = int(row["level"])
        row["label"] = TRAIT_LABELS[name][level]
        result[name] = row
    return result


def social_trait_summary(traits):
    if isinstance(traits, str):
        return traits
    rendered = labeled_social_traits(traits)
    return ("Social traits: "
            f"activity is {rendered['activity']['label']} "
            f"({TRAIT_DESCRIPTIONS['activity'][rendered['activity']['level']]}); "
            f"conformity is {rendered['conformity']['label']} "
            f"({TRAIT_DESCRIPTIONS['conformity'][rendered['conformity']['level']]}); "
            f"diversity is {rendered['diversity']['label']} "
            f"({TRAIT_DESCRIPTIONS['diversity'][rendered['diversity']['level']]}).")


def taste_summary(value):
    if isinstance(value, str):
        return value
    tastes = value.get("unique_tastes")
    if tastes is None:
        return value["summary"]
    rendered_tastes = "; ".join(
        f"{entry['taste']} ({entry['reason']})" for entry in tastes
    ) or "no stable unique taste identified"
    liked = ", ".join(value.get("liked_patterns", [])) or "no repeated liked pattern identified"
    disliked = (", ".join(value.get("disliked_patterns", []))
                 or "no repeated disliked pattern identified")
    return (f"Unique tastes: {rendered_tastes}. Liked patterns: {liked}. "
            f"Disliked patterns: {disliked}.")
