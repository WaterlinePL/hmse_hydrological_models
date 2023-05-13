from werkzeug.exceptions import HTTPException


class HydrusMissingFileError(HTTPException):
    code = 400
    description = "Hydrus model is missing an input file!"


class ModflowMissingFileError(HTTPException):
    code = 400
    description = "Modflow model is missing an input file!"


class ModflowCommonError(HTTPException):
    code = 400
    description = "Modflow model validation failed!"

