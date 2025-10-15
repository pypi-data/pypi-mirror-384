from typing import Optional, Dict, Any
from dataclasses import dataclass
from dbt.adapters.spark.relation import SparkRelation, SparkIncludePolicy

from dbt.adapters.spark.li_spark_utils import remove_undefined
from dbt.adapters.events.logging import AdapterLogger

logger = AdapterLogger("Spark")


@dataclass
class ExtendedSparkIncludePolicy(SparkIncludePolicy):
    database: bool = True


@dataclass(frozen=True, eq=False, repr=False)
class ExtendedSparkRelation(SparkRelation):
    is_openhouse: Optional[bool] = None

    @classmethod
    def __pre_deserialize__(cls, data: Dict[Any, Any]) -> Dict[Any, Any]:
        data = super().__pre_deserialize__(data)
        if "database" not in data["path"]:
            data["path"]["database"] = None
        else:
            data["path"]["database"] = remove_undefined(data["path"]["database"])
        return data
