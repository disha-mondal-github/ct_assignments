import requests
from bs4 import BeautifulSoup
from googlesearch import search
import time
import random
from typing import List, Dict
from fake_useragent import UserAgent
import re
from urllib.parse import urljoin, urlparse
import logging

class WebScraper:
    """Web scraper for legal information and recent cases"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Trusted legal sources for Indian law
        self.trusted_sources = [
            'indiankanoon.org',
            'main.sci.gov.in',
            'livelaw.in',
            'barandbench.com',
            'theleaflet.in',
            'scobserver.in',
            'legally.co.in',
            'taxguru.in'
        ]
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def is_trusted_source(self, url: str) -> bool:
        """Check if URL is from a trusted legal source"""
        try:
            domain = urlparse(url).netloc.lower()
            return any(source in domain for source in self.trusted_sources)
        except:
            return False
    
    def google_search_legal(self, query: str, num_results: int = 5) -> List[str]:
        """Search Google for legal information with Indian law focus"""
        try:
            # Add Indian legal context to query
            enhanced_query = f"{query} India law judgment case site:indiankanoon.org OR site:livelaw.in OR site:barandbench.com"
            
            urls = []
            search_results = search(enhanced_query, num_results=num_results * 2, stop=num_results * 2, pause=2)
            
            for url in search_results:
                if self.is_trusted_source(url):
                    urls.append(url)
                    if len(urls) >= num_results:
                        break
                        
            # If not enough trusted sources, search more broadly
            if len(urls) < 3:
                broader_query = f"{query} Supreme Court India High Court judgment 2024 2023"
                broader_results = search(broader_query, num_results=10, stop=10, pause=2)
                
                for url in broader_results:
                    if url not in urls and len(urls) < num_results:
                        urls.append(url)
            
            return urls[:num_results]
            
        except Exception as e:
            self.logger.error(f"Google search error: {str(e)}")
            return []
    
    def extract_text_from_url(self, url: str) -> Dict:
        """Extract relevant text content from a URL"""
        try:
            # Random delay to avoid being blocked
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header", "sidebar"]):
                script.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title"
            
            # Extract main content
            content_selectors = [
                'article', 'main', '.content', '.post-content', 
                '.judgment-text', '.case-content', '.legal-content',
                'div[class*="content"]', 'div[class*="article"]'
            ]
            
            content_text = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content_text = content_elem.get_text(separator=' ', strip=True)
                    break
            
            # If no specific content found, get body text
            if not content_text:
                content_text = soup.get_text(separator=' ', strip=True)
            
            # Clean up text
            content_text = re.sub(r'\s+', ' ', content_text)
            content_text = content_text[:3000]  # Limit content length
            
            return {
                'url': url,
                'title': title_text,
                'content': content_text,
                'source': urlparse(url).netloc
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting from {url}: {str(e)}")
            return {
                'url': url,
                'title': 'Error loading page',
                'content': 'Could not extract content from this page',
                'source': urlparse(url).netloc if url else 'unknown'
            }
    
    def search_recent_cases(self, query: str) -> List[Dict]:
        """Search for recent legal cases and information"""
        self.logger.info(f"Searching for recent cases: {query}")
        
        # Get URLs from Google search
        urls = self.google_search_legal(query, num_results=5)
        
        if not urls:
            return []
        
        # Extract content from URLs
        results = []
        for url in urls:
            content_data = self.extract_text_from_url(url)
            if content_data['content'] and len(content_data['content']) > 100:
                results.append(content_data)
        
        return results
    
    def search_legal_definition(self, term: str) -> List[Dict]:
        """Search for legal definitions and explanations"""
        query = f"legal definition {term} Indian law meaning explanation"
        return self.search_recent_cases(query)
    
    def search_case_law(self, case_name_or_topic: str) -> List[Dict]:
        """Search for specific case law or legal precedents"""
        queries = [
            f"{case_name_or_topic} Supreme Court India judgment",
            f"{case_name_or_topic} High Court India case law",
            f"{case_name_or_topic} legal precedent India"
        ]
        
        all_results = []
        for query in queries:
            results = self.search_recent_cases(query)
            all_results.extend(results)
            if len(all_results) >= 5:
                break
        
        # Remove duplicates based on URL
        unique_results = []
        seen_urls = set()
        for result in all_results:
            if result['url'] not in seen_urls:
                unique_results.append(result)
                seen_urls.add(result['url'])
        
        return unique_results[:5]
    
    def detect_query_type(self, query: str) -> str:
        """Detect the type of legal query to optimize search"""
        query_lower = query.lower()
        
        recent_keywords = ['recent', 'latest', 'new', '2024', '2023', 'current', 'today']
        case_keywords = ['case', 'judgment', 'ruling', 'decision', 'precedent']
        definition_keywords = ['what is', 'define', 'definition', 'meaning', 'explain']
        
        if any(keyword in query_lower for keyword in recent_keywords):
            return 'recent'
        elif any(keyword in query_lower for keyword in case_keywords):
            return 'case_law'
        elif any(keyword in query_lower for keyword in definition_keywords):
            return 'definition'
        else:
            return 'general'
    
    def comprehensive_legal_search(self, query: str) -> Dict:
        """Perform comprehensive legal search based on query type"""
        query_type = self.detect_query_type(query)
        
        if query_type == 'recent':
            search_query = f"{query} 2024 2023 latest judgment"
        elif query_type == 'case_law':
            search_query = f"{query} Supreme Court High Court precedent"
        elif query_type == 'definition':
            search_query = f"{query} Indian law definition legal meaning"
        else:
            search_query = query
        
        results = self.search_recent_cases(search_query)
        
        return {
            'query_type': query_type,
            'results': results,
            'total_results': len(results)
        }