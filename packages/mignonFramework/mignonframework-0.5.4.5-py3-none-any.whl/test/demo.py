import datetime
from typing import List

from mignonFramework import JsonConfigManager as js, injectJson, ClassKey, JsonConfigManager, SQLiteTracker, TableId, injectSQLite, VarChar

from typing import Annotated

config = SQLiteTracker("./resources/config/tracker.db")

@TableId("name")
@VarChar("name",100)
@VarChar("time",100)
class Info:
    name:str
    age:int
    time: str


@injectSQLite(config)
class Data:
    stu:List[Info]
    teacher: str



data = Data()

