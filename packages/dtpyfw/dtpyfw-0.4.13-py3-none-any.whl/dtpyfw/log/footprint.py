import logging

__all__ = ("leave",)


def leave(
    log_type: str,
    message: str | None = None,
    **kwargs,
):
    logger = logging.getLogger()

    kwargs["footprint"] = True
    kwargs["message"] = message

    data = dict(
        msg=message,
        extra={
            "details": kwargs,
        },
    )

    error_mapper = {
        "error": logger.error,
        "warning": logger.warning,
        "debug": logger.debug,
    }.get(log_type.lower(), logger.info)

    error_mapper(**data)
