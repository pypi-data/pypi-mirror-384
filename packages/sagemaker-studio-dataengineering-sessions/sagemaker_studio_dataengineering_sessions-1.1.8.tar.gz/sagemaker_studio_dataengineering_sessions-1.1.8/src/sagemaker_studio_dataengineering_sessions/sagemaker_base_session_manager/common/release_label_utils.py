def compare_emr_release_labels(label1, label2) -> int:
    """
    Compare two software release labels and return the newer one.

    The release labels are assumed to be in the format 'emr-X.Y.Z', where X, Y, and Z are integers.

    Args:
        label1 (str): The first release label to compare.
        label2 (str): The second release label to compare.

    Returns:
        1 -> if label1 is greater than label2
        0 -> if label1 is equals to label2
        -1 -> if label1 is smaller than label2
    """
    # Remove the leading 'emr-' from the labels
    label1 = label1.split("-")[1]
    label2 = label2.split("-")[1]

    # Split the labels into their components
    v1, v2, p1 = [int(x) for x in label1.split('.')]
    v3, v4, p2 = [int(x) for x in label2.split('.')]

    # Compare the major and minor version numbers
    if v1 > v3:
        return 1
    elif v1 < v3:
        return -1
    elif v2 > v4:
        return 1
    elif v2 < v4:
        return -1

    # Compare the patch version numbers
    elif p1 > p2:
        return 1
    elif p1 < p2:
        return -1
    else:
        return 0
