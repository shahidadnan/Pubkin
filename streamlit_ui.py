import streamlit as st
import streamlit.components.v1 as components


class StreamlitApp:
    def __init__(self, model, querier_class, search_class, query_class ):
        self.model = model
        self.PubMedQuerier = querier_class
        self.SearchWork = search_class
        self.query = query_class

    #st.write("Loaded UI")
    def run(self):
        # ------------- Sidebar ---------------- #
        st.sidebar.title("User Info")
        email = st.sidebar.text_input("Enter your email")

        # ------------- Main Page ---------------- #
        st.title("PubKin")

        query = st.text_input("Enter your search query")
        embedding_option = st.selectbox(
            "Choose embedding type", ["abstract", "title", "combined"], index=2
        )
        search = st.button("Search")

        if search:
            if not email or not query:
                st.warning("Both email and query are required.")
                return

            with st.spinner("🔄 Fetching data from PubMed..."):
                try:
                    # Initialize backend classes
                    querier = self.PubMedQuerier(email=email)
                    
                    mesh_query = self.query(query)
                    query = mesh_query.query_convert()
                    pmids = querier.search_pubmed(query, max_results=30)

                    if not pmids:
                        st.error("No articles found.")
                        return

                    articles = querier.fetch_article_details(pmids)
                    st.success("Articles retrieved!")

                    
                    model = self.model
                    searcher = self.SearchWork(model, query, articles )
                    
                    similarities = searcher.search_similar(embedding_option)

                    if not similarities:
                        st.warning("No embeddings found for selected type.")
                        return

                    st.markdown("### 🧠 Top Matches")
                    for item in similarities:
                        title = item['title']
                        journal = item.get('journal')
                        pub_year = item.get('pub_year')
                        
                        expander_label = f"""**{title}**
                            \n {journal} · {pub_year}"""
                        with st.expander(expander_label):
                            st.markdown(f"**PMID:** {item['pmid']}")
                            st.markdown(f"**Abstract:** {item['abstract']}")
                            # st.markdown(f"[🔗 View on PubMed](https://pubmed.ncbi.nlm.nih.gov/{item['pmid']}/)")
                            st.markdown(f"[🔗 View on DOI](https://doi.org/{item['doi']})")
                except Exception as e:
                    st.error(f"❗ Error: {str(e)}")