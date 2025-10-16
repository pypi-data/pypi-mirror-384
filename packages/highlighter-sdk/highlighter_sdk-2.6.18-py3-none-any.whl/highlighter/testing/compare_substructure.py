class Anyval:
    def __repr__(self):
        return "anyval"


anyval = Anyval()


def path_str(p):  # Pretty path display
    return p or "root"


def compare_substructure(full, part, path="", allow_extra_list_elements=True, allow_extra_dict_keys=True):
    """
    Recursively checks whether `part` is contained within `full`.
    """
    recursion_kwargs = {
        "allow_extra_list_elements": allow_extra_list_elements,
        "allow_extra_dict_keys": allow_extra_dict_keys,
    }
    if isinstance(part, dict):
        if not isinstance(full, dict):
            raise ValueError(f"Type mismatch at {path_str(path)}: expected dict, got {type(full).__name__}")
        matched_keys = []
        for pkey, pval in part.items():
            if pkey is anyval:
                for fkey, fval in full.items():
                    try:
                        compare_substructure(
                            fval, pval, f"{path}[{fkey}]" if path else f"[{fkey}]", **recursion_kwargs
                        )
                        matched_keys.append(fkey)
                        break
                    except ValueError:
                        pass
                else:
                    raise ValueError(
                        f"Missing value at {f"{path}[anyval]" if path else "[anyval]"}: Part value {pval} matches no dict value of {full}"
                    )
            elif pkey not in full:
                raise ValueError(f"Missing key '{pkey}' at {path_str(path)}")
            else:
                compare_substructure(
                    full[pkey], pval, f"{path}[{pkey}]" if path else f"[{pkey}]", **recursion_kwargs
                )
                matched_keys.append(pkey)
        if allow_extra_dict_keys or matched_keys == list(full.keys()):
            return True
        else:
            raise ValueError(f"Part {part} is missing dict keys {list(set(full.keys()) - set(matched_keys))}")

    elif isinstance(part, list):
        if not isinstance(full, list):
            raise ValueError(
                f"Type mismatch at {path_str(path)}: expected list of {part}, got {type(full).__name__} {full}"
            )
        return compare_iterable(full, part, path, **recursion_kwargs)
    elif isinstance(part, tuple):
        if not isinstance(full, tuple):
            raise ValueError(
                f"Type mismatch at {path_str(path)}: expected tuple of {part}, got {type(full).__name__} {full}"
            )
        return compare_iterable(full, part, path, **recursion_kwargs)
    else:
        if not part is anyval and full != part:
            raise ValueError(f"Value mismatch at {path_str(path)}: expected {part!r}, got {full!r}")
        return True


def compare_iterable(full, part, path, allow_extra_list_elements=True, **kwargs):
    consumed_index = 0
    errors = []
    n_matched_items = 0
    for subpart in part:
        for j, f in enumerate(full[consumed_index:]):
            index = consumed_index + j
            try:
                compare_substructure(
                    f,
                    subpart,
                    f"{path}[{index}]" if path else f"[{index}]",
                    allow_extra_list_elements=allow_extra_list_elements,
                    **kwargs,
                )
                consumed_index = index + 1
                n_matched_items += 1
                break
            except ValueError as e:
                errors.append(str(e))
        else:
            raise ValueError(
                f"Value mismatch at {path_str(path)}: Part {subpart} matches no element of {full[consumed_index:]}.\n{path_str(path)}: All errors:\n{f'\n{path_str(path)}: '.join(errors)}"
            )
    if allow_extra_list_elements or n_matched_items == len(full):
        return True
    else:
        raise ValueError(
            f"At path {path_str(path)} only {n_matched_items} of {len(full)} matched.\n{path_str(path)}: All errors:\n{f'\n{path_str(path)}: '.join(errors)}\n{path_str(path)}: Unmatched items: {full[consumed_index:]}"
        )
