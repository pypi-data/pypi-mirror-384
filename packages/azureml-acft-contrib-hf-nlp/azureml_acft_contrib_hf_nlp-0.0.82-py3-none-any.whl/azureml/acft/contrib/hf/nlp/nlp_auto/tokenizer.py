# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

"""
File containing HF tokenizer related functions
"""

from typing import Dict, Any

from transformers import AutoTokenizer, PreTrainedTokenizerBase

from ..constants.constants import HfModelTypes, HfConstants
from .config import AzuremlAutoConfig

from azureml.acft.common_components import get_logger_app


logger = get_logger_app(__name__)


class AzuremlAutoTokenizer(AutoTokenizer):

    @staticmethod
    def pre_init(hf_model_name_or_path: str, **kwargs) -> Dict[str, Any]:
        """Apply model adjustments before calling the Base tokenizer"""

        model_specific_args = {}

        # GPT2 specific adjustments for all tasks
        model_type = AzuremlAutoConfig.get_model_type(hf_model_name_or_path=hf_model_name_or_path, **kwargs)
        if model_type == HfModelTypes.GPT2:
            # adding eos_token as pad_token. The value of eos_token is taken from tokenization_gpt2.py file
            model_specific_args["pad_token"] = "<|endoftext|>"
            logger.info(f'Adding pad token to tokenizer init: {model_specific_args["pad_token"]}')
        elif model_type == HfModelTypes.LLAMA:
            # adding eos_token as pad_token. The value of eos_token is taken from tokenization_llama.py file
            model_specific_args["pad_token"] = "</s>"
            logger.info(f'Adding pad token to tokenizer init: {model_specific_args["pad_token"]}')

        return model_specific_args

    @classmethod
    def from_pretrained(cls, hf_model_name_or_path: str, **kwargs) -> PreTrainedTokenizerBase:
        """
        All the model specific adjustments are defined in their respective task preprocessing files
        :param kwargs
            The kwargs can't contain arbitrary key-value pairs as most of the kwargs will be sent to tokenizer
            during initialization
        """

        apply_adjust = kwargs.pop("apply_adjust", True)
        max_sequence_length = kwargs.pop("max_sequence_length", -1)
        load_config_kwargs = kwargs.pop("load_config_kwargs", {})
        model_specific_args = kwargs
        if apply_adjust:
            logger.info("Applying model adjustments")
            model_specific_args.update(AzuremlAutoTokenizer.pre_init(hf_model_name_or_path, **load_config_kwargs))

        logger.info(f"Tokenizer initialized with args {model_specific_args}")
        # fast tokenizer is loaded by default, if not slow tokenizer is loaded
        try:
            # fast tokenizer
            tokenizer = super().from_pretrained(
                hf_model_name_or_path,
                use_fast=True,
                **model_specific_args,
            )
        except Exception as e:
            logger.warning(f"Fast tokenizer not supported: {e}")
            logger.info("Trying default tokenizer.")
            # slow tokenizer
            tokenizer = super().from_pretrained(
                hf_model_name_or_path,
                **model_specific_args,
            )
        logger.debug("Loaded tokenizer : {}".format(tokenizer))

        # GPT-OSS specific adjustments - align tokenizer vocab with model config vocab_size
        # The gpt-oss-20b model has a mismatch between its config.vocab_size (201088) and the
        # tokenizer's actual vocabulary size (200019). This is because the model reserves 1069
        # token slots (indices 200019-201087) in its embedding layer that are not present in the
        # tokenizer files. When finetuning with LoRA, if the tokenizer size doesn't match the
        # model's embedding size, it triggers an automatic resize_token_embeddings() which creates
        # new LoRA adapters with mismatched shapes, causing validation failures.
        # 
        # To fix this, we detect GPT-OSS models and add placeholder tokens to align the tokenizer
        # vocabulary size with config.vocab_size BEFORE finetuning begins. This prevents embedding
        # resize and ensures LoRA adapters train with the correct dimensions.
        #
        # This alignment happens during preprocessing and the expanded tokenizer is saved, ensuring
        # both training and validation use the same tokenizer configuration.
        model_type = AzuremlAutoConfig.get_model_type(hf_model_name_or_path=hf_model_name_or_path, **load_config_kwargs)
        if model_type == HfModelTypes.GPT_OSS:
            logger.info(f"Applying GPT-OSS specific vocab alignment for {hf_model_name_or_path}")
            from transformers import AutoConfig
            
            config = AutoConfig.from_pretrained(hf_model_name_or_path, **load_config_kwargs)
            
            if config.vocab_size > len(tokenizer):
                num_tokens_to_add = config.vocab_size - len(tokenizer)
                logger.warning(
                    f"GPT-OSS model vocab size mismatch: config.vocab_size={config.vocab_size} "
                    f"vs tokenizer vocab_size={len(tokenizer)}. Adding {num_tokens_to_add} placeholder tokens."
                )
                
                # Generate placeholder tokens to align vocab size
                start_id = len(tokenizer)
                placeholder_tokens = [f"<|reserved_{start_id + i}|>" for i in range(num_tokens_to_add)]
                num_added = tokenizer.add_special_tokens({"additional_special_tokens": placeholder_tokens})
                
                logger.info(f"Added {num_added} placeholder tokens. New tokenizer size: {len(tokenizer)}")
                
                # Verify alignment
                if len(tokenizer) == config.vocab_size:
                    logger.info(f"Successfully aligned GPT-OSS tokenizer vocab size to {config.vocab_size}")
                else:
                    logger.warning(
                        f"GPT-OSS vocab alignment incomplete. Expected {config.vocab_size}, got {len(tokenizer)}"
                    )
            else:
                logger.info(f"GPT-OSS tokenizer vocab size already matches config: {len(tokenizer)}")


        AzuremlAutoTokenizer.set_model_max_length(tokenizer, max_sequence_length)

        return tokenizer

    @staticmethod
    def set_model_max_length(tokenizer: PreTrainedTokenizerBase, max_sequence_length: int = -1) -> None:
        """Set the model max length to a default value to avoid integer out of bounds error"""

        if (
            hasattr(tokenizer, HfConstants.MODEL_MAX_LENGTH_KEY) and
            getattr(tokenizer, HfConstants.MODEL_MAX_LENGTH_KEY) > HfConstants.LARGE_MODEL_MAX_LENGTH
        ):
            logger.info(
                f"Tokenizer {HfConstants.MODEL_MAX_LENGTH_KEY} is set to a very large value - {getattr(tokenizer, HfConstants.MODEL_MAX_LENGTH_KEY)}")
            if max_sequence_length != -1:
                setattr(tokenizer, HfConstants.MODEL_MAX_LENGTH_KEY, max_sequence_length)
            else:
                setattr(tokenizer, HfConstants.MODEL_MAX_LENGTH_KEY, HfConstants.DEFAULT_MAX_SEQ_LENGTH)
            logger.info(f"Adjusted the {HfConstants.MODEL_MAX_LENGTH_KEY} value to {getattr(tokenizer, HfConstants.MODEL_MAX_LENGTH_KEY)}")
        else:
            logger.info(f"Tokenizer {HfConstants.MODEL_MAX_LENGTH_KEY} value is {getattr(tokenizer, HfConstants.MODEL_MAX_LENGTH_KEY)}")
