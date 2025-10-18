from pathlib import Path

import yaml
from pydantic import BaseModel, Field, PositiveInt


class RTMDetConfig(BaseModel):
    """Configuration for the RTMDet model"""

    # ---- Scaling  ----
    deepen_factor: float = Field(
        ...,
        gt=0.0,
        description="Scaling factor for the model depth (e.g., the number of layers or blocks)",
    )
    widen_factor: float = Field(
        ...,
        gt=0.0,
        description="Scaling factor for the model width (e.g., the number of channels or neurons)",
    )
    neck_out_channels: PositiveInt = Field(
        ...,
        description="Number of channels of the output convolution layers in the PAFPN module",
    )
    # ---- Head ---
    head_num_stacked_convs: PositiveInt = Field(
        ...,
        description="Number of convolution blocks in each classification/regression tower",
    )
    head_num_levels: PositiveInt = Field(
        ...,
        ge=1,
        description="Number of pyramid levels the head operates on (e.g., 3 for P3-P5). Must equal the number of feature maps provided by the neck",
    )
    num_classes: PositiveInt = Field(..., description="Number of classes")
    input_size: PositiveInt = Field(
        ..., description="Input image size (assumes a square input)"
    )
    # nms_iou_threshold: float = Field(
    #     0.50, ge=0.0, le=1.0,
    #     ""
    # )
    max_num_detections: int = Field(
        300, description="Maximum number of detections kept after NMS per image"
    )


def load_config(path: str | Path) -> RTMDetConfig:
    return RTMDetConfig(**yaml.safe_load(Path(path).expanduser().read_text()))
