import inspect
import json

import requests


def forward(fullName):
    def inner(func):
        def wrapper(self, *args, **kwargs):
            appRule = app.env.getRuleByAppId(app.appId)
            # 当前APP, 不需要转发
            authApp = appRule.variables.get("authApp")
            if not authApp:
                return func(self, *args, **kwargs)
            else:
                if not app.env.envEntryList:
                    raise Exception("无环境入口")
                entry = app.domain
                uri = "{}/api/{}/{}/{}".format(
                    entry.strip("/"), authApp.replace(".", "/"), fullName.replace(".", "/"), func.__name__
                )
                argDict = {}
                f = inspect.getfullargspec(func)
                fargs = f.args
                fargs.pop(0)
                for key, value in zip(fargs, args):
                    argDict[key] = value
                if len(args) > len(f.args):
                    argDict[f.varargs] = args[len(f.args) - 1 :]
                for key, value in kwargs.items():
                    argDict[key] = value

                argDict = {"argDict": argDict}

                # 这里headers要把Token传过去
                try:
                    argDict = json.dumps(argDict)
                    response = requests.post(
                        uri,
                        data=argDict,
                        headers={"Content-Type": "application/json", "token": app.request.headers.get("token")},
                    )
                    print("===========================")
                    print("     uri: ", uri)
                    print("     data: ", argDict)
                    print("     response: ", response.text)
                    print("===========================")
                    resp = json.loads(response.text)
                except Exception:
                    raise Exception("响应无效")
                if resp["errcode"] != 0:
                    raise Exception(resp["errmsg"])
                data = resp["data"]
                return data

        return wrapper

    return inner
