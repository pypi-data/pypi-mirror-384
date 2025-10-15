import re


def normalize_filename(filename: str) -> str:
    """
    Normalize a filename by replacing all special characters with underscores.
    Consecutive underscores are replaced with a single underscore.
    Periods are also replaced with underscores.

    Args:
        filename (str): The original filename

    Returns:
        str: Normalized filename with special characters replaced by underscores

    Examples:
        >>> normalize_filename('test (1).csv')
        'test_1_csv'
        >>> normalize_filename('file with..multiple...periods')
        'file_with_multiple_periods'
    """
    # Replace all special characters (non-alphanumeric) with underscores
    normalized = re.sub(r'\W', '_', filename)
    # Replace consecutive underscores with a single one
    normalized = re.sub(r'_+', '_', normalized)
    return normalized