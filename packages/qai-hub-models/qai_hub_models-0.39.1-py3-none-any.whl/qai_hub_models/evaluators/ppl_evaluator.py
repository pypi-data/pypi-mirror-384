# ---------------------------------------------------------------------
# Copyright (c) 2025 Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
# ---------------------------------------------------------------------

from __future__ import annotations

import math
from collections.abc import Callable
from typing import TYPE_CHECKING

import torch
from torch.nn import CrossEntropyLoss
from tqdm import tqdm

from qai_hub_models.evaluators.base_evaluators import (
    BaseEvaluator,
    MetricMetadata,
    _DataLoader,
)

if TYPE_CHECKING:
    from transformers import PreTrainedTokenizer
    from transformers.modeling_outputs import CausalLMOutputWithPast

    from qai_hub_models.models._shared.llm.generator import LLM_Generator


class PerplexityEvaluator(BaseEvaluator):
    """Evaluator for computing PPL of a Large Language Model.
    This may not be as generic as hoped and may need work. Works with Llama 3.2 3B.

    """

    def __init__(
        self,
        context_length: int,
        device: torch.device,
        tokenizer: PreTrainedTokenizer,
    ):
        self.context_length = context_length
        self.device = device
        self.tokenizer = tokenizer

        self.reset()

    def add_batch(self, output: CausalLMOutputWithPast, gt: torch.Tensor):
        self.batch_index += 1
        logits = output.logits
        assert logits is not None
        # This kv cache is needed to maintain the context between multiple blocks.
        lm_logits = logits.reshape(1, -1, logits.shape[-1])
        shift_logits = lm_logits[..., :-1, :].contiguous().to(dtype=torch.float32)
        shift_labels = gt[..., 1:].contiguous().to(shift_logits.device)
        loss_fct = CrossEntropyLoss()
        loss_value = loss_fct(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
        ).item()
        self.loss += loss_value

    def reset(self):
        self.loss = 0.0
        self.batch_index = 0

    def get_accuracy_score(self) -> float:
        average_loss = self.loss / self.batch_index
        return math.exp(average_loss)

    def formatted_accuracy(self) -> str:
        return f"PPL (lower is better): {self.get_accuracy_score():.2f}"

    def for_each_batch(
        self,
        generator: LLM_Generator,
        data: _DataLoader,
        num_samples: int | None = None,
        callback: (
            Callable[[list[torch.Tensor], CausalLMOutputWithPast, torch.Tensor], None]
            | None
        ) = None,
    ) -> None:
        total_samples = 0
        batch_size = 1
        num_samples = num_samples or len(data)
        with tqdm(
            total=num_samples,
            desc="Number of samples completed",
        ) as pbar:
            for sample in data:
                input_ids, attention_mask, ground_truth = sample  # type:ignore[misc]
                inputs = [input_ids, attention_mask]
                inputs = [inp.to(self.device) for inp in inputs]
                outputs = generator(*inputs)
                if callback:
                    callback(inputs, outputs, ground_truth)
                total_samples += 1
                pbar.update(batch_size)
                if total_samples >= num_samples:
                    break

    def add_from_dataset(
        self,
        generator: LLM_Generator,
        data: _DataLoader,
        eval_iterations: int | None = None,
    ) -> None:
        def _add_batch(
            _: list[torch.Tensor],
            outputs: CausalLMOutputWithPast,
            ground_truth: torch.Tensor,
        ):
            self.add_batch(outputs, ground_truth)

        self.for_each_batch(generator, data, eval_iterations, _add_batch)

    def get_metric_metadata(self) -> MetricMetadata:
        return MetricMetadata(
            name="Perplexity",
            unit="PPL",
            description="A measure of how likely the model is to predict a given sequence of words. Lower is better.",
        )
