from pydggsapi.schemas.api.collection_providers import (
    CollectionProviderGetDataDictReturn,
    CollectionProviderGetDataReturn,
)
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import List, Union, Dict, Optional


@dataclass
class AbstractDatasourceInfo(ABC):
    data_cols: List[str] = field(default_factory=lambda: ["*"])
    exclude_data_cols: List[str] = field(default_factory=list)
    zone_groups: Optional[Dict[str, str]] = field(default_factory=dict)


class AbstractCollectionProvider(ABC):
    datasources: Dict[str, AbstractDatasourceInfo]

    # 1. The return data must be aggregated.
    # 2. The return consist of 4 parts (zoneIds, cols_name, cols_dtype, data)
    # 3. The zoneIds is the list of zoneID , its length must align with data's length
    # 4. cols_name and cols_dtype length must align
    # 5. data is the data :P
    # 6. In case of exception, return an empty CollectionProviderGetDataReturn, ie. all with []
    @abstractmethod
    def get_data(self, zoneIds: List[str], res: int, datasource_id: str) -> CollectionProviderGetDataReturn:
        raise NotImplementedError

    @abstractmethod
    def get_datadictionary(self) -> CollectionProviderGetDataDictReturn:
        raise NotImplementedError
