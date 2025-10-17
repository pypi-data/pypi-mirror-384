import json

from mignonFramework import JsonConfigManager

from typing import Any


data = json.dumps({
    "data":{
        "stu":{
            "name":"hello",
            "age":22,
            "hello":[1, 2, 3, 4]
        }
    }
})
if isinstance(data, str):
    print(data)

class Data:
    data: Any


cls = JsonConfigManager.dictToObject(Data, data)
cls.data.stu.hello.append(3)
print(cls.data.stu.hello)