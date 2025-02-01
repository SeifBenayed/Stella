import base64
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List
from utils.file_utils import FileUtils


class HelperFunct(FileUtils):

    def __init__(self, tmp_folder):
        super().__init__(tmp_folder)

    @staticmethod
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def create_chunks(self):
        fp = open(self.html_path, "r")
        txt = fp.read()
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=5000,
            chunk_overlap=20,
            is_separator_regex=False,
        )

        chunks = text_splitter.create_documents([txt])
        return chunks

    @staticmethod
    def length_function(documents: List[Document]) -> int:
        """Get number of tokens for input contents."""
        # return sum(llm.get_num_tokens(doc.page_content) for doc in documents)
        return sum(100 for doc in documents)
