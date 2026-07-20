class HospitalException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class NotFoundException(HospitalException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(404, detail)


class UnauthorizedException(HospitalException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(401, detail)


class ForbiddenException(HospitalException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(403, detail)


class ValidationException(HospitalException):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(422, detail)
