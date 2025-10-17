# -*-coding:utf-8-*-
"""
Created on 2022/12/27

@author: lyon

@desc:
"""

from jit.commons.utils.logger import log


class Converter(object):

    def __init__(self):
        self._globals = {}

    def getFuncSubClasses(self, baseCls):
        for subCls in baseCls.__subclasses__():
            if hasattr(subCls, "function"):
                self._globals[subCls.function] = subCls
            self.getFuncSubClasses(subCls)

    def getExprSubClasses(self, baseCls):
        for subCls in baseCls.__subclasses__():
            self._globals[subCls.__name__] = subCls
            self.getExprSubClasses(subCls)

    def eval(self, expression):
        # t表达式里面有 "T(modelPath)xxx"
        # 加载FUNC子类
        from models.Meta import Expression

        self.getExprSubClasses(Expression)
        Sql = app.getElement("globals.Sql")
        self._globals["Calc"] = Sql
        self._globals["null"] = None
        return eval(expression, self._globals)


converter = Converter()


class MemoryCompiler(object):
    """
    Q表达式内存计算判断
    """

    def __init__(self, expression, data=None):
        self.expression = expression
        self.data = data

    def parse(self):
        from models.Meta import Func

        if isinstance(self.expression, Func):
            result = FuncParser(self.expression).getMemory(self)
        else:
            # 根据类名选择对应的解析器(解析器需要我们自己手动去完成构建)
            Parser = globals()[self.expression.__class__.__name__ + "Parser"]
            result = Parser(self.expression).getMemory(self)
        return result

    def evalQ(self):
        try:
            result = self.parse()
            return converter.eval("lambda x: %s" % result)(self.data)
        except Exception as e:
            log.error(e)
            return False


class ExpressionParser(object):

    def __init__(self, *args, **kwargs):
        self.quoteCache = {"*": "*"}

    def getMemory(self, compiler):
        raise NotImplementedError


class QParser(ExpressionParser):
    """
    Q表达式解析
    """

    def __init__(self, q):
        super(QParser, self).__init__(q)
        self.q = q

    def getMemory(self, compiler):
        from models.Meta import QAND, QOR, getLookup

        result = []
        if self.q.sourceExpressions:
            # 嵌套结构
            for expr in self.q.sourceExpressions:
                if isinstance(expr, (QAND, QOR)):
                    result.append(expr())
                else:
                    result.append(self.__class__(expr).getMemory(compiler))
        else:
            # 非嵌套结构
            lookup = getLookup(self.q.compareName)
            if lookup:
                result.append(LookupParser(lookup(self.q.lhs, self.q.rhs)).getMemory(compiler))
        return "({})".format(" ".join(result))


class LookupParser(ExpressionParser):

    def __init__(self, lookup):
        super(LookupParser, self).__init__(lookup)
        self.lookup = lookup

    def getMemory(self, compiler):
        ls = MemoryCompiler(self.lookup.lhs, compiler.data).parse()
        rs = MemoryCompiler(self.lookup.rhs, compiler.data).parse()
        if "{ls}" in self.lookup.memory:
            return self.lookup.memory.format(ls=ls, rs=rs)
        return "(%s %s %s)" % (ls, self.lookup.memory, rs)


class FuncParser(ExpressionParser):

    def __init__(self, func):
        super(FuncParser, self).__init__(func)
        self.func = func

    def getMemory(self, compiler):
        exps = [str(MemoryCompiler(exp, compiler.data).parse()) for exp in self.func.sourceExpressions]
        return "%s(%s)" % (self.func.memory, ", ".join(exps))


class FParser(ExpressionParser):

    def __init__(self, f):
        super(FParser, self).__init__(f)
        self.f = f

    def getMemory(self, compiler):
        """
        如果有数据, 就返回值
        没有, 就返回 x.字段
        """
        # TODO: 暂时先只做一层
        return repr(compiler.data.get(self.f.fieldId, "x.%s" % self.f.fieldId))


class ValueParser(ExpressionParser):

    def __init__(self, value):
        super(ValueParser, self).__init__(value)
        self.value = value

    def getMemory(self, compiler):
        return repr(self.value.value)


class CombinedExpressionParser(ExpressionParser):

    def __init__(self, combine):
        super(CombinedExpressionParser, self).__init__(combine)
        self.combine = combine

    def getMemory(self, compiler):
        left = MemoryCompiler(self.combine.lhs, compiler.data).parse()
        right = MemoryCompiler(self.combine.rhs, compiler.data).parse()
        return "(%s %s %s)" % (left, self.combine.connector, right)
