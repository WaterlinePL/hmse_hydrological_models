from hmse_hydrological_models import model_config


def type_allowed(filename: str) -> bool:
    """
    @param filename: Path to the file whose extension needs to be checked
    @return: True if file has valid extension, False otherwise
    """

    # check if there even is an extension
    if '.' not in filename:
        return False

    # check if it's allowed
    extension = filename.rsplit('.', 1)[-1]
    return extension.upper() in model_config.ALLOWED_UPLOAD_TYPES
