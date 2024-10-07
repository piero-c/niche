from langdetect import detect, DetectorFactory, LangDetectException

# TODO - Fix or remove language constraints
# TODO - pydocs
def is_text_in_english(text):
    # Fix random seed in langdetect for consistency
    DetectorFactory.seed = 0
    try:
        language = detect(text)
        return language == 'en'
    except LangDetectException:
        return False

def merge_dicts_with_weight(dicts: list[dict[any, int|float]], weights: list[int]) -> dict[any, int|float]:
    """Merge a list of dictionaries into one, considering the weight of each.

    Args:
        dicts (list[dict[any, int | float]]): The dictionaries.
        weights (list[int]): The weights.

    Returns:
        dict[any, int|float]: The merged dict.
    """
    assert(len(dicts) == len(weights))
    merged_dict = {}
    for (d, weight) in zip(dicts, weights):
        for key, value in d.items():
            merged_dict[key] = merged_dict.get(key, 0) + value * weight
    
    return merged_dict