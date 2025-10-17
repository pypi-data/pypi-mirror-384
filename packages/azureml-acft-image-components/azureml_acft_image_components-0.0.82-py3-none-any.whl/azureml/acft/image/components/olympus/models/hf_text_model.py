# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import torch
from torch import nn
from transformers import AutoConfig, AutoModelForCausalLM
from typing import Optional
from peft import LoraConfig, get_peft_model  # Required for LoRA support

class HFTextModel(nn.Module):
    def __init__(
        self,
        model_name_or_path: str,
        lora_config: Optional[LoraConfig] = None,
        **kwargs,
    ):
        """
        Initializes the text model.

        Args:
            model_name_or_path (str): Pretrained model name or path.
            lora_config (Optional[LoraConfig]): LoRA configuration for fine-tuning.
            use_flash_attn (bool): Whether to enable flash attention via config.
            **kwargs: Additional arguments for model initialization.
        """
        super().__init__()

        # Load model config
        config = AutoConfig.from_pretrained(model_name_or_path)
        print("Initializing model with config")


        print(config)
        print(kwargs)


        # Load model with updated config
        self.language_model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            config=config,
            **kwargs,
        )

        # Apply LoRA if provided
        if lora_config:
            print("Applying LoRA configuration.")
            self.language_model = get_peft_model(self.language_model, lora_config)

    def forward(self, inputs: dict) -> torch.Tensor:
        input_ids = inputs.get("input_ids")
        attention_mask = inputs.get("attention_mask", None)
        labels = inputs.get("labels", None)
        return_dict = inputs.get("return_dict", True)

        if input_ids is None:
            raise ValueError("input_ids is a required input.")

        # Debugging input shape if needed
        # print(f"Forward pass input shape: {input_ids.shape}")

        outputs = self.language_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
            output_hidden_states=False,
            return_dict=return_dict,
        )

        logits = outputs.logits

        if labels is not None:
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous().to(shift_logits.device)
            logits = shift_logits
            labels = shift_labels

        logits = logits.permute(0, 2, 1)

        return (logits, labels) if labels is not None else logits
