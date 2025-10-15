from typing import List
from rankify.generator.models.base_rag_model import BaseRAGModel

from typing import List
from rankify.dataset.dataset import Document
from rankify.generator.rag_methods.base_rag_method import BaseRAGMethod
from tqdm.auto import tqdm 

class BasicRAG(BaseRAGMethod):
    """
    **BasicRAG (Naive RAG) Method** for Retrieval-Augmented Generation.

    Implements a simple RAG technique that answers questions by concatenating retrieved contexts and passing them,
    along with the question, to the underlying model. This is the most straightforward RAG approach.

    Attributes:
        model (BaseRAGModel): The RAG model instance used for generation.

    References:
        - **Lewis et al. **Retrieval-augmented generation for knowledge-intensive nlp tasks**  
          [Paper](https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html)
    
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
        generator = Generator(method="basic-rag", model_name='meta-llama/Meta-Llama-3.1-8B-Instruct', backend="huggingface")

        # Generate answer
        generated_answers = generator.generate([doc])
        print(generated_answers)  # Output: ["Paris"]
        ```
    
    Notes:
        - This method does not apply advanced reasoning or fusion techniques.
        - Suitable as a baseline for comparison with more sophisticated RAG methods.
    """
    def __init__(self, model: BaseRAGModel, **kwargs):
        """
        Initialize the BasicRAG method.

        Args:
            model (BaseRAGModel): The RAG model instance used for generation.
        """
        super().__init__(model=model)

    def answer_questions(self, documents: List[Document], custom_prompt=None, **kwargs) -> List[str]:
        """
        Answer questions for a list of documents using the model.

        Args:
            documents (List[Document]): A list of Document objects containing questions and contexts.
            custom_prompt (str, optional): Custom prompt to override default prompt generation.
            **kwargs: Additional parameters for the model's generate method.

        Returns:
            List[str]: Answers generated for each document.

        Notes:
            - Concatenates all context passages and passes them with the question to the model.
            - Uses the model's prompt generator to construct prompts.
        """
        answers = []

        for document in tqdm(documents, desc="Answering questions", unit="q"):
            # Extract question and contexts from the document
            question = document.question.question
            contexts = [context.text for context in document.contexts]

            # Construct the prompt
            prompt = self.model.prompt_generator.generate_user_prompt(question, contexts, custom_prompt)
            # Generate the answer using the model
            answer = self.model.generate(prompt=prompt, **kwargs)
            
            # Append the answer to the list
            answers.append(answer)
        return answers