"""
Engine de Scraping com Playwright - Anti-detecção avançada
"""

import asyncio
import random
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from bs4 import BeautifulSoup

from ..config import ScraperConfig
from ..utils.stealth import StealthMode
from ..utils.validators import Product, DataProcessor, ProductClassifier

class PlaywrightEngine:
    """Engine principal usando Playwright com recursos anti-detecção"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.config = ScraperConfig()
        
        # Cache de categorias para evitar requisições repetidas
        self.category_cache = {}
        
    async def __aenter__(self):
        """Context manager entry"""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
    
    async def start(self) -> None:
        """Inicializar browser com configurações stealth"""
        try:
            self.playwright = await async_playwright().start()
            
            # Configurações do browser - OTIMIZADO para performance
            self.browser = await self.playwright.chromium.launch(
                headless=True,   # Navegador invisível para performance
                args=self.config.get_playwright_args()
            )
            
            # Context com configurações realistas
            self.context = await self.browser.new_context(
                user_agent=self.config.get_random_user_agent(),
                viewport={'width': random.randint(1200, 1920), 'height': random.randint(800, 1080)},
                locale='pt-BR',
                timezone_id='America/Sao_Paulo',
                extra_http_headers=self.config.get_stealth_headers()
            )
            
            # Página principal
            self.page = await self.context.new_page()
            
            # Configurar modo stealth
            await StealthMode.setup_stealth(self.page)
            
            print("✅ Engine Playwright iniciada com sucesso")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar Playwright: {e}")
            raise
    
    async def close(self) -> None:
        """Fechar browser e recursos"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            print("🔧 Engine Playwright fechada")
        except Exception as e:
            print(f"⚠️ Erro ao fechar Playwright: {e}")
    
    async def navigate_to_page(self, url: str, wait_for_selector: str = None) -> bool:
        """Navegar para uma página com tratamento de erros"""
        try:
            # Navegar diretamente sem logs verbosos
            response = await self.page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            if not response or response.status >= 400:
                return False
                
            # Aguardar JavaScript carregar (reduzido)
            await asyncio.sleep(2)
            
            # Contornar proteções silenciosamente
            await StealthMode.bypass_cloudflare(self.page)
            await StealthMode.wait_for_page_load(self.page)
            
            # Aguardar seletor específico se fornecido
            if wait_for_selector:
                try:
                    await self.page.wait_for_selector(wait_for_selector, timeout=10000)
                except:
                    pass  # Continuar mesmo sem o seletor
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao navegar: {e}")
            return False
    
    async def extract_products_from_page(self, url: str) -> List[Product]:
        """Extrair produtos de uma página"""
        if not await self.navigate_to_page(url):
            return []
        
        try:
            # Aguardar produtos carregarem (otimizado)
            await asyncio.sleep(1)
            
            # Obter HTML da página
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Diferentes seletores para produtos
            product_selectors = [
                '.ui-search-result',
                '.ui-search-results__item',
                'article[data-testid]',
                '.poly-card',
                '.andes-card',
                '[class*="item"]'
            ]
            
            products = []
            
            for selector in product_selectors:
                elements = soup.select(selector)
                
                if elements and len(elements) > 1:  # Só usar seletores com produtos válidos
                    for element in elements[:50]:  # Limitar para evitar sobrecarga
                        product = await self._extract_single_product(element)
                        if product:
                            products.append(product)
                    break
            
            return products
            
        except Exception as e:
            return []
    
    async def extract_category_from_product_page(self, product_url: str) -> tuple[Optional[str], float]:
        """Extrair categoria real da página individual do produto via breadcrumb"""
        if not product_url:
            return None, 0.0
        
        # Verificar cache primeiro
        url_key = product_url.split('?')[0]  # Remover parâmetros da URL
        if url_key in self.category_cache:
            cached_result = self.category_cache[url_key]
            return cached_result['category'], cached_result['confidence']
        
        try:
            # Navegar para página do produto
            response = await self.page.goto(product_url, wait_until='domcontentloaded', timeout=30000)
            if not response or response.status >= 400:
                return None, 0.0
            
            # Aguardar página carregar
            await asyncio.sleep(1)
            
            # Buscar breadcrumb com categoria real
            breadcrumb_selectors = [
                '.andes-breadcrumb__item a',  # Breadcrumb padrão
                '.ui-navigation-link',        # Navegação alternativa
                '.breadcrumb a',              # Breadcrumb genérico
                '[data-testid="breadcrumb"] a'  # Breadcrumb com test-id
            ]
            
            for selector in breadcrumb_selectors:
                elements = await self.page.query_selector_all(selector)
                if elements and len(elements) > 1:  # Pular "Início"
                    for element in elements[1:]:  # Começar do segundo item
                        text = await element.inner_text()
                        if text and len(text.strip()) > 3:
                            # Limpar e formatar categoria
                            category = text.strip()
                            # Pular termos muito genéricos
                            if category.lower() not in ['início', 'home', 'mercado livre', 'ml']:
                                # Adicionar ao cache
                                self.category_cache[url_key] = {
                                    'category': category,
                                    'confidence': 0.9
                                }
                                return category, 0.9  # Alta confiança para breadcrumb
            
            # Fallback: buscar na meta description ou title
            title = await self.page.title()
            if title and 'mercado livre' in title.lower():
                # Tentar extrair categoria do title
                parts = title.split('|')
                if len(parts) > 1:
                    potential_category = parts[-1].strip()
                    if potential_category != 'Mercado Livre':
                        # Adicionar ao cache
                        self.category_cache[url_key] = {
                            'category': potential_category,
                            'confidence': 0.6
                        }
                        return potential_category, 0.6
            
            # Cache resultado negativo para evitar tentar novamente
            self.category_cache[url_key] = {
                'category': None,
                'confidence': 0.0
            }
            return None, 0.0
            
        except Exception as e:
            # Cache resultado negativo para evitar tentar novamente
            self.category_cache[url_key] = {
                'category': None,
                'confidence': 0.0
            }
            return None, 0.0

    async def _extract_single_product(self, element) -> Optional[Product]:
        """Extrair dados de um único produto"""
        try:
            # Nome do produto - buscar especificamente títulos de produtos
            name = None
            name_selectors = [
                '.poly-component__title',  # Título nas ofertas
                '.ui-search-item__title a',  # Título na busca normal
                'h3 a',  # Link do título
                '.ui-search-item__title',
                'h2 a', 'h3'
            ]
            
            for selector in name_selectors:
                name_elem = element.select_one(selector)
                if name_elem:
                    text = name_elem.get_text(strip=True) or name_elem.get('title', '')
                    if text and len(text) > 10 and not any(skip in text.lower() for skip in ['economiza', 'confira', 'ofertas']):
                        name = text
                        break
            
            if not name:
                return None
            
            # Preço atual - buscar especificamente preço não riscado
            price = None
            price_selectors = [
                '.poly-price__current .andes-money-amount__fraction',  # Preço atual nas ofertas - CORRETO
                '.andes-money-amount--cents-superscript .andes-money-amount__fraction',  # Preço atual alternativo
                '.ui-search-price__second-line .andes-money-amount__fraction',  # Busca normal
                '.poly-component__price .andes-money-amount:not(.andes-money-amount--previous) .andes-money-amount__fraction',  # Não riscado
                '.andes-money-amount:not(.andes-money-amount--previous) .andes-money-amount__fraction'
            ]
            
            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price = DataProcessor.clean_price(price_text)
                    if price and price > 10:  # Validar preço mínimo razoável
                        break
            
            # Preço original (se em promoção) - buscar preços riscados - ATUALIZADOS
            original_price = None
            original_selectors = [
                's.andes-money-amount.andes-money-amount--previous .andes-money-amount__fraction',  # CORRETO - Ofertas
                's.andes-money-amount--previous .andes-money-amount__fraction',  # Variação
                '.andes-money-amount--previous .andes-money-amount__fraction',  # Preço anterior genérico
                '.ui-search-price__original-value .andes-money-amount__fraction',  # Busca normal
                's .andes-money-amount__fraction',  # Qualquer elemento riscado
                'del .andes-money-amount__fraction'  # Elemento deletado
            ]
            
            for selector in original_selectors:
                orig_elem = element.select_one(selector)
                if orig_elem:
                    original_text = orig_elem.get_text(strip=True)
                    potential_original = DataProcessor.clean_price(original_text)
                    
                    # VALIDAÇÃO CRÍTICA: preço original deve ser > preço atual
                    if potential_original and potential_original > 10:
                        if price and potential_original > price:
                            original_price = potential_original
                            break
                        elif not price:  # Se ainda não temos preço atual, aceitar
                            original_price = potential_original
                            break
            
            # URL do produto - buscar especificamente links de produtos
            product_url = None
            link_selectors = [
                '.poly-component__title[href]',  # Link do título nas ofertas
                'a.ui-search-link[href]',  # Link na busca normal
                'h3 a[href]',  # Link no título
                'a[href*="/p/"], a[href*="ML"]'  # Links que contenham produto
            ]
            
            for selector in link_selectors:
                link_elem = element.select_one(selector)
                if link_elem:
                    href = link_elem.get('href', '')
                    if href and ('ML' in href or '/p/' in href):
                        product_url = href if href.startswith('http') else f"{self.config.BASE_URL}{href}"
                        break
            
            # Imagem
            image_url = None
            img_elem = element.select_one('img[src], img[data-src]')
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
            
            # Verificar se é promoção
            element_text = element.get_text()
            is_promotion = (
                DataProcessor.is_promotion_indicator(element_text) or
                original_price is not None or
                'off' in element_text.lower()
            )
            
            # Frete grátis
            free_shipping = DataProcessor.has_free_shipping(element_text)
            
            # Validação obrigatória - produto deve ter nome, preço e URL
            if not all([name, price, product_url]):
                return None
            
            # Classificar produto automaticamente
            # Primeiro: tentar extrair categoria real da página do produto
            real_category, real_confidence = None, 0.0
            if product_url and len(product_url) < 200:  # Evitar URLs muito longas
                try:
                    real_category, real_confidence = await self.extract_category_from_product_page(product_url)
                except:
                    pass
            
            # Segundo: usar sistema de palavras-chave como fallback
            fallback_category, fallback_confidence = ProductClassifier.classify_product(
                name=name,
                url=product_url,
                description=""
            )
            
            # Escolher melhor classificação
            if real_category and real_confidence > 0.8:
                category, category_confidence = real_category, real_confidence
            elif fallback_category and fallback_confidence > real_confidence:
                category, category_confidence = fallback_category, fallback_confidence
            elif real_category:
                category, category_confidence = real_category, real_confidence
            else:
                category, category_confidence = fallback_category, fallback_confidence
            
            # Criar produto
            product_data = {
                'name': name,
                'price': price,
                'original_price': original_price,
                'url': product_url,
                'image_url': image_url,
                'is_promotion': is_promotion,
                'free_shipping': free_shipping,
                'product_id': DataProcessor.extract_product_id(product_url) if product_url else None,
                'category': category,
                'category_confidence': category_confidence
            }
            
            return Product(**product_data)
            
        except Exception as e:
            return None
    
    async def search_products(self, query: str, max_products: int = 50) -> List[Product]:
        """Buscar produtos por termo"""
        products = []
        page_num = 1
        
        while len(products) < max_products and page_num <= 5:
            # URL de busca
            offset = (page_num - 1) * 50
            search_url = f"{self.config.SEARCH_BASE}/{query.replace(' ', '-')}"
            if page_num > 1:
                search_url += f"_Desde_{offset + 1}"
            
            page_products = await self.extract_products_from_page(search_url)
            
            if not page_products:
                break
            
            products.extend(page_products)
            page_num += 1
            
            # Delay mínimo entre páginas
            await asyncio.sleep(1)
        
        return products[:max_products]
    
    def _filter_relevant_products(self, products: List[Product], search_term: str) -> List[Product]:
        """Filtrar produtos relevantes baseado no termo de busca"""
        if not search_term:
            return products
        
        search_words = search_term.lower().split()
        relevant_products = []
        
        for product in products:
            if not product.name:
                continue
            
            product_name = product.name.lower()
            
            # Calcular relevância - quantas palavras do termo aparecem no nome
            matches = sum(1 for word in search_words if word in product_name)
            relevance_score = matches / len(search_words)
            
            # Aceitar produtos com pelo menos 20% de relevância (mais flexível)
            if relevance_score >= 0.2:
                relevant_products.append(product)
            # Ou se o nome contém o termo completo
            elif search_term.lower() in product_name:
                relevant_products.append(product)
            # Ou se contém palavras-chave principais (primeira palavra é mais importante)
            elif search_words and search_words[0] in product_name:
                relevant_products.append(product)
        
        return relevant_products
    
    async def search_products_with_progress(self, query: str, max_products: int = 50, progress_callback=None) -> List[Product]:
        """Buscar produtos por termo com callback de progresso"""
        products = []
        page_num = 1
        
        while len(products) < max_products and page_num <= 5:
            # Callback de progresso
            if progress_callback:
                progress_callback(len(products), max_products, f"Buscando '{query}' - página {page_num}...")
            
            # URL de busca
            offset = (page_num - 1) * 50
            search_url = f"{self.config.SEARCH_BASE}/{query.replace(' ', '-')}"
            if page_num > 1:
                search_url += f"_Desde_{offset + 1}"
            
            page_products = await self.extract_products_from_page(search_url)
            
            if not page_products:
                break
            
            # Filtrar produtos relevantes
            relevant_products = self._filter_relevant_products(page_products, query)
            products.extend(relevant_products)
            page_num += 1
            
            # Delay mínimo entre páginas
            await asyncio.sleep(1)
        
        # Callback final
        if progress_callback:
            progress_callback(len(products), max_products, f"Finalizando busca...")
        
        return products[:max_products]
    
    def _find_category_id(self, category: str) -> str:
        """Encontrar ID da categoria de forma inteligente"""
        if not category:
            return None
        
        # Primeiro: busca exata (case-sensitive)
        if category in self.config.CATEGORIES:
            return self.config.CATEGORIES[category]
        
        # Segundo: busca case-insensitive
        for cat_name, cat_id in self.config.CATEGORIES.items():
            if cat_name.lower() == category.lower():
                return cat_id
        
        # Terceiro: busca por palavras-chave (compatibilidade com nomes antigos)
        category_mappings = {
            'eletronicos': 'Eletrônicos, Áudio e Vídeo',
            'celulares': 'Celulares e Telefones',
            'informatica': 'Informática',
            'casa': 'Casa, Móveis e Decoração',
            'eletrodomesticos': 'Eletrodomésticos e Casa',
            'moda': 'Roupas e Calçados',
            'esportes': 'Esportes e Fitness',
            'livros': 'Livros, Revistas e Comics',
            'beleza': 'Saúde e Beleza',
            'games': 'Games',
            'automotivo': 'Carros, Motos e Outros',
            'relogios': 'Relógios e Joias'
        }
        
        category_lower = category.lower()
        if category_lower in category_mappings:
            real_name = category_mappings[category_lower]
            return self.config.CATEGORIES.get(real_name)
        
        # Quarto: busca parcial (se a categoria contém palavras-chave)
        for cat_name, cat_id in self.config.CATEGORIES.items():
            if any(word in cat_name.lower() for word in category_lower.split()):
                return cat_id
        
        return None

    async def search_category_with_progress(self, category: str, max_products: int = 50, progress_callback=None) -> List[Product]:
        """Buscar produtos por categoria com callback de progresso"""
        category_id = self._find_category_id(category)
        
        if not category_id:
            if progress_callback:
                progress_callback(0, max_products, f"❌ Categoria '{category}' não encontrada")
            return []
        
        products = []
        page_num = 1
        
        while len(products) < max_products and page_num <= 5:
            # Callback de progresso
            if progress_callback:
                progress_callback(len(products), max_products, f"Buscando categoria '{category}' - página {page_num}...")
            
            # URL da categoria
            offset = (page_num - 1) * 50
            category_url = f"{self.config.BASE_URL}/c/{category_id}"
            if page_num > 1:
                category_url += f"#D[A:{offset + 1}]"
            
            page_products = await self.extract_products_from_page(category_url)
            
            if not page_products:
                break
            
            products.extend(page_products)
            page_num += 1
            
            # Delay mínimo entre páginas
            await asyncio.sleep(1)
        
        # Callback final
        if progress_callback:
            progress_callback(len(products), max_products, f"Finalizando busca por categoria...")
        
        return products[:max_products]
    
    async def search_offers_with_progress(self, max_products: int = 50, progress_callback=None) -> List[Product]:
        """Buscar produtos em oferta com callback de progresso"""
        products = []
        page_num = 1
        
        while len(products) < max_products and page_num <= 5:
            # Callback de progresso
            if progress_callback:
                progress_callback(len(products), max_products, f"Buscando ofertas - página {page_num}...")
            
            # URL das ofertas com paginação
            if page_num == 1:
                offers_url = f"{self.config.BASE_URL}/ofertas"
            else:
                offset = (page_num - 1) * 50
                offers_url = f"{self.config.BASE_URL}/ofertas#D[A:{offset + 1}]"
            
            page_products = await self.extract_products_from_page(offers_url)
            
            if not page_products:
                break
            
            # Filtrar apenas produtos com desconto real
            promotion_products = [p for p in page_products if p.original_price and p.discount_percentage > 0]
            products.extend(promotion_products)
            
            page_num += 1
            
            # Delay mínimo entre páginas
            if page_num <= 5:  # Só delay se vai continuar
                await asyncio.sleep(1)
        
        # Callback final
        if progress_callback:
            progress_callback(len(products), max_products, f"Finalizando busca de ofertas...")
        
        return products[:max_products]
    
    async def search_category(self, category: str, max_products: int = 50) -> List[Product]:
        """Buscar produtos por categoria"""
        category_id = self._find_category_id(category)
        
        if not category_id:
            print(f"❌ Categoria '{category}' não encontrada")
            return []
        
        products = []
        page_num = 1
        
        while len(products) < max_products and page_num <= 5:
            # URL da categoria
            offset = (page_num - 1) * 50
            category_url = f"{self.config.BASE_URL}/c/{category_id}"
            if page_num > 1:
                category_url += f"#D[A:{offset + 1}]"
            
            page_products = await self.extract_products_from_page(category_url)
            
            if not page_products:
                break
            
            products.extend(page_products)
            page_num += 1
            
            # Delay mínimo entre páginas
            await asyncio.sleep(1)
        
        return products[:max_products]
    
    async def search_offers(self, max_products: int = 50) -> List[Product]:
        """Buscar produtos em oferta percorrendo múltiplas páginas"""
        products = []
        page_num = 1
        
        while len(products) < max_products and page_num <= 5:
            # URL das ofertas com paginação
            if page_num == 1:
                offers_url = f"{self.config.BASE_URL}/ofertas"
            else:
                offset = (page_num - 1) * 50
                offers_url = f"{self.config.BASE_URL}/ofertas#D[A:{offset + 1}]"
            
            page_products = await self.extract_products_from_page(offers_url)
            
            if not page_products:
                break
            
            # Filtrar apenas produtos com desconto real
            promotion_products = [p for p in page_products if p.original_price and p.discount_percentage > 0]
            products.extend(promotion_products)
            
            page_num += 1
            
            # Delay mínimo entre páginas
            if page_num <= 5:  # Só delay se vai continuar
                await asyncio.sleep(1)
        
        return products[:max_products]