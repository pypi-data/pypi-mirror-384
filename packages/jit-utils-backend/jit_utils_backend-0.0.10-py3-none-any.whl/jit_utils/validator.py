from dataclasses import MISSING, dataclass, fields
from jit.errcode import Code

class ElementErrorCode:
    PARAMS_MISSING_ERROR = Code(code=47000, reason="元素{fullName}缺少配置参数:{fieldName}")
    PARAMS_TYPE_ERROR = Code(code=47001, reason="元素{fullName}配置参数:{fieldName}期望是{expect}传入是{actual}")


@dataclass
class ParamsValidator:

    def __init__(self, __fullName__, **kwargs):
        for fieldInfo in fields(self):
            fieldName = fieldInfo.name
            if fieldName not in kwargs:
                # 没有默认值
                if fieldInfo.default is MISSING:
                    raise ElementErrorCode.PARAMS_MISSING_ERROR.formatReason(fullName=__fullName__, fieldName=fieldName)

            value = kwargs.get(fieldName, fieldInfo.default)
            try:
                value = fieldInfo.type(value)
            except ValueError:
                raise ElementErrorCode.PARAMS_TYPE_ERROR.formatReason(
                    fullName=__fullName__, expect=fieldInfo.type.__name__, actual=type(value).__name__
                )
            setattr(self, fieldName, value)
        if hasattr(self, "__post_init__"):
            self.__post_init__(__fullName__)
