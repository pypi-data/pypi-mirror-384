# -*-coding:utf-8-*-
"""
Created on 2024/09/29

@author: 臧韬

@desc: 因为框架打包不重启的时候会出现isinstance方法和issubclass函数出现问题，
       所以重新实现这两个方法，通过类名来确定是否为子类，而不是通过对象ID。
"""


def issubclassByName(cls, class_or_tuple: type | tuple):
    if isinstance(class_or_tuple, tuple):
        for cls_name in class_or_tuple:
            if issubclassByName(cls, cls_name):
                return True
        else:
            return False

    if not isinstance(cls, type):
        raise TypeError("issubclassByName() arg 0 must be a class")

    if not isinstance(class_or_tuple, type):
        raise TypeError("isinstanceByName() arg 1 must be a class or tuple with class")

    __className = class_or_tuple.__name__
    if cls is type:
        # 特殊情况
        mroNames = [item.__name__ for item in type.mro(type)]
    else:
        mroNames = [item.__name__ for item in cls.mro()]
    if __className in mroNames:
        return True
    else:
        return False


def isinstanceByName(obj, class_or_tuple: type | tuple):
    if isinstance(class_or_tuple, tuple):
        for cls_name in class_or_tuple:
            if isinstanceByName(obj, cls_name):
                return True
        else:
            return False

    if not isinstance(obj, object):
        raise TypeError("isinstanceByName() arg 0 must be an object")

    if not isinstance(class_or_tuple, type):
        raise TypeError("isinstanceByName() arg 1 must be a class or tuple with class")

    cls = type(obj)
    if cls.__name__ == class_or_tuple.__name__:
        return True
    return issubclassByName(cls, class_or_tuple)


if __name__ == "__main__":
    A = type("A", (object,), {})
    B = type("B", (A,), {})

    a = A()
    b = B()

    print("class B is subclass of A: ", issubclassByName(B, A))
    print("object b is instance of A: ", isinstanceByName(b, A))
    print("object b is instance of B: ", isinstanceByName(b, B))
    print("object b is instance of B or A: ", isinstanceByName(b, (B, A)))
    print("object a is instance of object: ", isinstanceByName(a, object))
    print("class A is instance of type: ", isinstanceByName(A, type))
    print("object a is not instance of type: ", not isinstanceByName(a, type))
