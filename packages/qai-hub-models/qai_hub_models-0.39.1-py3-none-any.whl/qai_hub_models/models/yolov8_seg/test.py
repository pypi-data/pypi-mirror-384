# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------

from typing import cast

import numpy as np
import pytest
import torch
from ultralytics.models import YOLO as ultralytics_YOLO
from ultralytics.nn.tasks import SegmentationModel

from qai_hub_models.models._shared.yolo.app import YoloSegmentationApp
from qai_hub_models.models._shared.yolo.model import yolo_segment_postprocess
from qai_hub_models.models.yolov8_seg.demo import IMAGE_ADDRESS
from qai_hub_models.models.yolov8_seg.demo import main as demo_main
from qai_hub_models.models.yolov8_seg.model import (
    MODEL_ASSET_VERSION,
    MODEL_ID,
    YoloV8Segmentor,
)
from qai_hub_models.utils.asset_loaders import CachedWebModelAsset, load_image
from qai_hub_models.utils.image_processing import preprocess_PIL_image
from qai_hub_models.utils.set_env import set_temp_env
from qai_hub_models.utils.testing import assert_most_close

WEIGHTS = "yolov8n-seg.pt"
OUTPUT_IMAGE_ADDRESS = CachedWebModelAsset.from_asset_store(
    MODEL_ID, MODEL_ASSET_VERSION, "test_images/out_bus_with_mask.png"
)


def test_task() -> None:
    """Verify that raw (numeric) outputs of both (QAIHM and non-qaihm) networks are the same."""
    # Set the environment variable to force torch.load to use weights_only=False
    # This is needed for PyTorch 2.8+ where the default changed to weights_only=True
    with set_temp_env({"TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD": "1"}):
        source_model = cast(SegmentationModel, ultralytics_YOLO(WEIGHTS).model)
    qaihm_model = YoloV8Segmentor.from_pretrained(WEIGHTS)
    qaihm_app = YoloSegmentationApp(qaihm_model)
    processed_sample_image = preprocess_PIL_image(load_image(IMAGE_ADDRESS))
    processed_sample_image = qaihm_app.preprocess_input(processed_sample_image)

    with torch.no_grad():
        # original model output
        source_out = source_model(processed_sample_image)
        source_out_postprocessed = yolo_segment_postprocess(
            source_out[0], qaihm_model.num_classes
        )
        source_out = [*source_out_postprocessed, source_out[1][-1]]

        # Qualcomm AI Hub Model output
        qaihm_out_postprocessed = qaihm_model(processed_sample_image)
        for i in range(0, len(source_out_postprocessed)):
            assert np.allclose(source_out_postprocessed[i], qaihm_out_postprocessed[i])


@pytest.mark.trace
def test_trace() -> None:
    net = YoloV8Segmentor.from_pretrained(WEIGHTS)
    input_spec = net.get_input_spec()
    trace = net.convert_to_torchscript(input_spec, check_trace=False)

    # Collect output via app for traced model
    img = load_image(IMAGE_ADDRESS)
    app = YoloSegmentationApp(trace)
    out_imgs = app.predict(img)

    expected_out = load_image(OUTPUT_IMAGE_ADDRESS)
    assert_most_close(
        np.asarray(out_imgs[0], dtype=np.float32),
        np.asarray(expected_out, dtype=np.float32),
        0.005,
    )


def test_demo() -> None:
    # Run demo and verify it does not crash
    demo_main(is_test=True)
