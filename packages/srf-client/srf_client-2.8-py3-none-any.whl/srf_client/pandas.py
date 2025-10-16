from __future__ import annotations

import io
import math
from datetime import timedelta, timezone
from functools import partial, reduce
from typing import Any, Callable, Collection, List, Optional, Union, cast, \
    NamedTuple, MutableMapping

import pandas as pd

from .model import ChargerTransaction, Leg, Trip

DF_BiFunc = Callable[[pd.DataFrame, pd.DataFrame], pd.DataFrame]


def to_numeric(v: str) -> int | float:
    """Convert a string to a number, coercing errors into NaN."""
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return math.nan


class Data(NamedTuple):
    """Alternate shape for leg data."""

    index: List[int]
    data: List[tuple]


def get_data_frame(self: Union[Leg, Trip],
                   data_types: Union[str, Collection[str]],
                   resolution: Union[str, timedelta, None] = None,
                   conversion: Optional[Callable[[str], Any]] = to_numeric,
                   include_can_source: bool = None
                   ) -> pd.DataFrame:
    """
    Return available measurements as a time-series :code:`DataFrame`.

    :code:`Series` will be named :code:`{TYPE}_{FIELD}` in the order given
    by :code:`data_types`.

    Data will be interpolated to the specified resolution.

    :param data_types: Data types to fetch.
    :param resolution: Target resolution. If :code:`None` (the default) then
        it will use the approximate resolution of the first requested type.
    :param conversion: Conversion to apply to all values. If :code:`None`
        then all values will be strings.
    :param include_can_source: Include and partition by multiple CAN sources.

    .. versionchanged:: 2.3
       Added ``include_can_source`` parameter.
    """
    if isinstance(data_types, str):
        data_types = [data_types]

    collected: MutableMapping[str, Optional[Data]] = {
        dt: Data([], []) for dt in data_types
    }
    for m in self.get_data(include=data_types):
        collected[m.type].index.append(int(m.timestamp))
        row = m.data.split(',')
        if conversion is not None:
            if include_can_source:
                row[1:] = [conversion(v) for v in row[1:]]
            else:
                row = (conversion(v) for v in row)
        collected[m.type].data.append(tuple(row))

    to_dt = partial(pd.to_datetime, unit='ms')
    if resolution is None and len(data_types) > 1:
        try:
            index = collected[data_types[0]].index
            resolution = to_dt(index[1]) - to_dt(index[0])
        except IndexError:
            raise ValueError('No data for first type and no resolution given')

    new_index = None
    if resolution is not None:
        # np.datetime64 cannot hold timezone
        start = self.start_time.astimezone(timezone.utc).replace(tzinfo=None)
        end = self.end_time.astimezone(timezone.utc).replace(tzinfo=None)
        new_index = pd.date_range(start=pd.to_datetime(start).ceil(resolution),
                                  end=pd.to_datetime(end).ceil(resolution),
                                  freq=resolution)

    type_defs = self._client.get_types()

    converted: List[pd.DataFrame] = []
    for dt in data_types:
        if len(collected[dt].index) == 0:
            continue

        index = pd.DatetimeIndex(to_dt(collected[dt].index))
        data = collected[dt].data
        columns = [f'{dt} {field.name}' for field in type_defs[dt].fields]
        if include_can_source and dt[0].isalpha():
            columns = ['source'] + columns
        del collected[dt]  # allow GC of the data during loop
        df = pd.DataFrame.from_records(data=data,
                                       index=index,
                                       columns=columns)

        if not index.is_unique:
            # https://csrf.atlassian.net/browse/PLAT-222
            df = df[~index.duplicated()]
            index = df.index

        if 'source' in df.columns:
            out = []
            grouped = df.groupby('source', sort=False)
            for source, idx in grouped.groups.items():
                out.append(df.loc[idx, :]
                           .drop(columns=['source'])
                           .rename(mapper=lambda x: f'{x} {source}', axis=1))
        else:
            out = (df,)

        for df in out:
            if new_index is not None:
                df = df \
                    .reindex(index.union(new_index)) \
                    .interpolate(method='index') \
                    .reindex(new_index)

            if not df.empty:
                converted.append(df)

    if len(converted) == 0:
        return pd.DataFrame()
    else:
        return reduce(cast(DF_BiFunc, pd.DataFrame.join), converted)


def get_gradient_frame(self: Leg, **kwargs) -> pd.DataFrame:
    """
    Return computed gradient data as a time-series :code:`DataFrame`.

    :param generate: Request and wait for generation if not available
    :param timeout: How long to wait if requesting generation

    .. versionadded:: 1.4
    """
    type_defs = self._client.get_types()
    columns = ['9 ' + field.name for field in type_defs['9'].fields]

    data = self.get_gradient(**kwargs)
    if not data:
        return pd.DataFrame()

    # TODO: load csv directly?
    df = pd.DataFrame.from_records(
        ((pd.to_datetime(int(m.timestamp), unit='ms'), *(
            pd.to_numeric(v) for v in m.data.split(','))) for m in data),
        index='timestamp',
        columns=['timestamp', *columns]
    )
    return df


def get_transaction_frame(self: ChargerTransaction) -> pd.DataFrame:
    """
    Return meter readings as a time-series :code:`DataFrame`.

    .. versionadded:: 2.1
    """
    response = self._client.get(self.uri + '/data',
                                headers={'Accept': 'text/csv'})
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text),
                     names=['timestamp', 'value'],
                     dtype={'timestamp': 'int64',
                            'value': 'float64'},
                     index_col='timestamp')
    df.index = pd.to_datetime(df.index, unit='ms')
    return df


Leg.get_data_frame = get_data_frame
Trip.get_data_frame = get_data_frame
Leg.get_gradient_frame = get_gradient_frame
ChargerTransaction.get_data_frame = get_transaction_frame
