from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
import streamlit as st



class queryConvert:
    def __init__(self, query:str):
        load_dotenv()
        self.query = query
        # os.environ["GROQ_API_KEY"]= os.getenv("GROQ_API_KEY")
        self.API_KEY = st.secrets["GROQ_API_KEY"]

    def query_convert(self):

        # Initialize Mixtral model
        llm = ChatGroq(model_name="moonshotai/kimi-k2-instruct", temperature=0.2, groq_api_key=self.API_KEY)

        # Example user query
        # user_query = "design and synthesis of gsk3 inhibitors"

        # System instruction to guide the LLM to focus on PubMed-style search generation
        system_prompt = """
        You are a biomedical search expert. Your task is to convert user questions into precise PubMed search queries.

        Rules:
        - Use only terms suitable for PubMed Boolean search (e.g., AND, OR, NOT).
        - Use MeSH terms if possible.
        - Avoid generating full summaries — just the query.

        Return only the query string.
        """

        # Generate PubMed search query
        response = llm([
            SystemMessage(content=system_prompt),
            HumanMessage(content=self.query)
        ])

    
        return response.content
