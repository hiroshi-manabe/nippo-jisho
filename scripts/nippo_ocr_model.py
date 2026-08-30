#!/usr/bin/env python3
"""Compact convolutional recurrent CTC recognizer for Nippo Jisho lines."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


@dataclass(frozen=True)
class ModelConfig:
    cnn_channels: tuple[int, ...] = (32, 64, 128, 192)
    temporal_blocks: int = 8
    dropout: float = 0.2


class TemporalBlock(nn.Module):
    def __init__(self, channels: int, dilation: int, dropout: float) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv1d(
                channels,
                channels,
                kernel_size=3,
                padding=dilation,
                dilation=dilation,
                groups=channels,
            ),
            nn.BatchNorm1d(channels),
            nn.GELU(),
            nn.Conv1d(channels, channels, kernel_size=1),
            nn.Dropout(dropout),
        )

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        return values + self.block(values)


class LineCTC(nn.Module):
    width_reduction = 4

    def __init__(self, classes: int, config: ModelConfig = ModelConfig()) -> None:
        super().__init__()
        channels = (1,) + config.cnn_channels
        strides = ((2, 2), (2, 2), (2, 1), (2, 1))
        blocks: list[nn.Module] = []
        for source, target, stride in zip(channels, channels[1:], strides):
            blocks.extend(
                [
                    nn.Conv2d(source, target, 3, stride=stride, padding=1),
                    nn.BatchNorm2d(target),
                    nn.GELU(),
                ]
            )
        self.cnn = nn.Sequential(*blocks)
        dilations = (1, 2, 4, 8)
        self.sequence = nn.Sequential(
            *[
                TemporalBlock(
                    config.cnn_channels[-1],
                    dilations[index % len(dilations)],
                    config.dropout,
                )
                for index in range(config.temporal_blocks)
            ]
        )
        self.classifier = nn.Linear(config.cnn_channels[-1], classes)
        # A randomly initialized CTC model otherwise converges very easily to
        # emitting only blanks on this small historical corpus.
        with torch.no_grad():
            self.classifier.bias.zero_()
            self.classifier.bias[0] = -2.0
        self.config = config

    def output_lengths(self, widths: torch.Tensor) -> torch.Tensor:
        return torch.div(widths + 3, 4, rounding_mode="floor")

    def forward(
        self, images: torch.Tensor, widths: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        features = self.cnn(images).mean(dim=2)
        lengths = self.output_lengths(widths)
        encoded = self.sequence(features).transpose(1, 2)
        return self.classifier(encoded), lengths
