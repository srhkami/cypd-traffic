from src.api.schemas import ApiResponse


def ok(message: str, data=None) -> ApiResponse:
    """建立成功的統一回應"""
    return ApiResponse(success=True, message=message, data=data)


def fail(message: str, data=None) -> ApiResponse:
    """建立失敗的統一回應"""
    return ApiResponse(success=False, message=message, data=data)
