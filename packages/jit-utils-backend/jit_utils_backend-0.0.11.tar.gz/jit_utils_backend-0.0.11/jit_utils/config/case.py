# -*-coding:utf-8-*-
"""
Created on 2023/10/23

@author: 臧韬

@desc: 默认描述
"""
from .config import TlConfig
from .field import IntField, StringField


class TlConfigCase(object):
    def normal(self):
        """这是一个普通使用的例子"""

        class IDCardConfig(TlConfig):
            name = StringField(maxLen=8, minLen=2, required=True)
            age = IntField(maxNum=200, minNum=0, default=18)

        config = IDCardConfig(name="张三", age=18)
        print("normal case: config.name -> {}".format(config.name))
        print("normal case: config.age -> {}".format(config.age))
        print("normal case: config.toDict -> {}".format(config.value))

        # 如果没有传入会使用默认值
        config2 = IDCardConfig(name="李四")
        print("normal case: config2.age -> {}".format(config2.age))

        try:
            IDCardConfig(age=21)
        except Exception as e:
            print("normal case: error -> {}".format(e))

    def transform(self):
        class IDCardConfig(TlConfig):
            name = StringField(maxLen=8, minLen=2)
            age = IntField(maxNum=200, minNum=0)

        config = IDCardConfig(name="张三", age="18")
        print("transform case: config.age -> {}".format(config.age))
        print("transform case: config.age type -> {}".format(type(config.age)))

    def customTransform(self):
        # 通过自定义的字段来自定义转换方式
        class DoubleIntField(IntField):
            def __init__(self, *args, **kwargs):
                super(DoubleIntField, self).__init__(*args, **kwargs)

                self.transformFunc = self.toDouble

            @staticmethod
            def toDouble(value):
                return value * 2

        class MyConfig(TlConfig):
            # 使用自定义的转换方法
            double = DoubleIntField(maxNum=200)

        config = MyConfig(double=100)

        # 输出的值变成了输入的两倍
        print("transform case: config.double -> {}".format(config.double))

        config.double = 20

        # 如果是后面赋值，也会及时校验和转换
        print("transform case: config.double -> {}".format(config.double))
        # 检测会在转换后进行检测合法性，这里输入101，通过转换后变成202，超过了字段设置的最大值，所以会触发报错
        try:
            config.double = 101
        except Exception as e:
            print("transform case: errmsg -> {}".format(e))


if __name__ == "__main__":
    TlConfigCase().normal()
