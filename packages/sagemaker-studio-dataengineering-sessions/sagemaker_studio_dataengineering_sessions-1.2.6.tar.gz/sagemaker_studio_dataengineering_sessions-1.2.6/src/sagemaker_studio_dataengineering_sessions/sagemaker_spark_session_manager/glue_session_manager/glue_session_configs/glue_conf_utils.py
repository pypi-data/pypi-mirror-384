from sagemaker_studio_dataengineering_sessions.sagemaker_base_session_manager.common.sagemaker_connection_display import SageMakerConnectionDisplay


def string_to_dict(input_string: str) -> dict[str, any]:
    """
    Convert a configuration string to a dictionary.

    Args:
        input_string: The input configuration string

    Returns:
        Dictionary containing the parsed configuration
    """
    try:
        # Input validation
        if not isinstance(input_string, str):
            raise TypeError("Input must be a string")

        # Split the string by '--conf' and remove any leading/trailing whitespace
        parts = [part.strip() for part in input_string.split('--conf') if part.strip()]
        result = {}

        for part in parts:
            if '=' not in part:
                SageMakerConnectionDisplay.write_msg(f"Skipping invalid config (no '=' found): {part}")
                continue

            key, value = part.split('=', 1)
            key = key.strip()
            value = value.strip()

            if not key or not value:
                SageMakerConnectionDisplay.write_msg(f"Skipping invalid config (key or value is empty): {part}")
                continue

            # Check for duplicate keys
            if key in result:
                SageMakerConnectionDisplay.write_msg(f"Duplicate key found: {key}. Using last value.")

            result[key] = value

        return result

    except Exception as e:
        SageMakerConnectionDisplay.send_error(f"Invalid config string: {str(e)}")
        raise


def dict_to_string(input_dict: dict[str, any]) -> str:
    """
    Convert a configuration dictionary to a Spark configuration string.

    Args:
        input_dict: The input configuration dictionary

    Returns:
        String containing the formatted configuration
    """
    try:
        # Input validation
        if not isinstance(input_dict, dict):
            raise TypeError("Input must be a dictionary")

        # Validate and process each key-value pair
        valid_pairs = []
        for key, value in input_dict.items():
            if not isinstance(key, str):
                SageMakerConnectionDisplay.write_msg(f"Skipping invalid key: {key}")
                continue
            if value is None:
                SageMakerConnectionDisplay.write_msg(f"Skipping empty value: {key}={value}")
                continue

            if isinstance(value, bool):
                formatted_value = str(value).lower()
            elif isinstance(value, str):
                formatted_value = value.strip()
            else:
                formatted_value = value
            valid_pairs.append(f"{key.strip()}={formatted_value}")

        # if dict is empty, return empty string
        return " --conf ".join(valid_pairs)

    except Exception as e:
        SageMakerConnectionDisplay.send_error(f"Unable to convert dictionary to string: {str(e)}")
        raise
