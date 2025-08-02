from streamlit_ui import StreamlitApp
from query_pubmed import PubMedQuerier
# from searchworkflow import SearchWork
# from sentence_transformers import SentenceTransformer
from searchworkflow_faiss import SearchWork_faiss
from langchain_community.embeddings import HuggingFaceEmbeddings
from wrapPubmed import PubMedBERTEmbedding
from query_conversion import queryConvert


model = PubMedBERTEmbedding()
    
app = StreamlitApp(model, PubMedQuerier, SearchWork_faiss, queryConvert)
    

if __name__ == "__main__":
    print("loading model")
    # model = PubMedBERTEmbedding()
    # model = HuggingFaceEmbeddings(model = "neuml/pubmedbert-base-embeddings")

    print("starting streamlit")
    # app = StreamlitApp(model, PubMedQuerier, SearchWork_faiss)
    
    app.run()
