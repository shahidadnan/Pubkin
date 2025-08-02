import json
import torch
import numpy as np
#import faiss
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import json
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel


class SearchWork:
    def __init__(self, model,query,data):
        self.model = model 
        self.articles = data
        self.query = query
        self.embedding_data = {}
        self.embedding_results = {}
        

    def search_similar(self,use_case):
        

        for article in self.articles:
            # Extract required fields
            pmid = str(article.get('pmid', ''))
            abstract = article.get('abstract', '')
            title = article.get('title', '')
            authors = article.get('authors', [])
            publishers = article.get('publishers', '')

            if not pmid:
                continue

            # Combine title and abstract for comprehensive embedding
            combined_text = f"{title}. {abstract}".strip()

            # Create embeddings
            embeddings = {}

            if abstract:
                abstract_embedding = self.model.encode([abstract])[0]   #[0] → extracts the first (and only) embedding from the returned list.
                embeddings['abstract'] = abstract_embedding.tolist()    #.tolist() converts the embedding from a NumPy array or tensor to a Python list (useful for serialization).

            if title:
                title_embedding = self.model.encode([title])[0]
                embeddings['title'] = title_embedding.tolist()

            if combined_text:
                combined_embedding = self.model.encode([combined_text])[0]
                embeddings['combined'] = combined_embedding.tolist()

            # Store in results
            self.embedding_results[pmid] = {
                'pmid': pmid,
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'publishers': publishers,
                'embeddings': embeddings,
                'chunk': combined_text
            }

        self.embedding_data = self.embedding_results

        # Encode the query
        query_embedding = self.model.encode([self.query])[0]
        # Compute similarities
        similarities = []
        for pmid, article_data in self.embedding_data.items():
            #performing semantic search on combined (topic + abs data)
            if use_case=='combined':
                #performing semantic search on combined (topic + abs data)
            
                if 'combined' in article_data['embeddings']:
                    article_embedding = np.array(article_data['embeddings']['combined'])
                    similarity = np.dot(query_embedding, article_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(article_embedding)+ 1e-10
                    )

            elif use_case=='title':
                #performing semantic search on title.
            
                if 'title' in article_data['embeddings']:
                    article_embedding = np.array(article_data['embeddings']['title'])
                    similarity = np.dot(query_embedding, article_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(article_embedding)+ 1e-10
                    )


            elif use_case=='abstract':
                # perfroming semntic search on abstract

                if 'abstract' in article_data['embeddings']:
                    article_embedding = np.array(article_data['embeddings']['abstract'])
                    similarity = np.dot(query_embedding, article_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(article_embedding)+ 1e-10
                    )


            similarities.append({
                'pmid': pmid,
                'similarity': float(similarity),
                'title': article_data['title'],
                'abstract': article_data['abstract'],
                'chunk': article_data['chunk'],
                'authors': article_data['authors'],
                'publishers': article_data['publishers']
            })

        # Sort and print top results
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities

        #for i in range(min(10, len(similarities))):
        #   print(f"\nResult {i+1}")
         #   print(f"PMID: {similarities[i]['pmid']}")
          #  print(f"Title: {similarities[i]['title']}")
           # print(f"Abstract: {similarities[i]['abstract']}")
            #print(f"Similarity Score: {similarities[i]['similarity']:.4f}")
    
        