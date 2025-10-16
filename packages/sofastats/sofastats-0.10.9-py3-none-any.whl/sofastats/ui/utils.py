from typing import Any

def get_unlabelled(possibly_labelled: Any) -> str:
    """
    e.g. 'Country (country)' => 'country'
    'NZ (1)' => '1'
    """
    try:
        if '(' in possibly_labelled:
            start_idx = possibly_labelled.rindex('(')
            unlabelled = possibly_labelled[start_idx:].lstrip('(').rstrip(')')
        else:
            unlabelled = possibly_labelled
    except TypeError as e:  ## e.g. a number
        unlabelled = possibly_labelled
    return unlabelled
