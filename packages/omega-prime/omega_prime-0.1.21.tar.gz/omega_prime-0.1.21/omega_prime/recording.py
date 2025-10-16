import typing
from pathlib import Path
from warnings import warn

import betterosi
import numpy as np
import shapely
from matplotlib import pyplot as plt
from matplotlib.patches import Polygon as PltPolygon
import pandas as pd
import polars as pl
import altair as alt
import json
import pandera.polars as pa
import pandera.extensions as extensions
import pyarrow
import pyarrow.parquet as pq
import polars as pl
from .map_odr import MapOdr
from .map import MapOsi, ProjectionOffset, MapOsiCenterline
import itertools
import altair as alt
import polars as pl
import polars_st as st

pi_valued = pa.Check.between(-np.pi, np.pi)
polars_schema = {
    "total_nanos": pl.Int64,
    "idx": pl.Int64,
    "x": pl.Float64,
    "y": pl.Float64,
    "z": pl.Float64,
    "vel_x": pl.Float64,
    "vel_y": pl.Float64,
    "vel_z": pl.Float64,
    "acc_x": pl.Float64,
    "acc_y": pl.Float64,
    "acc_z": pl.Float64,
    "length": pl.Float64,
    "width": pl.Float64,
    "height": pl.Float64,
    "roll": pl.Float64,
    "pitch": pl.Float64,
    "yaw": pl.Float64,
    "type": pl.Int64,
    "role": pl.Int64,
    "subtype": pl.Int64,
}


@extensions.register_check_method(
    statistics=["column_name", "column_value", "other_column_name", "other_column_unset_value"]
)
def other_column_set_on_column_value(
    polars_obj, *, column_name: str, column_value, other_column_name: str, other_column_unset_value
):
    return polars_obj.lazyframe.select(
        ~(pl.col(column_name) == column_value).and_(pl.col(other_column_name) == other_column_unset_value)
    )


@extensions.register_check_method(
    statistics=["column_name", "column_value", "other_column_name", "other_column_unset_value"]
)
def other_column_unset_on_column_value(
    polars_obj, *, column_name, column_value, other_column_name: str, other_column_unset_value: int
):
    return polars_obj.lazyframe.select(
        ~(pl.col(column_name) != column_value).and_(pl.col(other_column_name) != other_column_unset_value)
    )


def has_no_frame_skip(df):
    return (
        df.group_by("idx")
        .agg(((pl.col("frame").sort().diff().drop_nulls() == 1).all()).alias("no_skip"))
        .select(pl.col("no_skip").all())
        .row(0)[0]
    )


@extensions.register_check_method()
def check_has_no_frame_skip(polars_obj):
    return polars_obj.lazyframe.select(pl.col("frame").sort().diff().fill_null(1).over("idx") == 1)


recording_moving_object_schema = pa.DataFrameSchema(
    title="DataFrame Schema for ASAM OSI GroundTruth of MovingObjects",
    description="",
    columns={
        "x": pa.Column(polars_schema["x"], title="MovingObject.base.position.x", description="osi3.Vector3d.x"),
        "y": pa.Column(polars_schema["y"], title="MovingObject.base.position.y", description="osi3.Vector3d.y"),
        "z": pa.Column(polars_schema["z"], title="MovingObject.base.position.z", description="osi3.Vector3d.z"),
        "vel_x": pa.Column(polars_schema["vel_x"], title="MovingObject.base.velocity.x", description="osi3.Vector3d.x"),
        "vel_y": pa.Column(polars_schema["vel_y"], title="MovingObject.base.velocity.y", description="osi3.Vector3d.y"),
        "vel_z": pa.Column(polars_schema["vel_z"], title="MovingObject.base.velocity.z", description="osi3.Vector3d.z"),
        "acc_x": pa.Column(
            polars_schema["acc_x"], title="MovingObject.base.acceleration.x", description="osi3.Vector3d.x"
        ),
        "acc_y": pa.Column(
            polars_schema["acc_y"], title="MovingObject.base.acceleration.y", description="osi3.Vector3d.y"
        ),
        "acc_z": pa.Column(
            polars_schema["acc_z"], title="MovingObject.base.acceleration.z", description="osi3.Vector3d.z"
        ),
        "length": pa.Column(
            polars_schema["length"],
            pa.Check.gt(0),
            title="MovingObject.base.dimesion.length",
            description="osi3.Dimenstion3d.length",
        ),
        "width": pa.Column(
            polars_schema["width"],
            pa.Check.gt(0),
            title="MovingObject.base.dimesion.width",
            description="osi3.Dimenstion3d.width",
        ),
        "height": pa.Column(
            polars_schema["height"],
            pa.Check.ge(0),
            title="MovingObject.base.dimesion.height",
            description="osi3.Dimenstion3d.height",
        ),
        "type": pa.Column(
            polars_schema["type"],
            pa.Check.between(
                0, 4, error=f"Type must be one of { ({o.name: o.value for o in betterosi.MovingObjectType}) }"
            ),
            title="MovingObject.type",
            description="osi3.MovingObject.Type",
        ),
        "role": pa.Column(
            polars_schema["role"],
            pa.Check.between(
                -1,
                10,
                error=f"Type must be one of { ({o.name: o.value for o in betterosi.MovingObjectVehicleClassificationRole}) }",
            ),
            title="MovingObject.vehicle_classification.role",
            description="osi3.MovingObject.VehicleClassification.Role",
        ),
        "subtype": pa.Column(
            polars_schema["subtype"],
            pa.Check.between(
                -1,
                17,
                error=f"Subtype must be one of { ({o.name: o.value for o in betterosi.MovingObjectVehicleClassificationType}) }",
            ),
            title="MovingObject.vehicle_classification.type",
            description="osi3.MovingObject.VehicleClassification.Type",
        ),
        "roll": pa.Column(
            polars_schema["roll"],
            pi_valued,
            title="MovingObject.base.orientation.roll",
            description="osi3.Orientation3d.roll",
        ),
        "pitch": pa.Column(
            polars_schema["pitch"],
            pi_valued,
            title="MovingObject.base.orientation.pitch",
            description="osi3.Orientation3d.pitch",
        ),
        "yaw": pa.Column(
            polars_schema["yaw"],
            pi_valued,
            title="MovingObject.base.orientation.yaw",
            description="osi3.Orientation3d.yaw",
        ),
        "idx": pa.Column(
            polars_schema["idx"], pa.Check.ge(0), title="MovingObject.id.value", description="osi3.Identifier.value"
        ),
        "total_nanos": pa.Column(
            polars_schema["total_nanos"],
            pa.Check.ge(0),
            title="GroundTruth.timestamp.nanos+1e9*GroundTruth.timestamp.seconds",
            description="osi3.Timestamp.nanos, osi3.Timestamp.seconds",
        ),
    },
    unique=["idx", "total_nanos"],
    checks=[
        pa.Check.other_column_set_on_column_value(
            "type",
            int(betterosi.MovingObjectType.TYPE_VEHICLE),
            "role",
            -1,
            error="`role` is `-1` despite type beeing `TYPE_VEHICLE`",
        ),
        pa.Check.other_column_unset_on_column_value(
            "type",
            int(betterosi.MovingObjectType.TYPE_VEHICLE),
            "role",
            -1,
            error="`role` is set despite type not beeing `TYPE_VEHICLE`",
        ),
        pa.Check.other_column_set_on_column_value(
            "type",
            int(betterosi.MovingObjectType.TYPE_VEHICLE),
            "subtype",
            -1,
            error="`subtype` is `-1` despite type beeing `TYPE_VEHICLE`",
        ),
        pa.Check.other_column_unset_on_column_value(
            "type",
            int(betterosi.MovingObjectType.TYPE_VEHICLE),
            "subtype",
            -1,
            error="`subtype` is set despite type not beeing `TYPE_VEHICLE`",
        ),
        pa.Check.check_has_no_frame_skip(error="Some objects skip frames during their etistence."),
    ],
)


def timestamp2ts(timestamp: betterosi.Timestamp):
    return timestamp.seconds * 1_000_000_000 + timestamp.nanos


def nearest_interp(xi, x, y):
    # https://stackoverflow.com/a/21003629
    idx = np.abs(x - xi[:, None])
    return y[idx.argmin(axis=1)]


class MovingObject:
    def __init__(self, recording, idx):
        super().__init__()
        self.idx = int(idx)
        self._recording = recording
        self._df = self._recording._df.filter(idx=self.idx)
        self._mv_df = self._recording._mv_df.filter(idx=self.idx)

    @property
    def df(self):
        return self._df

    @property
    def polygon(self):
        if "polygon" not in self._df.columns:
            self._recording._add_polygons_to_df()
            self._df = self._recording._df.filter(pl.col("idx") == self.idx)
        return self._df["polygon"]

    @property
    def nanos(self):
        return self._df["total_nanos"]

    def plot(self, ax: plt.Axes | None = None):
        if ax is None:
            fig, ax = plt.subplots(1, 1)
            ax.set_aspect(1)
        ax.plot(self.x, self.y, label=str(self.idx), c="red", alpha=0.5)

    def plot_mv_frame(self, ax: plt.Axes, frame: int):
        if "polygon" not in self._df.columns:
            self._recording._add_polygons_to_df()
        polys = self._df.filter(pl.col("frame") == frame)["polygon"]
        for p in polys:
            ax.add_patch(PltPolygon(p.exterior.coords, fc="red", alpha=0.2))

    def __getattr__(self, k):
        try:
            return self._mv_df[k].first()
        except:
            try:
                return self._df[k]
            except:
                return self._df[k[:-1]]


class Recording:
    _MovingObjectClass: typing.ClassVar = MovingObject

    @staticmethod
    def _add_polygons(df):
        if "polygon" not in df.columns:
            ar = (
                df[:]
                .select(
                    (
                        pl.col("x")
                        + (+pl.col("length") / 2) * pl.col("yaw").cos()
                        - (+pl.col("width") / 2) * pl.col("yaw").sin()
                    ).alias("x1"),
                    (
                        pl.col("x")
                        + (+pl.col("length") / 2) * pl.col("yaw").cos()
                        - (-pl.col("width") / 2) * pl.col("yaw").sin()
                    ).alias("x2"),
                    (
                        pl.col("x")
                        + (-pl.col("length") / 2) * pl.col("yaw").cos()
                        - (-pl.col("width") / 2) * pl.col("yaw").sin()
                    ).alias("x3"),
                    (
                        pl.col("x")
                        + (-pl.col("length") / 2) * pl.col("yaw").cos()
                        - (+pl.col("width") / 2) * pl.col("yaw").sin()
                    ).alias("x4"),
                    (
                        pl.col("y")
                        + (+pl.col("length") / 2) * pl.col("yaw").sin()
                        + (+pl.col("width") / 2) * pl.col("yaw").cos()
                    ).alias("y1"),
                    (
                        pl.col("y")
                        + (+pl.col("length") / 2) * pl.col("yaw").sin()
                        + (-pl.col("width") / 2) * pl.col("yaw").cos()
                    ).alias("y2"),
                    (
                        pl.col("y")
                        + (-pl.col("length") / 2) * pl.col("yaw").sin()
                        + (-pl.col("width") / 2) * pl.col("yaw").cos()
                    ).alias("y3"),
                    (
                        pl.col("y")
                        + (-pl.col("length") / 2) * pl.col("yaw").sin()
                        + (+pl.col("width") / 2) * pl.col("yaw").cos()
                    ).alias("y4"),
                )
                .to_numpy()
            )
            polys = shapely.polygons(np.stack([ar[:, :4], ar[:, 4:]], axis=2))
            df = df.with_columns(pl.Series(name="polygon", values=polys))
        return df

    def _add_polygons_to_df(self):
        self._df = self._add_polygons(self._df)

    @staticmethod
    def get_moving_object_ground_truth(
        nanos: int, df: pl.DataFrame, host_vehicle_idx: int | None = None, validate: bool = False
    ) -> betterosi.GroundTruth:
        if validate:
            recording_moving_object_schema.validate(df, lazy=True)

        def get_object(row):
            return betterosi.MovingObject(
                id=betterosi.Identifier(value=row["idx"]),
                type=betterosi.MovingObjectType(row["type"]),
                base=betterosi.BaseMoving(
                    dimension=betterosi.Dimension3D(length=row["length"], width=row["width"], height=row["width"]),
                    position=betterosi.Vector3D(x=row["x"], y=row["y"], z=row["z"]),
                    orientation=betterosi.Orientation3D(roll=row["roll"], pitch=row["pitch"], yaw=row["yaw"]),
                    velocity=betterosi.Vector3D(x=row["vel_x"], y=row["vel_y"], z=row["vel_z"]),
                    acceleration=betterosi.Vector3D(x=row["acc_x"], y=row["acc_y"], z=row["acc_z"]),
                ),
                vehicle_classification=betterosi.MovingObjectVehicleClassification(
                    type=row["subtype"], role=row["role"]
                ),
            )

        mvs = [get_object(r) for r in df.iter_rows(named=True)]
        gt = betterosi.GroundTruth(
            version=betterosi.InterfaceVersion(version_major=3, version_minor=7, version_patch=9),
            timestamp=betterosi.Timestamp(seconds=int(nanos // int(1e9)), nanos=int(nanos % int(1e9))),
            host_vehicle_id=betterosi.Identifier(value=0)
            if host_vehicle_idx is None
            else betterosi.Identifier(value=host_vehicle_idx),
            moving_object=mvs,
        )
        return gt

    def __init__(
        self,
        df,
        map=None,
        projections=None,
        host_vehicle_idx: int | None = None,
        validate=False,
        compute_polygons=False,
        traffic_light_states: dict | None = None,
    ):
        # Convert pandas DataFrame to polars DataFrame if necessary
        if isinstance(df, pd.DataFrame):
            df = pl.DataFrame(df, schema_overrides=polars_schema)
        if "total_nanos" not in df.columns:
            raise ValueError("df must contain column `total_nanos`.")
        nanos2frame = {n: i for i, n in enumerate(df["total_nanos"].unique())}
        mapping = pl.DataFrame(
            {"total_nanos": list(nanos2frame.keys()), "frame": list(nanos2frame.values())},
            schema=dict(total_nanos=polars_schema["total_nanos"], frame=pl.UInt32),
        )
        if "frame" in df.columns:
            df = df.drop("frame")
        df = df.join(mapping, on="total_nanos", how="left")
        if not isinstance(df, pl.DataFrame):
            df = pl.DataFrame(df, schema_overrides=polars_schema)
        if validate:
            recording_moving_object_schema.validate(df, lazy=True)

        super().__init__()
        self.nanos2frame = nanos2frame

        if "polygon" not in df.columns and compute_polygons:
            df = self._add_polygons(df)
        if "vel" not in df.columns:
            df = df.with_columns((pl.col("vel_x") ** 2 + pl.col("vel_y") ** 2).sqrt().alias("vel"))
        if "acc" not in df.columns:
            df = df.with_columns((pl.col("acc_x") ** 2 + pl.col("acc_y") ** 2).sqrt().alias("acc"))
        self.projections = projections if projections is not None else []
        self.traffic_light_states = traffic_light_states if traffic_light_states is not None else {}

        self._df = df
        self.map = map
        self._moving_objects = None
        self.host_vehicle_idx = host_vehicle_idx

    @property
    def df(self):
        return self._df

    @property
    def host_vehicle(self):
        return self.moving_objects.get(self.host_vehicle_idx, None)

    @property
    def moving_objects(self):
        if self._moving_objects is None:
            self._mv_df = (
                self._df.group_by("idx")
                .agg(
                    pl.col("length", "width", "height").mean(),
                    pl.col("type", "subtype", "role").median(),
                    pl.col("frame").min().alias("birth"),
                    pl.col("frame").max().alias("end"),
                    pl.col("total_nanos").min().alias("t_birth"),
                    pl.col("total_nanos").max().alias("t_end"),
                )
                .with_columns(
                    pl.col("type").map_elements(lambda x: betterosi.MovingObjectType(x), return_dtype=object),
                    pl.col("subtype").map_elements(
                        lambda x: betterosi.MovingObjectVehicleClassificationType(x) if x != -1 else None,
                        return_dtype=object,
                    ),
                    pl.col("role").map_elements(
                        lambda x: betterosi.MovingObjectVehicleClassificationRole(x).name if x != -1 else None,
                        return_dtype=object,
                    ),
                )
            )

            self._moving_objects = {int(idx): self._MovingObjectClass(self, idx) for idx in self._df["idx"].unique()}

        return self._moving_objects

    def to_osi_gts(self) -> list[betterosi.GroundTruth]:
        first_iteration = True
        for [nanos], group_df in self._df.sort(["total_nanos"]).group_by("total_nanos", maintain_order=True):
            gt = self.get_moving_object_ground_truth(
                nanos, group_df, host_vehicle_idx=self.host_vehicle_idx, validate=False
            )
            if first_iteration:
                first_iteration = False
                if self.map is not None and isinstance(self.map, MapOsi | MapOsiCenterline):
                    gt.lane_boundary = [b._osi for b in self.map.lane_boundaries.values()]
                    gt.lane = [l._osi for l in self.map.lanes.values()]
            if nanos in self.traffic_light_states:
                gt.traffic_light = self.traffic_light_states[nanos]
            yield gt

    @classmethod
    def from_osi_gts(cls, gts: list[betterosi.GroundTruth], **kwargs):
        projs = []
        traffic_light_states = {}

        gts, tmp_gts = itertools.tee(gts, 2)
        first_gt = next(tmp_gts)
        if first_gt.host_vehicle_id is not None:
            host_vehicle_idx = first_gt.host_vehicle_id.value
        else:
            host_vehicle_idx = None

        def get_gts():
            for i, gt in enumerate(gts):
                total_nanos = gt.timestamp.seconds * 1_000_000_000 + gt.timestamp.nanos
                if gt.proj_frame_offset is not None and gt.proj_frame_offset.position is None:
                    raise ValueError(
                        f"Offset of {i}th ground truth message (total_nanos={total_nanos}) is set without position."
                    )
                projs.append(
                    dict(
                        proj_string=gt.proj_string,
                        offset=ProjectionOffset(
                            x=gt.proj_frame_offset.position.x,
                            y=gt.proj_frame_offset.position.y,
                            z=gt.proj_frame_offset.position.z,
                            yaw=gt.proj_frame_offset.yaw,
                        )
                        if gt.proj_frame_offset is not None
                        else None,
                    )
                )

                traffic_light_states[total_nanos] = gt.traffic_light

                for mv in gt.moving_object:
                    yield dict(
                        total_nanos=total_nanos,
                        idx=mv.id.value,
                        x=mv.base.position.x,
                        y=mv.base.position.y,
                        z=mv.base.position.z,
                        vel_x=mv.base.velocity.x,
                        vel_y=mv.base.velocity.y,
                        vel_z=mv.base.velocity.z,
                        acc_x=mv.base.acceleration.x,
                        acc_y=mv.base.acceleration.y,
                        acc_z=mv.base.acceleration.z,
                        length=mv.base.dimension.length,
                        width=mv.base.dimension.width,
                        height=mv.base.dimension.height,
                        roll=mv.base.orientation.roll,
                        pitch=mv.base.orientation.pitch,
                        yaw=mv.base.orientation.yaw,
                        type=mv.type,
                        role=mv.vehicle_classification.role
                        if mv.type == betterosi.MovingObjectType.TYPE_VEHICLE
                        else -1,
                        subtype=mv.vehicle_classification.type
                        if mv.type == betterosi.MovingObjectType.TYPE_VEHICLE
                        else -1,
                    )

        df_mv = pl.DataFrame(get_gts(), schema=polars_schema).sort(["total_nanos", "idx"])
        return cls(
            df_mv,
            projections=projs,
            host_vehicle_idx=host_vehicle_idx,
            traffic_light_states=traffic_light_states,
            **kwargs,
        )

    @classmethod
    def from_file(
        cls,
        filepath,
        xodr_path: str | None = None,
        validate: bool = False,
        parse_map: bool = False,
        compute_polygons: bool = False,
        step_size: float = 0.01,
    ):
        if Path(filepath).suffix == ".parquet":
            return cls.from_parquet(
                filepath, parse_map=parse_map, validate=validate, compute_polygons=compute_polygons, step_size=step_size
            )

        gts = betterosi.read(filepath, return_ground_truth=True, mcap_return_betterosi=True)
        gts, tmp_gts = itertools.tee(gts, 2)
        first_gt = next(tmp_gts)
        r = cls.from_osi_gts(gts, validate=validate, compute_polygons=compute_polygons)
        if xodr_path is not None:
            r.map = MapOdr.from_file(xodr_path, parse=parse_map)
        elif Path(filepath).suffix == ".mcap":
            try:
                r.map = MapOdr.from_file(filepath, parse=parse_map)
            except StopIteration:
                pass
        if r.map is None:
            try:
                r.map = MapOsi.create(first_gt)
                warn("No map provided in mcap. OSI GroundTruth map is used!")
            except RuntimeError:
                try:
                    r.map = MapOsiCenterline.create(first_gt)
                    warn("No map provided in mcap. OSI GroundTruth (Centerline) map is used!")
                except RuntimeError:
                    pass
        if r.map is None:
            warn("No xodr map provided in MCAP nor OSI map in GroundTruth!")
        return r

    def to_mcap(self, filepath):
        if Path(filepath).suffix != ".mcap":
            raise ValueError()
        with betterosi.Writer(filepath) as w:
            for gt in self.to_osi_gts():
                w.add(gt)
            if isinstance(self.map, MapOdr):
                w.add(self.map.to_osi(), topic="ground_truth_map", log_time=0)

    def to_hdf(self, filename, key="moving_object"):
        #!pip install tables
        to_drop = [] if "polygon" not in self._df.columns else ["polygon"]
        to_drop += ["frame"]
        self._df.drop(columns=to_drop).to_pandas().to_hdf(filename, key=key)

    @classmethod
    def from_hdf(cls, filename, key="moving_object"):
        df = pl.DataFrame(pd.read_hdf(filename, key=key), schema_overrides=polars_schema)
        return cls(df, map=None, host_vehicle_idx=None)

    def interpolate(self, new_nanos: list[int] | None = None, hz: float | None = None):
        df = self._df
        nanos_min, nanos_max, frame_min, frame_max = df.select(
            nanos_min=pl.col("total_nanos").min(),
            nanos_max=pl.col("total_nanos").max(),
            frame_min=pl.col("frame").min(),
            frame_max=pl.col("frame").max(),
        ).row(0)
        if new_nanos is None:
            if hz is None:
                new_nanos = np.linspace(nanos_min, nanos_max, frame_max - frame_min, dtype=int)
            else:
                step = 1e9 / hz
                new_nanos = np.arange(start=nanos_min, stop=nanos_max + 1, step=step, dtype=int)
        else:
            new_nanos = np.array(new_nanos)
        new_dfs = []
        for [idx], track_df in df.group_by("idx"):
            track_data = {}
            track_new_nanos = new_nanos[
                np.logical_and(track_df["total_nanos"].min() <= new_nanos, track_df["total_nanos"].max() >= new_nanos)
            ]
            for c in ["x", "y", "z", "vel_x", "vel_y", "vel_z", "acc_x", "acc_y", "acc_z", "length", "width", "height"]:
                track_data[c] = np.interp(track_new_nanos, track_df["total_nanos"], track_df[c])
            for c in ["type", "subtype", "role"]:
                track_data[c] = nearest_interp(
                    track_new_nanos, track_df["total_nanos"].to_numpy(), track_df[c].to_numpy()
                )
            for c in ["roll", "pitch", "yaw"]:
                # Unwrap angles to handle discontinuities, then interpolate, then wrap back to [-π, π]
                unwrapped_angles = np.unwrap(track_df[c])
                interpolated = np.interp(track_new_nanos, track_df["total_nanos"], unwrapped_angles)
                track_data[c] = np.mod(interpolated + np.pi, 2 * np.pi) - np.pi
            new_track_df = pl.DataFrame(track_data)
            new_track_df = new_track_df.with_columns(
                pl.Series(name="idx", values=np.ones_like(track_new_nanos) * idx, dtype=polars_schema["idx"]),
                pl.Series(name="total_nanos", values=track_new_nanos, dtype=polars_schema["total_nanos"]),
            )
            new_dfs.append(new_track_df)
        new_df = pl.concat(new_dfs)
        return self.__init__(df=new_df, map=self.map, host_vehicle_idx=self.host_vehicle_idx)

    def plot(self, ax=None, legend=False) -> plt.Axes:
        if ax is None:
            fig, ax = plt.subplots(1, 1)
            ax.set_aspect(1)
        if self.map:
            self.map.plot(ax)
        self.plot_mvs(ax=ax)
        self.plot_tl(ax=ax)
        if legend:
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        return ax

    def plot_mvs(self, ax=None, legend=False):
        if ax is None:
            fig, ax = plt.subplots(1, 1)
            ax.set_aspect(1)
        for [idx], mv in self._df["idx", "x", "y"].group_by("idx"):
            ax.plot(*mv["x", "y"], c="red", alpha=0.5, label=str(idx))
        if legend:
            ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        return ax

    def plot_tl(self, ax=None):
        if ax is None:
            fig, ax = plt.subplots(1, 1)
            ax.set_aspect(1)
        tl_dict = {}
        for tl_states in self.traffic_light_states:
            for tl in self.traffic_light_states[tl_states]:
                if tl.id.value not in tl_dict.keys():
                    tl_dict[tl.id.value] = tl

        for tl in tl_dict:
            try:
                x = tl_dict[tl].base.position.x
                y = tl_dict[tl].base.position.y
                ax.plot(
                    x, y, marker="o", label=f"Traffic Light {tl_dict[tl].id.value}", c="blue", alpha=0.7, markersize=2
                )
            except AttributeError as e:
                print(f"Warning: Skipping traffic light {tl.id.value} due to missing position data: {e}")
                continue
        return ax

    def plot_frame(self, frame: int, ax=None):
        ax = self.plot(ax=ax)
        self.plot_mv_frame(ax, frame=frame)
        return ax

    def plot_mv_frame(self, ax: plt.Axes, frame: int):
        if "polygon" not in self._df.columns:
            self._add_polygons_to_df()
        polys = self._df.filter(pl.col("frame") == frame)["polygon"]
        for p in polys:
            ax.add_patch(PltPolygon(p.exterior.coords, fc="red"))

    @classmethod
    def from_parquet(cls, filename, parse_map: bool = False, step_size: float = 0.01, **kwargs):
        t = pq.read_table(filename)
        df = pl.DataFrame(t, schema_overrides=polars_schema)
        m = None
        host_vehicle_idx = None
        if t.schema.metadata is not None:
            if b"host_vehicle_idx" in t.schema.metadata:
                host_vehicle_idx = int(t.schema.metadata[b"host_vehicle_idx"].decode())
            if b"xodr" in t.schema.metadata:
                m = MapOdr.create(
                    odr_xml=t.schema.metadata[b"xodr"].decode(),
                    name=t.schema.metadata[b"xodr_name"].decode(),
                    parse=parse_map,
                    step_size=step_size,
                )
            elif b"osi" in t.schema.metadata:
                gt = betterosi.GroundTruth().from_json(t.schema.metadata[b"osi"].decode())
                if len(gt.lane_boundary) > 0:
                    m = MapOsi.create(gt)
                else:
                    m = MapOsiCenterline.create(gt)
        return cls(df, map=m, host_vehicle_idx=host_vehicle_idx, **kwargs)

    def to_parquet(self, filename):
        metadata = {}
        if self.host_vehicle_idx is not None:
            metadata[b"host_vehicle_idx"] = str(self.host_vehicle_idx).encode()
        if len(self.projections) > 0:
            proj_meta = {
                b"proj_string": self.projections[0]["proj_string"],
            }
            if self.projections[0]["offset"] is not None:
                proj_meta[b"offset_x"] = str(self.projections[0]["offset"].x).encode()
                proj_meta[b"offset_y"] = str(self.projections[0]["offset"].y).encode()
                proj_meta[b"offset_z"] = str(self.projections[0]["offset"].z).encode()
                proj_meta[b"offset_yaw"] = str(self.projections[0]["offset"].yaw).encode()

        else:
            proj_meta = {}
        to_drop = ["frame"]
        if "polygon" in self._df.columns:
            to_drop.append("polygon")
        t = pyarrow.table(self._df.drop(*to_drop))
        map_meta = {}
        if hasattr(self.map, "odr_xml"):
            map_meta = {b"xodr": self.map.odr_xml.encode(), b"xodr_name": self.map.name.encode()}
        elif hasattr(self.map, "_osi"):
            d = json.loads(self.map._osi.to_json())
            if "movingObject" in d:
                del d["movingObject"]
            map_meta = {b"osi": json.dumps(d).encode()}

        t = t.cast(t.schema.with_metadata(metadata | proj_meta | map_meta))
        pq.write_table(t, filename)

    def plot_altair(
        self,
        start_frame=0,
        end_frame=-1,
        plot_map=True,
        plot_map_polys=True,
        metric_column=None,
        plot_wedges=True,
        idx=None,
        height=None,
        width=None,
    ):
        if "polygon" not in self._df.columns:
            self._df = self._add_polygons(self._df)
        if "geometry" not in self._df.columns:
            self._df = self._df.with_columns(geometry=st.from_shapely("polygon"))

        if end_frame != -1:
            df = self._df.filter(pl.col("frame") < end_frame, pl.col("frame") >= start_frame)
        else:
            df = self._df.filter(pl.col("frame") >= start_frame)

        [frame_min], [frame_max] = df.select(
            pl.col("frame").min().alias("min"),
            pl.col("frame").max().alias("max"),
        )[0]
        slider = alt.binding_range(min=frame_min, max=frame_max, step=1, name="frame")
        op_var = alt.param(value=0, bind=slider)

        df = df.with_columns(
            pl.concat_str(
                pl.col("type").map_elements(lambda x: betterosi.MovingObjectType(x).name, return_dtype=pl.String),
                pl.col("subtype").map_elements(
                    lambda x: betterosi.MovingObjectVehicleClassificationType(x).name,
                    return_dtype=pl.String,
                ),
                separator="-",
            ).alias("type")
        )
        buffer = pl.col("length").max()
        xmin, xmax, ymin, ymax = df.select(
            (pl.col("x").min() - buffer).alias("xmin"),
            (pl.col("x").max() + buffer).alias("xmax"),
            (pl.col("y").min() - buffer).alias("ymin"),
            (pl.col("y").max() + buffer).alias("ymax"),
        ).row(0)
        pov_df = pl.DataFrame({"polygon": [shapely.Polygon([[xmax, ymax], [xmax, ymin], [xmin, ymin], [xmin, ymax]])]})
        pov_df = pov_df.select(geometry=st.from_shapely("polygon"))
        pov = alt.Chart({"values": pov_df.st.to_dicts()}).mark_geoshape(fillOpacity=0, filled=False, opacity=0)

        plots = [pov]
        if plot_map and self.map is not None:
            plots.append(self.map.plot_altair(recording=self, plot_polys=plot_map_polys))

        mv_dict = {"values": df["geometry", "idx", "frame", "type"].st.to_dicts()}
        plots.append(
            alt.Chart(mv_dict)
            .mark_geoshape()
            .encode(
                color=(
                    alt.when(alt.FieldEqualPredicate(equal=self.host_vehicle_idx or -1, field="properties.idx"))
                    .then(alt.value("red"))
                    .when(alt.FieldEqualPredicate(equal=-1 if idx is None else idx, field="properties.idx"))
                    .then(alt.value("red"))
                    .otherwise(alt.value("blue"))
                ),
                tooltip=["properties.idx:N", "properties.frame:N", "properties.type:O"],
            )
            .transform_filter(alt.FieldEqualPredicate(field="properties.frame", equal=op_var))
        )
        if plot_wedges:
            wedges_df = df["idx", "frame", "type", "x", "y", "yaw", "length"].with_columns(
                pl.col("yaw").degrees().alias("deg"), (pl.col("length") / 4).alias("size")
            )
            plots.append(
                alt.Chart(wedges_df)
                .mark_point(shape="wedge", color="white", strokeWidth=2)
                .encode(
                    alt.Longitude("x:Q"),
                    alt.Latitude("y:Q"),
                    alt.Angle("deg").scale(domain=[180, -180], range=[-90, 270]),
                    alt.Size("size", legend=None),
                    tooltip=["idx:N", "frame:N", "type:O"],
                )
                .transform_filter(alt.FieldEqualPredicate(field="frame", equal=op_var))
            )

        view = (
            alt.layer(*plots)
            .properties(
                title="Map",
                **({"height": height} if height is not None else {}),
                **({"width": width} if width is not None else {}),
            )
            .project("identity", reflectY=True)
        )

        if metric_column is not None and idx is not None:
            metric = (
                df["idx", metric_column, "frame"]
                .filter(idx=idx)
                .plot.line(x="frame", y=metric_column, color=alt.value("red"))
                .properties(title=f"{metric_column} of object {idx}")
            )
            vertline = (
                alt.Chart()
                .mark_rule()
                .encode(x=alt.datum(op_var, type="quantitative", scale=alt.Scale(domain=[frame_min, frame_max])))
            )
            view = view | (metric + vertline)
        return view.add_params(op_var)
        if "polygon" not in self._df.columns:
            self._df = self._add_polygons(self._df)
        if "geometry" not in self._df.columns:
            self._df = self._df.with_columns(geometry=st.from_shapely("polygon"))

        if end_frame != -1:
            df = self._df.filter(pl.col("frame") < end_frame, pl.col("frame") >= start_frame)
        else:
            df = self._df.filter(pl.col("frame") >= start_frame)

        [frame_min], [frame_max] = df.select(
            pl.col("frame").min().alias("min"),
            pl.col("frame").max().alias("max"),
        )[0]
        slider = alt.binding_range(min=frame_min, max=frame_max, step=1, name="frame")
        op_var = alt.param(value=0, bind=slider)

        df = df.with_columns(
            pl.concat_str(
                pl.col("type").map_elements(lambda x: betterosi.MovingObjectType(x).name, return_dtype=pl.String),
                pl.col("subtype").map_elements(
                    lambda x: betterosi.MovingObjectVehicleClassificationType(x).name,
                    return_dtype=pl.String,
                ),
                separator="-",
            ).alias("type")
        )
        mv_dict = {"values": df["geometry", "idx", "frame", "type"].st.to_dicts()}
        if plot_wedges:
            wedges_df = df["idx", "frame", "type", "x", "y", "yaw", "length"].with_columns(
                pl.col("yaw").degrees().alias("deg"), (pl.col("length") / 4).alias("size")
            )
            plots.append(
                alt.Chart(wedges_df)
                .mark_point(shape="wedge", color="white", strokeWidth=2)
                .encode(
                    alt.Longitude("x:Q"),
                    alt.Latitude("y:Q"),
                    alt.Angle("deg").scale(domain=[180, -180], range=[-90, 270]),
                    alt.Size("size", legend=None),
                    tooltip=["idx:N", "frame:N", "type:O"],
                )
                .transform_filter(alt.FieldEqualPredicate(field="frame", equal=op_var))
            )
        view = (
            alt.layer(
                *[
                    o
                    for o in [
                        None
                        if not plot_map or self.map is None
                        else self.map.plot_altair(recording=self, plot_polys=plot_map_polys),
                        alt.Chart(mv_dict)
                        .mark_geoshape()
                        .encode(
                            color=(
                                alt.when(
                                    alt.FieldEqualPredicate(equal=self.host_vehicle_idx or -1, field="properties.idx")
                                )
                                .then(alt.value("red"))
                                .when(alt.FieldEqualPredicate(equal=-1 if idx is None else idx, field="properties.idx"))
                                .then(alt.value("red"))
                                .otherwise(alt.value("blue"))
                            ),
                            tooltip=["properties.idx:N", "properties.frame:N", "properties.type:O"],
                        )
                        .transform_filter(alt.FieldEqualPredicate(field="properties.frame", equal=op_var)),
                    ]
                    if o is not None
                ]
            )
            .properties(
                title="Map",
                **({"height": height} if height is not None else {}),
                **({"width": width} if width is not None else {}),
            )
            .project("identity", reflectY=True)
        )

        if metric_column is not None and idx is not None:
            metric = (
                df["idx", metric_column, "frame"]
                .filter(idx=idx)
                .plot.line(x="frame", y=metric_column, color=alt.value("red"))
                .properties(title=f"{metric_column} of object {idx}")
            )
            vertline = (
                alt.Chart()
                .mark_rule()
                .encode(x=alt.datum(op_var, type="quantitative", scale=alt.Scale(domain=[frame_min, frame_max])))
            )
            view = view | (metric + vertline)
        return view.add_params(op_var)
