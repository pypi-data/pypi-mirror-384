from ..core.require_extra import require_extra

__all__ = ("bucket",)

require_extra("bucket", "boto3", "botocore")
