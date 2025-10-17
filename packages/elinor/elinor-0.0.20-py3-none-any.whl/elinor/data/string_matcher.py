from rapidfuzz import fuzz, process

def match_best_str(
    target: str,
    choices: list[str],
    score_cutoff: int = 70,
) -> tuple[str, float]:
    output = process.extractOne(target, choices, scorer=fuzz.ratio, score_cutoff=score_cutoff)
    if output is None:
        return "", 0 # Return empty string and score 0 if no match found
    best_match, best_score, _ = output
    return best_match, best_score
