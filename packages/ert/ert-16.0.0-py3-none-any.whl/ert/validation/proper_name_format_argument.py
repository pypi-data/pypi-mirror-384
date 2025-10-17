import re

from .argument_definition import ArgumentDefinition
from .validation_status import ValidationStatus


class ProperNameFormatArgument(ArgumentDefinition):
    NOT_A_VALID_NAME_FORMAT = (
        "The argument must be a valid string containing a "
        "%d and only characters of these types: "
        "Letters: A-Z and a-z, "
        "numbers: 0-9, "
        "underscore: _, "
        "dash: -, "
        "period: . and "
        "brackets: > < "
    )

    PATTERN = re.compile(r"^[A-Za-z0-9_\-.<>]*(%d)[A-Za-z0-9_\-.<>]*$")

    def __init__(self, **kwargs: bool) -> None:
        super().__init__(**kwargs)

    def validate(self, token: str) -> ValidationStatus:
        validation_status = super().validate(token)

        if not validation_status:
            return validation_status

        match = ProperNameFormatArgument.PATTERN.match(token)

        if match is None:
            validation_status.setFailed()
            validation_status.addToMessage(
                ProperNameFormatArgument.NOT_A_VALID_NAME_FORMAT
            )
        elif not validation_status.failed():
            validation_status.setValue(token)

        return validation_status
