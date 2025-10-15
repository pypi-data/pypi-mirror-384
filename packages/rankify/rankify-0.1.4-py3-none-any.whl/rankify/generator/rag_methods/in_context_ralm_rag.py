import os
import json
from typing import List
import torch
from tqdm import tqdm
from rankify.dataset.dataset import Document
from rankify.generator.models.base_rag_model import BaseRAGModel
from rankify.generator.rag_methods.base_rag_method import BaseRAGMethod
from transformers import AutoConfig

class InContextRALMRAG(BaseRAGMethod):
    """
    **In-Context Retrieval-Augmented Language Model (RALM) Generator**.


    This class implements **In-Context Retrieval-Augmented Language Models (RALM)** for **context-aware text generation**.
    It **integrates retrieved passages** into the input prompt for **few-shot learning**, improving response quality.

    Attributes:
        model (BaseRAGModel): The underlying RAG model used for generation.
        tokenizer: Tokenizer associated with the model.
        device (str): Device used for inference (`'cuda'` or `'cpu'`).
        cache_dir (str): Directory to store downloaded models and cache files.
        num_docs (int): Number of retrieved contexts to include in the prompt (default: 1).
        max_length (int): Maximum number of tokens the model can process.
        max_tokens_to_generate (int): Maximum number of tokens the model generates in response.

    Methods:
        _build_qa_prompt(example): Constructs a QA prompt with retrieved passages for in-context learning.
        _prepare_dataloader(documents): Converts Document objects into a dataset formatted for RALM.
        answer_questions(documents, custom_prompt=None): Generates answers for a list of documents using RALM.

    References:
        - **Ram et al.** *In-Context Retrieval-Augmented Language Models*  
          [Paper](https://arxiv.org/abs/2302.00083)

    See Also:
        - `BaseRAGMethod`: Parent class for RAG techniques.
        - Few-Shot Learning: This method leverages retrieved passages for in-context QA.

    Example:
        ```python
        from rankify.dataset.dataset import Document, Question, Answer, Context
        from rankify.generator.generator import Generator

        # Sample question and contexts
        question = Question("What is the capital of France?")
        answers=Answer('')
        contexts = [
            Context(id=1, title="France", text="The capital of France is Paris.", score=0.9),
            Context(id=2, title="Germany", text="Berlin is the capital of Germany.", score=0.5)
        ]

        # Create a Document
        doc = Document(question=question, answers= answers, contexts=contexts)

        # Initialize Generator (e.g., Meta Llama, with huggingface backend)
        generator = Generator(method="in-context-ralm", model_name='meta-llama/Meta-Llama-3.1-8B-Instruct', backend="huggingface")

        # Generate answer
        generated_answers = generator.generate([doc])
        print(generated_answers)  # Output: ["Paris"]
        ```

    Notes:
        - RALM dynamically integrates retrieved passages to guide response generation.
        - Optimized for retrieval-augmented question answering (RAG).
        - Prompts are constructed to encourage factual, concise answers suitable for evaluation and comparison.
    """

    CACHE_DIR = os.environ.get("RERANKING_CACHE_DIR", "./cache")

    def __init__(self, model:BaseRAGModel, **kwargs):
        """
        Initializes the RALM Generator.

        Args:
            method (str): The generator type (`"in-context-ralm"`).
            model_name (str): The name of the pre-trained RALM model (e.g., `"meta-llama/Llama-3.1-8B"`).
            **kwargs: Additional parameters for model configuration.

        Example:
            ```python
            generator = InContextRALMGenerator(method="in-context-ralm", model_name="meta-llama/Llama-3.1-8B")
            ```
        """
        self.base_rag_model = model
        self.model = model.model
        self.tokenizer = model.tokenizer
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.cache_dir = self.CACHE_DIR
        self.num_docs = kwargs.get("num_docs", 1)  # Default: 1 supporting document



        self.tokenizer.pad_token = self.tokenizer.eos_token

        self.config = AutoConfig.from_pretrained(model.model_name)

        # Set generation parameters
        self.max_length = self.config.n_positions if hasattr(self.config, "n_positions") else self.config.max_position_embeddings
        self.max_tokens_to_generate = kwargs.get("max_tokens_to_generate", 10)


    def _prepare_dataloader(self, documents: list[Document]):
        """
        Converts `Document` objects into a dataset **formatted for RALM**.

        Args:
            documents (List[Document]): A list of documents with **queries and retrieved contexts**.

        Returns:
            list: A list of dictionaries formatted for in-context learning.

        Example:
            ```python
            dataset = generator._prepare_dataloader(documents)
            ```
        """
        examples = []
        for doc in documents:
            example = {
                "question": doc.question.question,
                "answers": doc.answers.answers,
                "ctxs": [{"title": ctx.title, "text": ctx.text, "score": ctx.score} for ctx in doc.contexts]
            }
            examples.append(example)

        return examples

    def answer_questions(self, documents: List[Document], custom_prompt=None) -> List[str]:
        """
        Generates answers for **a list of documents** using RALM.

        Args:
            documents (List[Document]): A list of documents with **queries and retrieved contexts**.

        Returns:
            List[str]: A list of generated answers.
        """
        eval_dataset = self._prepare_dataloader(documents)

        results = []
        for example in tqdm(eval_dataset, desc="Answering questions", unit="q"):
            context_strs = [f"{ctx['title']}\n\n{ctx['text']}" for ctx in example["ctxs"][:self.num_docs]]
            prompt = self.base_rag_model.prompt_generator.generate_user_prompt(
                question=example["question"],
                contexts=context_strs,
                custom_prompt=custom_prompt
            )

            tokenized_input = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
            input_ids = tokenized_input.input_ids.to(self.device)
            attention_mask = tokenized_input.attention_mask.to(self.device)  # Extract attention mask

            if input_ids.shape[-1] > self.max_length - self.max_tokens_to_generate:
                input_ids = input_ids[..., -(self.max_length - self.max_tokens_to_generate):]
                attention_mask = attention_mask[..., -(self.max_length - self.max_tokens_to_generate):]

            with torch.no_grad():
                outputs = self.model.generate(input_ids, attention_mask=attention_mask, max_new_tokens=self.max_tokens_to_generate,  pad_token_id=self.tokenizer.pad_token_id )

            # Extract generated text
            generation_str = self.tokenizer.decode(outputs[0].cpu(), skip_special_tokens=True)
            answer = generation_str[len(prompt):].split("\n")[0]

            results.append(answer)

        return results

