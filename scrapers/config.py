"""
Configurações do Sistema de Web Scraping
"""

import random
from typing import List, Dict
from fake_useragent import UserAgent

class ScraperConfig:
    """Configurações centralizadas do scraper"""
    
    # URLs base
    BASE_URL = "https://www.mercadolivre.com.br"
    SEARCH_BASE = "https://lista.mercadolivre.com.br"
    API_BASE = "https://api.mercadolibre.com"
    
    # Categorias do ML com IDs corretos
    CATEGORIES = {
        "eletronicos": "MLB1000",
        "celulares": "MLB1055", 
        "informatica": "MLB1648",
        "casa": "MLB1574",
        "moda": "MLB1430",
        "esportes": "MLB1276",
        "livros": "MLB3025",
        "beleza": "MLB263532",
        "games": "MLB1144",
        "automotivo": "MLB1743"
    }
    
    # User agents realistas
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
    ]
    
    # Configurações de timing
    MIN_DELAY = 1.0
    MAX_DELAY = 3.0
    PAGE_LOAD_TIMEOUT = 30000  # 30 segundos
    REQUEST_TIMEOUT = 15
    
    # Configurações de scraping
    MAX_RETRIES = 3
    MAX_PAGES_PER_SEARCH = 10
    MAX_PRODUCTS_PER_PAGE = 50
    
    # Configurações de cache
    CACHE_TTL = 3600  # 1 hora
    MAX_CACHE_SIZE = 1000
    
    @staticmethod
    def get_random_user_agent() -> str:
        """Retorna um user agent aleatório"""
        try:
            ua = UserAgent()
            return ua.random
        except:
            return random.choice(ScraperConfig.USER_AGENTS)
    
    @staticmethod
    def get_random_delay() -> float:
        """Retorna um delay aleatório entre requisições"""
        return random.uniform(ScraperConfig.MIN_DELAY, ScraperConfig.MAX_DELAY)
    
    @staticmethod
    def get_stealth_headers() -> Dict[str, str]:
        """Headers para evitar detecção"""
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Sec-CH-UA': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Linux"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': ScraperConfig.get_random_user_agent()
        }
    
    @staticmethod
    def get_playwright_args() -> List[str]:
        """Argumentos para o Playwright com anti-detecção"""
        return [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--disable-extensions',
            '--no-first-run',
            '--disable-default-apps',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-web-security',
            '--allow-running-insecure-content'
        ]