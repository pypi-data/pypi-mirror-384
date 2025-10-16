from typing import List, Union, Dict, Any
# Make sure you have langchain installed for this import to work
# pip install langchain
from langchain.docstore.document import Document
from langchain.text_splitter import TextSplitter
import tiktoken
import numpy as np
import matplotlib.pyplot as plt

class TextSplitterComparer:
    """
    A class to compare different types of LangChain Text Splitters
    by analyzing the token distribution in the resulting chunks and
    visualizing the results.

    It supports both a single string (str) and a list of LangChain
    Documents (List[Document]) as input.
    """

    def __init__(self, input_doc: Union[str, List[Document]], splitters_to_compare: Dict[str, TextSplitter]):
        """
        Initializes the comparer with the text or documents to process and a dictionary of splitters.

        Args:
            input_doc (Union[str, List[Document]]): The text (str) or list of
                                                   documents (List[Document]) to be split.
            splitters_to_compare (Dict[str, TextSplitter]): A dictionary where keys are identifying
                                                            names for the splitters and values are
                                                            LangChain TextSplitter instances.
        """
        self.input_doc = input_doc
        self.splitters_to_compare = splitters_to_compare
        # It's recommended to use the same encoding that the final model will use
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, text_chunk: str) -> int:
        """
        Calculates the number of tokens in a chunk of text.
        """
        return len(self.tokenizer.encode(text_chunk))

    def analyze_splitter(self, splitter_name: str, splitter: TextSplitter) -> Dict[str, Any]:
        """
        Analyzes a single splitter and calculates token distribution metrics.

        It checks if input_doc is a string or a list of Documents to use
        the appropriate splitting method ('split_text' or 'split_documents').

        Args:
            splitter_name (str): The identifying name of the splitter.
            splitter (TextSplitter): A LangChain TextSplitter instance.

        Returns:
            dict: A dictionary with the analysis metrics.
        """
        # --- MODIFIED LOGIC ---
        # Check the type of input_doc to decide which method to use
        if isinstance(self.input_doc, str):
            # If it's a string, use split_text
            text_chunks = splitter.split_text(self.input_doc)
        elif isinstance(self.input_doc, list):
            # If it's a list, we assume it's List[Document] and use split_documents
            document_chunks = splitter.split_documents(self.input_doc)
            # Extract the text content (page_content) from each Document
            text_chunks = [doc.page_content for doc in document_chunks]
        else:
            # Raise an error if the type is not supported
            raise TypeError(f"The input_doc type ({type(self.input_doc)}) is not supported. It must be str or List[Document].")
        # --- END OF MODIFIED LOGIC ---

        token_counts = [self._count_tokens(chunk) for chunk in text_chunks]

        if not token_counts:
            return {
                "splitter_name": splitter_name,
                "number_of_chunks": 0,
                "token_statistics": {
                    "mean": 0, "median": 0, "std_dev": 0,
                    "min": 0, "max": 0, "25th_percentile": 0, "75th_percentile": 0,
                },
                "token_distribution": []
            }

        stats = {
            "mean": np.mean(token_counts),
            "median": np.median(token_counts),
            "std_dev": np.std(token_counts),
            "min": np.min(token_counts),
            "max": np.max(token_counts),
            "25th_percentile": np.percentile(token_counts, 25),
            "75th_percentile": np.percentile(token_counts, 75),
        }

        return {
            "splitter_name": splitter_name,
            "number_of_chunks": len(text_chunks),
            "token_statistics": stats,
            "token_distribution": token_counts
        }

    def compare(self) -> List[Dict[str, Any]]:
        """
        Compares all splitters provided during initialization.

        Returns:
            list: A list of dictionaries, each containing the analysis of one splitter.
        """
        results = []
        for name, splitter in self.splitters_to_compare.items():
            results.append(self.analyze_splitter(name, splitter))
        return results

    def print_results(self, results: List[Dict[str, Any]]):
        """
        Prints the comparison results in a readable format.
        """
        for result in results:
            print(f"--- Analysis for: {result['splitter_name']} ---")
            print(f"Total number of chunks: {result['number_of_chunks']}")
            stats = result['token_statistics']
            print("Token distribution statistics per chunk:")
            for key, value in stats.items():
                print(f"  - {key.replace('_', ' ').capitalize()}: {value:.2f}")
            print("-" * (25 + len(result['splitter_name'])))
            print("\n")

    def plot_distributions(self, results: List[Dict[str, Any]]):
        """
        Creates a token distribution plot for each splitter.
        Each plot shows the number of tokens per chunk.
        """
        num_splitters = len(results)
        if num_splitters == 0:
            print("No results to plot.")
            return

        cols = 2 if num_splitters > 1 else 1
        rows = (num_splitters + 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(15, 5 * rows), squeeze=False)
        fig.suptitle('Token Distribution Comparison per Splitter', fontsize=16, y=1.02)

        axes = axes.flatten()

        for i, result in enumerate(results):
            ax = axes[i]
            token_counts = result['token_distribution']
            chunk_indices = range(1, len(token_counts) + 1)

            ax.bar(chunk_indices, token_counts, color='skyblue', edgecolor='black')

            splitter_instance = self.splitters_to_compare.get(result['splitter_name'])
            if splitter_instance and hasattr(splitter_instance, '_chunk_size'):
                chunk_size = splitter_instance._chunk_size
                ax.axhline(y=chunk_size, color='r', linestyle='--', label=f'Target Chunk Size ({chunk_size})')

            ax.set_title(f"Splitter: '{result['splitter_name']}'")
            ax.set_xlabel("Chunk Index")
            ax.set_ylabel("Number of Tokens")
            if ax.get_legend_handles_labels()[1]: # Only show legend if it exists
              ax.legend()
            ax.grid(axis='y', linestyle='--', alpha=0.7)

        for i in range(len(results), len(axes)):
            fig.delaxes(axes[i])

        plt.tight_layout(rect=[0, 0, 1, 0.98])
        plt.show()