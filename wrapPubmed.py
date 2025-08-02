from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings

class PubMedBERTEmbedding(Embeddings):
    def __init__(self, model_name="neuml/pubmedbert-base-embeddings"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts):
        return self.model.encode(texts, convert_to_numpy=True).tolist()

    def embed_query(self, text):
        return self.model.encode(text, convert_to_numpy=True).tolist()