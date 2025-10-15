# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------


from __future__ import annotations

from qai_hub_models.models._shared.llm.export import export_main
from qai_hub_models.models.common import Precision, TargetRuntime
from qai_hub_models.models.llama_v3_1_sea_lion_3_5_8b_r import (
    MODEL_ID,
    FP_Model,
    Model,
    PositionProcessor,
)
from qai_hub_models.models.llama_v3_1_sea_lion_3_5_8b_r.model import (
    DEFAULT_PRECISION,
    MODEL_ASSET_VERSION,
    NUM_LAYERS_PER_SPLIT,
    NUM_SPLITS,
)

DEFAULT_EXPORT_DEVICE = "Snapdragon 8 Elite QRD"

SUPPORTED_PRECISION_RUNTIMES = {
    Precision.w4a16: [
        TargetRuntime.GENIE,
        TargetRuntime.ONNXRUNTIME_GENAI,
    ]
}


def main():
    export_main(
        MODEL_ID,
        MODEL_ASSET_VERSION,
        SUPPORTED_PRECISION_RUNTIMES,
        NUM_SPLITS,
        NUM_LAYERS_PER_SPLIT,
        Model,
        FP_Model,
        PositionProcessor,
        DEFAULT_EXPORT_DEVICE,
        DEFAULT_PRECISION,
    )


if __name__ == "__main__":
    main()
