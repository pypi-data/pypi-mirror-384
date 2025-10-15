"""
Prompt formatting class definitions.
"""

#
# @authors: Syed Rizvi
#

# Python built-in libraries
import json
import random
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

# Third-party libraries
from datasets import Dataset

HERE = Path(__file__).parent
SUPPORTED_TASKS = [
    "cell_type_prediction",
    "cell_type_generation",
]
MULTICELL_SUPPORTED_TASKS = [
    "tissue_prediction",
    "tissue_conditional_generation",
    "natural_language_interpretation",
]


def get_cell_sentence_str(ds_sample, num_genes: Optional[int] = None):
    """
    Helper function for formatting cell sentences. Returns a cell sentence string containing
    a list of space-separated gene names. Caps number of genes at 'num_genes' if not None.

    Arguments:
        ds_sample: Huggingface dataset sample, assumed to follow C2S data schema.
        num_genes: if not None, integer representing number of genes to limit cell sentence to.
    """
    full_cell_sentence = ds_sample["cell_sentence"]
    if num_genes is not None:
        full_cell_sentence_gene_list = full_cell_sentence.split(" ")
        cell_sentence_str = " ".join(full_cell_sentence_gene_list[:num_genes])
        num_genes_str = str(num_genes)
    else:
        cell_sentence_str = full_cell_sentence
        num_genes_str = ""
    return cell_sentence_str, num_genes_str


class PromptFormatter(ABC):
    """
    Abstract base class for prompt formatting.

    Subclasses should implement the format_hf_ds method, which takes a Huggingface
    dataset and formats it with any chosen prompts for the desired task. It should
    return a new Huggingface dataset with at least the following columns:
    - model_input: str, the formatted model input
    - response: str, the formatted model response
    These will be used by the tokenizer to format the data for the model.
    """
    
    @abstractmethod
    def format_hf_ds(self, hf_ds):
        """Format a Huggingface dataset with prompts."""
        pass


class C2SPromptFormatter(PromptFormatter):
    """
    Wrapper class to abstract different types of input data that can be passed
    in cell2sentence based workflows.
    """

    def __init__(self, task: str, top_k_genes: int, random_seed: int = 42):
        """
        Loads prompts for standard C2S tasks and handles prompt formatting given
        a cell sentence dataset.

        Arguments:
            task: task to format prompts for (options: 'cell_type_prediction', 'cell_type_generation').
            top_k_genes: number of genes to use per cell sentence.
            random_seed: random seed to control random number generation for reproducibility.
        """
        assert task in SUPPORTED_TASKS, "Specified finetuning task is not yet supported."
        assert top_k_genes > 0, "'top_k_genes' must be an integer > 0"
        self.task = task
        self.top_k_genes = top_k_genes
        random.seed(random_seed)

        self.prompts_dict = {}
        if task == "cell_type_prediction":
            with open(HERE / "prompts/single_cell_cell_type_prediction_prompts.json", "r") as f:
                self.prompts_dict = json.load(f)
        elif task == "cell_type_generation":
            with open(HERE / "prompts/single_cell_cell_type_conditional_generation_prompts.json", "r") as f:
                self.prompts_dict = json.load(f)
    
    def get_keys_for_task(self):
        """
        Depending on the task, this function will tell you what keys are supposed to be formatted in the
        model input and model output.
        """
        if self.task == "cell_type_prediction":
            model_input_keys = ["num_genes", "organism", "cell_sentence"]
            response_keys = ["cell_type"]
        elif self.task == "cell_type_generation":
            model_input_keys = ["num_genes", "organism", "cell_type"]
            response_keys = ["cell_sentence"]
        
        return model_input_keys, response_keys
    
    def format_hf_ds(self, hf_ds):
        """
        Helper function to loop through dataset samples, format prompts

        Arguments:
            hf_ds: Huggingface arrow dataset containing cell sentences to format prompts with.
        """
        model_inputs_list = []
        responses_list = []

        # Get keys for model input and response which will need to be formatted
        model_input_keys, response_keys = self.get_keys_for_task()

        for cell_idx in range(hf_ds.num_rows):
            sample = hf_ds[cell_idx]
            
            # Get cell sentence
            single_cell_sentence_str, num_genes_str = get_cell_sentence_str(sample, num_genes=self.top_k_genes)
            sample["cell_sentence"] = single_cell_sentence_str
            sample["num_genes"] = num_genes_str

            # Select an input prompt, format keys
            model_input_str = random.choice(self.prompts_dict["model_input"])
            model_input_str = model_input_str.format(**{key: sample[key] for key in model_input_keys})
            
            # Format key in response
            response_str = self.prompts_dict["response"][0]  # 1 response template
            response_str = response_str.format(**{key: sample[key] for key in response_keys})

            model_inputs_list.append(model_input_str)
            responses_list.append(response_str)

        # Create formatted Huggingface dataset
        ds_split_dict = {
            "sample_type": [self.task] * hf_ds.num_rows,
            "model_input": model_inputs_list,
            "response": responses_list,
        }
        ds = Dataset.from_dict(ds_split_dict)
        return ds


class C2SMultiCellPromptFormatter(PromptFormatter):
    """
    Wrapper class for multi-cell prompt formatting.
    """

    def __init__(self, task: str, top_k_genes: int, random_seed: int = 42):
        """
        Loads prompts for standard C2S tasks and handles prompt formatting given
        a cell sentence dataset.

        Arguments:
            task: task to format prompts for (options: 'cell_type_prediction', 'cell_type_generation').
            top_k_genes: number of genes to use per cell sentence.
            random_seed: random seed to control random number generation for reproducibility.
        """
        assert task in MULTICELL_SUPPORTED_TASKS, "Specified finetuning task is not yet supported."
        assert top_k_genes > 0, "'top_k_genes' must be an integer > 0"
        self.task = task
        self.top_k_genes = top_k_genes
        random.seed(random_seed)

        self.prompts_dict = {}
        if task == "tissue_prediction":
            with open(HERE / "prompts/multi_cell_tissue_prediction_prompts.json", "r") as f:
                self.prompts_dict = json.load(f)
        elif task == "tissue_conditional_generation":
            with open(HERE / "prompts/multi_cell_tissue_conditional_generation.json", "r") as f:
                self.prompts_dict = json.load(f)
        elif task == "natural_language_interpretation":
            with open(HERE / "prompts/multi_cell_natural_lang_interpretation_prompts.json", "r") as f:
                self.prompts_dict = json.load(f)
    
    def get_keys_for_task(self):
        """
        Depending on the task, this function will tell you what keys are supposed to be formatted in the
        model input and model output.
        """
        if self.task == "tissue_prediction":
            model_input_keys = ["num_genes", "num_cells", "organism", "multi_cell_sentences"]
            response_keys = ["tissue"]
        elif self.task == "tissue_conditional_generation":
            model_input_keys = ["num_genes", "num_cells", "organism", "tissue"]
            response_keys = ["multi_cell_sentences"]
        elif self.task == "natural_language_interpretation":
            model_input_keys = ["num_genes", "num_cells", "organism", "multi_cell_sentences"]
            response_keys = ["abstract"]
        
        return model_input_keys, response_keys
    
    def format_hf_ds(self, hf_ds, multi_cell_indices_ds):
        """
        Helper function to loop through dataset samples, format prompts

        Arguments:
            hf_ds: Huggingface arrow dataset containing cell sentences to format prompts with.
            multi_cell_indices_ds: Huggingface arrow dataset containing multi-cell indices,
                indicating which cells are grouped together from the original dataset.
        """
        model_inputs_list = []
        responses_list = []

        # Get keys for model input and response which will need to be formatted
        model_input_keys, response_keys = self.get_keys_for_task()

        for cell_idx in range(multi_cell_indices_ds.num_rows):
            multi_cell_sample = multi_cell_indices_ds[cell_idx]
            multi_cell_indices = multi_cell_sample["multi_cell_groupings"]

            # Build multi-cell string
            multi_cell_str = ""
            for idx, cell_idx in enumerate(multi_cell_indices):
                sample = hf_ds[cell_idx]
                multi_cell_str += f"Cell {idx + 1}:\n"
                single_cell_sentence_str, _ = get_cell_sentence_str(sample, num_genes=self.top_k_genes)
                multi_cell_str += single_cell_sentence_str
                multi_cell_str += ".\n"
            multi_cell_sample["multi_cell_sentences"] = multi_cell_str
            multi_cell_sample["num_genes"] = self.top_k_genes
            multi_cell_sample["num_cells"] = len(multi_cell_indices)

            # Select an input prompt, format keys
            model_input_str = random.choice(self.prompts_dict["model_input"])
            model_input_str = model_input_str.format(**{key: multi_cell_sample[key] for key in model_input_keys})
            
            # Format key in response
            response_str = self.prompts_dict["response"][0]  # 1 response template
            response_str = response_str.format(**{key: multi_cell_sample[key] for key in response_keys})

            model_inputs_list.append(model_input_str)
            responses_list.append(response_str)

        # Create formatted Huggingface dataset
        ds_split_dict = {
            "sample_type": [self.task] * multi_cell_indices_ds.num_rows,
            "model_input": model_inputs_list,
            "response": responses_list,
        }
        ds = Dataset.from_dict(ds_split_dict)
        return ds
