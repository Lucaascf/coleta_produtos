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
    
    # URLs para sistema de afiliados
    AFFILIATE_LOGIN_URL = "https://www.mercadolivre.com.br/hub/login"
    AFFILIATE_GENERATOR_URL = "https://www.mercadolivre.com.br/afiliados/linkbuilder#menu-lateral"
    AFFILIATE_DASHBOARD_URL = "https://www.mercadolivre.com.br/vendas"
    
    # Categorias do ML com IDs corretos - usando nomes reais do ML
    CATEGORIES = {
        "Eletrônicos, Áudio e Vídeo": "MLB1000",
        "Celulares e Telefones": "MLB1055", 
        "Informática": "MLB1648",
        "Casa, Móveis e Decoração": "MLB1574",
        "Eletrodomésticos e Casa": "MLB1556",
        "Roupas e Calçados": "MLB1430",
        "Esportes e Fitness": "MLB1276",
        "Livros, Revistas e Comics": "MLB3025",
        "Saúde e Beleza": "MLB263532",
        "Games": "MLB1144",
        "Carros, Motos e Outros": "MLB1743",
        "Relógios e Joias": "MLB1137"
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
    
    # Configurações específicas para afiliados
    AFFILIATE_CONTEXT_DIR = "affiliate_profile"  # Diretório para salvar contexto do browser
    AFFILIATE_BATCH_SIZE = 10  # Processar links em lotes
    AFFILIATE_DELAY_BETWEEN_LINKS = 2.0  # Delay entre processamento de links
    
    # Seletores CSS para automação do gerador de links
    AFFILIATE_SELECTORS = {
        "login_email": "input[name='email'], input[type='email'], #email",
        "login_password": "input[name='password'], input[type='password'], #password",
        "login_button": "button[type='submit'], .andes-button--primary, .btn-primary",
        "link_input": "input[placeholder*='link'], input[placeholder*='URL'], input[type='url'], .link-input, #url-input",
        "generate_button": "button:has-text('Gerar'), button:has-text('Criar'), button[type='submit'], .generate-btn, .btn-generate",
        "generated_link": ".generated-link, .affiliate-link, [data-testid='generated-link'], .result-link, .output-link",
        "copy_button": ".copy-btn, button[title*='Copiar'], [data-testid='copy-button']"
    }
    
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