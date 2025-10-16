import logging
import os
from datetime import datetime
from typing import List
from typing import Literal
from typing import Optional
from typing import Union

from redis import Redis
from redis_om import JsonModel
from redis_om.model.model import NotFoundError

from ..bliss_globals import current_session
from ..import_utils import UnavailableObject
from ..import_utils import is_available
from ..persistent.ndarray import PersistentNdArray
from .compatibility import Field
from .compatibility import get_redis_db_url

logger = logging.getLogger(__name__)

XrpdFieldName = Literal["radial", "azimuthal", "intensity"]


def _create_database_proxy() -> Union[Redis, UnavailableObject]:
    try:
        return Redis.from_url(get_redis_db_url())
    except Exception as ex:
        # We are here because one of these reasons:
        #  - BEACON_HOST is not defined (ValueError).
        #  - BEACON_HOST is wrong (some socket exception).
        #  - Beacon or Redis are down (some socket exception).
        if is_available(current_session):
            # We are in a Bliss session. We should always have access to Redis.
            raise
        # We are not in a Bliss session, most likely the test suite.
        logger.warning(
            "Redis connection not available (%s). If this is not the "
            "test suite there is an issue with BEACON_HOST=%r or Redis itself.",
            ex,
            os.environ.get("BEACON_HOST", None),
        )
        return UnavailableObject(ImportError())


class XrpdPlotInfo(JsonModel, frozen=True):
    scan_name: str
    lima_name: str
    radial_label: str
    azim_label: Optional[str]
    hdf5_url: Optional[str]
    timestamp: datetime = Field(default_factory=datetime.now)
    field_names: List[XrpdFieldName]

    @property
    def legend(self) -> str:
        return f"{self.scan_name} ({self.lima_name})"

    def _get_data_key(self, field_name: XrpdFieldName) -> str:
        return f"{self.scan_name}:{self.lima_name}:plot_data:{field_name}"

    def get_data_array(self, field_name: XrpdFieldName):
        if field_name not in self.field_names:
            raise KeyError(f"No field {field_name} in this PlotInfo")
        return PersistentNdArray(self._get_data_key(field_name))

    def delete_data_arrays(self):
        for field_name in self.field_names:
            PersistentNdArray(self._get_data_key(field_name)).remove()

    @classmethod
    def get(cls, pk):
        try:
            return super().get(pk)
        except NotFoundError:
            # Reraise NotFoundError to get more info in the error message
            raise KeyError(f"PlotInfo not found at {pk}@{cls._meta.database}")

    class Meta:
        database = _create_database_proxy()
