# Copyright (c) 2025 Krnel
# Points of Contact:
#   - kimmy@krnel.ai

from typing import Literal

from krnel.graph.dataset_ops import TextColumnType, VectorColumnType


class LLMGenerateTextOp(TextColumnType):
    model_name: str
    prompt: TextColumnType
    max_tokens: int = 100

class LLMLayerActivationsOp(VectorColumnType):
    model_name: str
    text: TextColumnType
    """
    The prompt to get activations for. We always apply chat template.
    """

    layer_num: int
    """Supports negative indexing: -1 = last layer, -2 = second-to-last.
    Not supported for SentenceTransformers or Ollama; set to -1 for those model providers.
    """

    token_mode: Literal["last", "mean", "all"]
    """Token pooling mode.  Not supported for Ollama or SentenceTransformers."""

    batch_size: int

    max_length: int | None = None
    "Maximum number of tokens in input. Longer prompts are truncated."

    dtype: str | None = None
    "DType of both the model itself and the output embeddings."

    device: str = "auto"
    "default: 'cuda' or 'mps' if available, else 'cpu'"

    torch_compile: bool = False
    "Whether to use torch.compile for performance optimization"

class LLMLogitScoresOp(VectorColumnType):
    model_name: str
    text: TextColumnType
    "The prompt to get activations for."
    batch_size: int
    logit_token_ids: list[str | int]
    """List of tokens to get logit scores for. The output is a vector of shape ``(len(dataset), len(logit_token_ids))``.

    Logits can be either strings (to specify that token, which must exist in the vocabulary), or integers (to specify the token ID directly).
    """
    apply_chat_template: bool = True
    "Whether to apply chat template to the prompt. Default True."
    dtype: str | None = None
    "DType of both the model itself and the output scores."
    device: str = "auto"
    "default: 'cuda' or 'mps' if available, else 'cpu'"
    max_length: int | None = None
    "Maximum number of tokens in input. Longer prompts are truncated."

    torch_compile: bool = False
    "Whether to use torch.compile for performance optimization"

    append_to_chat_template: str | None = None
    """If using chat template, optionally append this string to the end of the prompt.
    This is useful for, say, guardrail models that expect newlines at the end of a system prompt."""