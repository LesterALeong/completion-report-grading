def merge_counts(counts, additions):
    return {key: counts.get(key, 0) + additions.get(key, 0) for key in set(counts) | set(additions)}
