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
from ..utils.validators import Product, DataProcessor

class PlaywrightEngine:
    """Engine principal usando Playwright com recursos anti-detecção"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.config = ScraperConfig()
        
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
            
            # Configurações do browser - VISÍVEL para debug
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # NAVEGADOR VISÍVEL!
                slow_mo=1000,    # Slow motion para ver o que acontece
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
            print(f"🌐 NAVEGANDO PARA: {url}")
            print(f"⏳ Aguarde, o navegador será aberto...")
            
            # Navegar
            print("🚀 Carregando página...")
            response = await self.page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            if not response or response.status >= 400:
                print(f"❌ Erro HTTP: {response.status if response else 'Sem resposta'}")
                return False
                
            print(f"✅ Página carregada! Status: {response.status}")
            
            # Aguardar um pouco mais para carregar JavaScript
            print("⏳ Aguardando JavaScript carregar...")
            await asyncio.sleep(3)
            
            # Verificar se a página tem conteúdo
            title = await self.page.title()
            print(f"📄 Título da página: {title}")
            
            # Contornar proteções
            print("🛡️ Verificando proteções anti-bot...")
            if not await StealthMode.bypass_cloudflare(self.page):
                print("⚠️ Possível bloqueio detectado")
            
            # Aguardar carregamento completo
            print("⏳ Aguardando carregamento completo...")
            if not await StealthMode.wait_for_page_load(self.page):
                print("⚠️ Timeout no carregamento da página")
            
            # Aguardar seletor específico se fornecido
            if wait_for_selector:
                print(f"🔍 Procurando seletor: {wait_for_selector}")
                try:
                    await self.page.wait_for_selector(wait_for_selector, timeout=15000)
                    print(f"✅ Seletor encontrado!")
                except:
                    print(f"⚠️ Seletor {wait_for_selector} não encontrado")
            
            # Tirar screenshot para debug
            print("📸 Salvando screenshot...")
            await self.page.screenshot(path=f"debug_screenshot_{asyncio.get_event_loop().time():.0f}.png")
            
            # Simular comportamento humano
            print("🤖 Simulando comportamento humano...")
            await StealthMode.random_mouse_movement(self.page)
            await StealthMode.human_scroll(self.page)
            
            print("✅ Navegação completa!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao navegar: {e}")
            return False
    
    async def extract_products_from_page(self, url: str) -> List[Product]:
        """Extrair produtos de uma página"""
        if not await self.navigate_to_page(url):
            return []
        
        try:
            # Aguardar produtos carregarem
            await asyncio.sleep(random.uniform(2, 4))
            
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
                
                if elements and len(elements) > 5:  # Só usar seletores com muitos resultados
                    print(f"✅ Usando seletor: {selector} ({len(elements)} produtos)")
                    
                    valid_products = 0
                    for element in elements[:50]:  # Limitar para evitar sobrecarga
                        product = await self._extract_single_product(element)
                        if product:
                            products.append(product)
                            valid_products += 1
                    
                    print(f"📦 Validados {valid_products} produtos de {len(elements)} elementos")
                    break
            
            print(f"📦 Extraídos {len(products)} produtos da página")
            return products
            
        except Exception as e:
            print(f"❌ Erro ao extrair produtos: {e}")
            return []
    
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
            
            # Criar produto
            product_data = {
                'name': name,
                'price': price,
                'original_price': original_price,
                'url': product_url,
                'image_url': image_url,
                'is_promotion': is_promotion,
                'free_shipping': free_shipping,
                'product_id': DataProcessor.extract_product_id(product_url) if product_url else None
            }
            
            return Product(**product_data)
            
        except Exception as e:
            print(f"⚠️ Erro ao extrair produto: {e}")
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
            
            print(f"🔍 Buscando página {page_num}: {query}")
            
            page_products = await self.extract_products_from_page(search_url)
            
            if not page_products:
                print(f"❌ Nenhum produto encontrado na página {page_num}")
                break
            
            products.extend(page_products)
            page_num += 1
            
            # Delay entre páginas
            await asyncio.sleep(random.uniform(2, 4))
        
        return products[:max_products]
    
    async def search_category(self, category: str, max_products: int = 50) -> List[Product]:
        """Buscar produtos por categoria"""
        category_id = self.config.CATEGORIES.get(category.lower())
        
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
            
            print(f"🏷️ Buscando categoria '{category}' - página {page_num}")
            
            page_products = await self.extract_products_from_page(category_url)
            
            if not page_products:
                print(f"❌ Nenhum produto encontrado na página {page_num}")
                break
            
            products.extend(page_products)
            page_num += 1
            
            # Delay entre páginas
            await asyncio.sleep(random.uniform(2, 4))
        
        return products[:max_products]
    
    async def search_offers(self, max_products: int = 50) -> List[Product]:
        """Buscar produtos em oferta"""
        offers_url = f"{self.config.BASE_URL}/ofertas"
        
        print("🔥 Buscando ofertas do Mercado Livre")
        
        products = await self.extract_products_from_page(offers_url)
        
        # Filtrar apenas produtos com desconto
        promotion_products = [p for p in products if p.is_promotion or p.original_price]
        
        return promotion_products[:max_products]