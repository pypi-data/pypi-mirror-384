
def validate_input_parameters(input_parameters: dict, required_keys: list[str]) -> bool:
    """
    Function to validate the input parameters in a pipeline component.

    Args:
        input_parameters (dict): the input parameters whose key presence will be validated.
        required_keys (list[str]): keys that must be present in the input parameters.

    Raises:
        ValueError: if any of the required keys are missing from the input parameters.

    Returns:
        bool: flag indicating whether the input parameters are valid.
    """

    missing_keys = [key for key in required_keys if key not in input_parameters]
    if len(missing_keys) > 0:
        raise ValueError(f"Input parameters must contain the following keys: {', '.join(missing_keys)}")
    return True