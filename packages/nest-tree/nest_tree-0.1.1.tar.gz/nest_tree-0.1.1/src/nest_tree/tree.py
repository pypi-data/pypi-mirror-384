from typing import Union


def tree(
    data,
    leaf: str = "none",
    level: Union[int, None] = None,
    print_output: bool = True,
    return_output: bool = False,
):
    """
    Return a string representing the structure of a nested dict/list like `tree`.

    Args:
        data: dict or list (possibly nested)
        leaf (str): Controls leaf node behavior
            - "none": stop at innermost key/index, print nothing at leaves
            - "type": print str(type(value)) for leaves
            - "value": print str(value) for leaves
        level (str | None): maximum recursion depth (int or None). If None, expand fully.
        print_output (bool): if True, also print the result to stdout (default True)
        return_output (bool): if True, return the output string (default False)

    Returns:
        str: the textual tree representation
    """
    lines = []

    def _print(node, indent="", is_last=True, label=None, depth=0):
        # Print the current node's label (key or [index]) if we have one
        if label is not None:
            connector = "└── " if is_last else "├── "
            lines.append(indent + connector + str(label))
            indent = indent + ("    " if is_last else "│   ")

        # Stop if level limit is reached
        if level is not None and depth >= level:
            return

        # Recurse into containers
        if isinstance(node, dict):
            items = list(node.items())
            for i, (k, v) in enumerate(items):
                _print(v, indent, i == len(items) - 1, k, depth + 1)

        elif isinstance(node, list):
            for i, v in enumerate(node):
                _print(v, indent, i == len(node) - 1, f"[{i}]", depth + 1)

        else:
            # Leaf behavior
            if leaf == "none":
                return
            leaf_text = str(node) if leaf == "value" else str(type(node))
            lines.append(indent + "└── " + leaf_text)

    _print(data, "", True, None, 0)
    output = "\n".join(lines)
    if print_output:
        print(output)
    if return_output:
        return output
