import os
from langchain_openai import AzureOpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore


class Embeddings:
    def __init__(self):
        self.embeddings_model = AzureOpenAIEmbeddings(
            api_key=os.environ["azure_api_key_emb_1"],
            deployment=os.environ["azure_deployment_emb_1"],
            azure_endpoint=os.environ["azure_endpoint_emb_1"]
        )

    def create_vector_store(self, chunks):
        self.vectorstore = InMemoryVectorStore.from_texts(chunks, embedding=self.embeddings_model)
        self.retriever = self.vectorstore.as_retriever()


    def get_relevant_docs(self, query):
        self.retrieved_documents = self.retriever.invoke(query)
        return self.retrieved_documents
