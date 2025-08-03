from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from typing import List, Dict

class SearchWork_faiss:
    def __init__(self, model, query: str, articles: List[Dict]):
        self.model = model
        self.query = query
        self.articles = articles

    def build_documents(self, use_case: str) -> List[Document]:
        documents = []
        for article in self.articles:
            pmid = str(article.get('pmid', ''))
            title = article.get('title', '')
            abstract = article.get('abstract', '')
            authors = article.get('authors', [])
            doi = article.get('doi', '')
            journal = article.get('journal')
            pub_year = article.get('pub_year')
            pub_type = article.get('publication_types')

            if not pmid:
                continue

            if use_case == 'combined':
                content = f"{title}. {abstract}".strip()
            elif use_case == 'title':
                content = title.strip()
            elif use_case == 'abstract':
                content = abstract.strip()
            else:
                continue  # skip invalid use_case

            if content:
                metadata = {
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "chunk": content,
                    "authors": authors,
                    "doi": doi,
                    "journal": journal,
                    "pub_year": pub_year,
                    "publication_types":pub_type

                }
                documents.append(Document(page_content=content, metadata=metadata))
        return documents

    def search_similar(self, use_case, top_k=25, similarity_threshold: float = 0.48):
        # Step 1: Convert to LangChain documents
        docs = self.build_documents(use_case)

        if not docs:
            return []

        # Step 2: Build FAISS index
        vectorstore = FAISS.from_documents(docs, self.model)

        # Step 3: Search
        results = vectorstore.similarity_search_with_score(self.query, k=top_k)

        # Step 4: Format results
        formatted = []
        for doc, score in results:
            if score is None:
                continue  # skip invalid results

            similarity = 1 - score  # FAISS returns distance; convert to similarity
            if similarity < similarity_threshold:
                continue

        for doc, score in results:
            formatted.append({
                "pmid": doc.metadata["pmid"],
                "similarity": 1 - score,  # FAISS returns distance; convert to similarity
                "title": doc.metadata["title"],
                "abstract": doc.metadata["abstract"],
                "chunk": doc.metadata["chunk"],
                "authors": doc.metadata["authors"],
                "doi": doc.metadata["doi"],
                "journal": doc.metadata["journal"],
                "pub_year": doc.metadata["pub_year"],
                "publication_types":doc.metadata["publication_types"]
})

        return sorted(formatted, key=lambda x: x["similarity"], reverse=True)
