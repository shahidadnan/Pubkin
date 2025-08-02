from query_pubmed import PubMedQuerier
from searchworkflow import SearchWork 
from sentence_transformers import SentenceTransformer

def main():
    """
    Main function to demonstrate usage
    """
    # Configuration
    EMAIL = "a.shahid.3003@gmail.com"  # CHANGE THIS TO YOUR EMAIL
    API_KEY = None  # Optional: Add your NCBI API key for higher rate limits
    
    # Initialize querier
    querier = PubMedQuerier(EMAIL, API_KEY)
    
    # Example search query
    search_query = "design and synthesis of Gsk3 inhibitors" #CHANGE THIS TO YOUR QUERY
    model = SentenceTransformer("neuml/pubmedbert-base-embeddings")

    try:
        # Search PubMed
        pmid_list = querier.search_pubmed(search_query, max_results=30)
        
        if not pmid_list:
            print("No results found.")
            return
        querier.display_summary(articles)
        
        # Fetch detailed article information
        articles = querier.fetch_article_details(pmid_list)
    
        obj_search = SearchWork(model,search_query,articles)
        
        obj_search.search_similar('title')
        # Display summary
        
        # Save results
        #csv_file = querier.save_to_csv(articles)
        #json_file = querier.save_to_json(articles)
        
        #print(f"\nFiles saved:")
        #print(f"  CSV: {csv_file}")
        #print(f"  JSON: {json_file}")
        
    except Exception as e:
        print(f"Error in main execution: {e}")


if __name__ == "__main__":
    main()