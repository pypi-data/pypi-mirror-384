#
# Copyright 2025 DataRobot, Inc. and its affiliates.
#
# All rights reserved.
#
# DataRobot, Inc.
#
# This is proprietary source code of DataRobot, Inc. and its
# affiliates.
#
# Released under the terms of DataRobot Tool and Utility Agreement.
from __future__ import annotations

import math
from typing import Any, Callable, List, Optional

import pandas as pd

from dmm.constants import ColumnName


class GeospatialSupport:
    """
    One class for geospatial handling in both places:
      • Evaluator: collect per-chunk geometry, reduce per bucket, and finalize into a geo-shaped DataFrame.
      • Report: resolve/attach 'geospatialCoordinate' (WKT) to each bucket row.

    If geo_attr is falsy (metric is not geospatial), all methods are no-ops.
    """

    def __init__(
        self,
        geo_attr: Optional[str],
        timestamp_col: Optional[str] = None,
        metric_name: Optional[str] = None,
    ):
        self.geo_attr = geo_attr or None
        self.timestamp_col = timestamp_col
        self.metric_name = metric_name or "metric"

        self._bucket_frames: List[pd.DataFrame] = []
        self._final_frames: List[pd.DataFrame] = []

        self._row_resolvers: tuple[Callable[[dict], Optional[str]], ...] = (
            self._from_server_attr,
            self._from_camel,
            self._from_snake,
            self._from_lonlat,
            self._from_geometry,
        )

    def attach(self, bucket: dict, row_like: Any) -> None:
        """
        Attach 'geospatialCoordinate' to the bucket if geo is configured; no-op if not.
        Raises ValueError if configured but not resolvable from row.
        """
        if not self.geo_attr:
            return

        row = row_like if isinstance(row_like, dict) else row_like.to_dict()
        for fn in self._row_resolvers:
            wkt = fn(row)
            if wkt:
                bucket["geospatialCoordinate"] = wkt
                return

        raise ValueError(
            f"Geospatial metric expects coordinates in '{self.geo_attr}' "
            "(or 'geospatialCoordinate', 'geospatial_coordinate', "
            "'longitude'+'latitude', or 'geometry')."
        )

    def ingest_chunk(self, chunk: pd.DataFrame) -> None:
        """Collect per-row geometry from a chunk. No-op if not geospatial or timestamp_col not set."""
        if (
            not (self.geo_attr and self.timestamp_col)
            or self.timestamp_col not in chunk
        ):
            return

        ts = pd.to_datetime(self._safe_ts_series(chunk), utc=True, errors="coerce")

        df = None
        if self.geo_attr in chunk.columns:
            df = pd.DataFrame(
                {"timestamp": ts, "geometry": chunk[self.geo_attr].astype(str)}
            )
        elif {"longitude", "latitude"}.issubset(chunk.columns):
            lon = pd.to_numeric(chunk["longitude"], errors="coerce")
            lat = pd.to_numeric(chunk["latitude"], errors="coerce")
            ok = lon.between(-180, 180) & lat.between(-90, 90)
            if ok.any():
                df = pd.DataFrame(
                    {
                        "timestamp": ts[ok],
                        "geometry": "POINT ("
                        + lon[ok].astype(float).astype(str)
                        + " "
                        + lat[ok].astype(float).astype(str)
                        + ")",
                    }
                )
        elif "geometry" in chunk.columns:
            df = pd.DataFrame(
                {"timestamp": ts, "geometry": chunk["geometry"].astype(str)}
            )

        if df is None:
            return

        df = df.dropna(subset=["timestamp", "geometry"])
        if df.empty:
            return

        df["sampleSize"] = 1
        df["value"] = 1.0
        self._bucket_frames.append(df[["timestamp", "geometry", "sampleSize", "value"]])

    def reduce_bucket(self, bucket_timestamp) -> None:
        """Reduce collected rows for the completed bucket into per-(timestamp, geometry) aggregates."""
        if not self.geo_attr or not self._bucket_frames:
            return
        gdf = pd.concat(self._bucket_frames, ignore_index=True)
        gdf["timestamp"] = pd.to_datetime(bucket_timestamp, utc=True)

        red = gdf.groupby(["timestamp", "geometry"], as_index=False).agg(
            sampleSize=("sampleSize", "sum"), value=("value", "sum")
        )
        red = red.rename(
            columns={"sampleSize": ColumnName.NR_SAMPLES, "value": self.metric_name}
        )
        self._final_frames.append(
            red[
                ["timestamp", ColumnName.NR_SAMPLES, self.metric_name, "geometry"]
            ].copy()
        )
        self._bucket_frames.clear()

    def finalize(self, base_df: pd.DataFrame) -> pd.DataFrame:
        """
        Return a DataFrame suitable for report():
          • If geo output exists, return geo-shaped frame (timestamp, samples, <metric>, geometry).
          • Otherwise, return the original base_df unchanged.
        No explicit if/return in caller code; just:  result_df = geo.finalize(result_df)
        """
        if not self._final_frames:
            return base_df
        geo_df = pd.concat(self._final_frames, ignore_index=True)
        return geo_df.sort_values(["timestamp", "geometry"], ignore_index=True)

    def _from_server_attr(self, row: dict) -> Optional[str]:
        return self._to_wkt(row.get(self.geo_attr)) if self.geo_attr else None

    @staticmethod
    def _from_camel(row: dict) -> Optional[str]:
        return GeospatialSupport._to_wkt(row.get("geospatialCoordinate"))

    @staticmethod
    def _from_snake(row: dict) -> Optional[str]:
        return GeospatialSupport._to_wkt(row.get("geospatial_coordinate"))

    @staticmethod
    def _from_geometry(row: dict) -> Optional[str]:
        return GeospatialSupport._to_wkt(row.get("geometry"))

    @staticmethod
    def _from_lonlat(row: dict) -> Optional[str]:
        lon, lat = row.get("longitude"), row.get("latitude")
        try:
            lon_f, lat_f = float(lon), float(lat)
        except (TypeError, ValueError):
            return None
        if -180.0 <= lon_f <= 180.0 and -90.0 <= lat_f <= 90.0:
            return f"POINT ({lon_f} {lat_f})"
        return None

    @staticmethod
    def _to_wkt(val: Any) -> Optional[str]:
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return None
        if isinstance(val, dict):
            coords = val.get("coordinates") or val.get("coord")
            if isinstance(coords, (list, tuple)) and len(coords) >= 2:
                try:
                    lon, lat = float(coords[0]), float(coords[1])
                except (TypeError, ValueError):
                    return None
                if -180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0:
                    return f"POINT ({lon} {lat})"
                return None
        s = str(val).strip()
        return s or None

    def _safe_ts_series(self, chunk: pd.DataFrame) -> pd.Series:
        ts_obj = chunk[self.timestamp_col]
        if isinstance(ts_obj, pd.DataFrame):
            col_selector = ~ts_obj.columns.duplicated()
            ts_series = ts_obj.loc[:, col_selector].iloc[:, 0]
            ts_series.index = chunk.index
            return ts_series
        return ts_obj
