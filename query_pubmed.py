#!/usr/bin/env python3

import time
from Bio import Entrez
import pandas as pd
from datetime import datetime
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

class PubMedQuerier:
    def __init__(self, email, api_key=None):
        """
        Initialize PubMed querier with email (required by NCBI)
        
        Args:
            email (str): Your email address (required by NCBI)
            api_key (str, optional): NCBI API key for higher rate limits
        """
        Entrez.email = email
        if api_key:
            Entrez.api_key = api_key
        
    def search_pubmed(self, query, max_results=30, sort_by='relevance'):
        """
        Search PubMed for articles matching the query
        Args:
            query (str): Search query
            max_results (int): Maximum number of results to retrieve
            sort_by (str): Sort order ('relevance', 'pub_date', 'title', etc.)
        
        Returns:
            list: List of PubMed IDs
        """
        try:
            print(f"Searching PubMed for: '{query}'")
            
            # Perform the search
            search_handle = Entrez.esearch(
                db="pubmed",
                term=query,
                retmax=max_results,
                sort=sort_by,
                usehistory="y"
            )
            
            search_results = Entrez.read(search_handle)
            search_handle.close()
            
            id_list = search_results["IdList"]
            print(f"Found {len(id_list)} articles")
            
            return id_list
            
        except Exception as e:
            print(f"Error during search: {e}")
            return []
    

    def fetch_article_details(self, pmid_list):
        """
        Fetch detailed information for a list of PubMed IDs using batching + threading + rate-limiting
        """
        articles = []
        batch_size = 10
        rate_limit_per_sec = 3  # PubMed allows 3 requests/sec without API key
        delay_between_batches = 1 / rate_limit_per_sec  # ~333ms

        def fetch_batch(batch):
            try:
                handle = Entrez.efetch(
                    db="pubmed",
                    id=batch,
                    rettype="medline",
                    retmode="xml"
                )
                records = Entrez.read(handle)
                handle.close()
                return [self._extract_article_info(r) for r in records['PubmedArticle']]
            except Exception as e:
                print(f"[ERROR] Failed fetching batch {batch}: {e}")
                return []

        print(f"Fetching {len(pmid_list)} articles in batches of {batch_size}...")

        # Create all batches
        batches = [pmid_list[i:i + batch_size] for i in range(0, len(pmid_list), batch_size)]

        with ThreadPoolExecutor(max_workers=rate_limit_per_sec) as executor:
            futures = []
            last_submit_time = time.time()

            for i, batch in enumerate(batches):
                now = time.time()
                elapsed = now - last_submit_time
                if elapsed < delay_between_batches:
                    time.sleep(delay_between_batches - elapsed)

                futures.append(executor.submit(fetch_batch, batch))
                last_submit_time = time.time()

            # Gather results
            for future in as_completed(futures):
                articles.extend(future.result())

        print(f"[INFO] Finished fetching {len(articles)} articles")
        return articles

    def _extract_article_info(self, record):
        """
        Extract comprehensive information from a PubMed record
        
        Args:
            record: PubMed XML record
            
        Returns:
            dict: Dictionary containing article information
        """
        article = record['MedlineCitation']['Article']
        medline_citation = record['MedlineCitation']
        
        # Basic article information
        info = {
            'pmid': medline_citation['PMID'],
            'title': '',
            'abstract': '',
            'authors': [],
            'journal': '',
            'journal_abbrev': '',
            'issn': '',
            'volume': '',
            'issue': '',
            'pages': '',
            'pub_date': '',
            'pub_year': '',
            'doi': '',
            'keywords': [],
            'mesh_terms': [],
            'publication_types': [],
            'language': '',
            'country': '',
            'nlm_unique_id': '',
            'issn_linking': ''
        }
        
        # Title
        if 'ArticleTitle' in article:
            info['title'] = str(article['ArticleTitle'])
        
        # Abstract
        if 'Abstract' in article and 'AbstractText' in article['Abstract']:
            abstract_parts = article['Abstract']['AbstractText']
            if isinstance(abstract_parts, list):
                info['abstract'] = ' '.join([str(part) for part in abstract_parts])
            else:
                info['abstract'] = str(abstract_parts)
        
        # Authors
        if 'AuthorList' in article:
            authors = []
            for author in article['AuthorList']:
                if 'LastName' in author and 'ForeName' in author:
                    full_name = f"{author['ForeName']} {author['LastName']}"
                    if 'Initials' in author:
                        full_name = f"{author['ForeName']} {author['Initials']} {author['LastName']}"
                    authors.append(full_name)
                elif 'CollectiveName' in author:
                    authors.append(str(author['CollectiveName']))
            info['authors'] = authors
        
        # Journal information
        journal = article['Journal']
        info['journal'] = str(journal.get('Title', ''))
        info['journal_abbrev'] = str(journal.get('ISOAbbreviation', ''))
        
        if 'ISSN' in journal:
            info['issn'] = str(journal['ISSN'])
        
        # Volume, Issue, Pages
        if 'JournalIssue' in journal:
            issue = journal['JournalIssue']
            info['volume'] = str(issue.get('Volume', ''))
            info['issue'] = str(issue.get('Issue', ''))
            
            # Publication date
            if 'PubDate' in issue:
                pub_date = issue['PubDate']
                year = pub_date.get('Year', '')
                month = pub_date.get('Month', '')
                day = pub_date.get('Day', '')
                info['pub_date'] = f"{year}-{month}-{day}".strip('-')
                info['pub_year'] = str(year)
        
        # Pages
        if 'Pagination' in article and 'MedlinePgn' in article['Pagination']:
            info['pages'] = str(article['Pagination']['MedlinePgn'])
        
        # DOI and other identifiers
        if 'ELocationID' in article:
            for eloc in article['ELocationID']:
                if eloc.attributes.get('EIdType') == 'doi':
                    info['doi'] = str(eloc)
        
        # Keywords
        if 'KeywordList' in medline_citation:
            keywords = []
            for keyword_list in medline_citation['KeywordList']:
                for keyword in keyword_list:
                    keywords.append(str(keyword))
            info['keywords'] = keywords
        
        # MeSH terms
        if 'MeshHeadingList' in medline_citation:
            mesh_terms = []
            for mesh_heading in medline_citation['MeshHeadingList']:
                descriptor = mesh_heading['DescriptorName']
                mesh_terms.append(str(descriptor))
            info['mesh_terms'] = mesh_terms
        
        # Publication types
        if 'PublicationTypeList' in article:
            pub_types = []
            for pub_type in article['PublicationTypeList']:
                pub_types.append(str(pub_type))
            info['publication_types'] = pub_types
        
        # Language
        if 'Language' in article:
            info['language'] = str(article['Language'][0])
        
        # Country and other journal info
        if 'MedlineJournalInfo' in medline_citation:
            journal_info = medline_citation['MedlineJournalInfo']
            info['country'] = str(journal_info.get('Country', ''))
            info['nlm_unique_id'] = str(journal_info.get('NlmUniqueID', ''))
            info['issn_linking'] = str(journal_info.get('ISSNLinking', ''))
        
        return info
    
    def save_to_csv(self, articles, filename=None):
        """
        Save articles to CSV file
        
        Args:
            articles (list): List of article dictionaries
            filename (str): Output filename (optional)
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pubmed_results_{timestamp}.csv"
        
        # Convert lists to strings for CSV
        for article in articles:
            for key, value in article.items():
                if isinstance(value, list):
                    article[key] = '; '.join(value)
        
        df = pd.DataFrame(articles)
        df.to_csv(filename, index=False)
        print(f"Results saved to {filename}")
        
        return filename
    
    def save_to_json(self, articles, filename=None):
        """
        Save articles to JSON file
        
        Args:
            articles (list): List of article dictionaries
            filename (str): Output filename (optional)
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pubmed_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to {filename}")
        return filename
    
    def display_summary(self, articles):
        """
        Display a summary of the retrieved articles
        
        Args:
            articles (list): List of article dictionaries
        """
        print(f"\n=== PUBMED SEARCH SUMMARY ===")
        print(f"Total articles retrieved: {len(articles)}")
        
        if articles:
            print(f"\nFirst article:")
            article = articles[0]
            print(f"  Title: {article['title'][:100]}...")
            print(f"  Authors: {', '.join(article['authors'][:3])}...")
            print(f"  Journal: {article['journal']}")
            print(f"  Year: {article['pub_year']}")
            print(f"  PMID: {article['pmid']}")
            
            # Count statistics
            journals = [a['journal'] for a in articles if a['journal']]
            years = [a['pub_year'] for a in articles if a['pub_year']]
            
            print(f"\nMost common journals:")
            journal_counts = pd.Series(journals).value_counts().head(5)
            for journal, count in journal_counts.items():
                print(f"  {journal}: {count} articles")
            
            print(f"\nPublication years:")
            year_counts = pd.Series(years).value_counts().head(5)
            for year, count in year_counts.items():
                print(f"  {year}: {count} articles")


