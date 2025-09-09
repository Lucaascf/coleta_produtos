#!/usr/bin/env python3
"""
Script de Debug - Investigar Estrutura de Preços do Mercado Livre
Objetivo: Identificar seletores CSS corretos para preços originais (de/por)
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

class PriceStructureDebugger:
    """Debugger para estrutura de preços do ML"""
    
    def __init__(self):
        self.results = {
            "analysis_date": datetime.now().isoformat(),
            "pages_analyzed": [],
            "price_structures": [],
            "selector_candidates": [],
            "recommendations": []
        }
    
    async def analyze_price_structures(self):
        """Analisar estruturas de preço em diferentes páginas"""
        
        # URLs para testar (com produtos que provavelmente têm desconto)
        test_urls = [
            "https://www.mercadolivre.com.br/ofertas",
            "https://lista.mercadolivre.com.br/air-fryer",
            "https://lista.mercadolivre.com.br/smartphone",
            "https://www.mercadolivre.com.br/c/MLB1055",  # Celulares
        ]
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=500)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            for url in test_urls:
                print(f"\n🔍 ANALISANDO: {url}")
                self.results["pages_analyzed"].append(url)
                
                try:
                    # Navegar para página
                    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    await asyncio.sleep(3)
                    
                    # Obter HTML
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Analisar estruturas de preço
                    await self._analyze_page_prices(page, soup, url)
                    
                except Exception as e:
                    print(f"❌ Erro ao analisar {url}: {e}")
                    continue
            
            await browser.close()
        
        # Salvar resultados
        await self._save_analysis()
    
    async def _analyze_page_prices(self, page, soup, url):
        """Analisar preços de uma página específica"""
        
        print("🔍 Procurando produtos com preços...")
        
        # Seletores para containers de produtos
        product_selectors = [
            '.ui-search-result',
            '.poly-card', 
            '.andes-card',
            '[data-testid*="result"]'
        ]
        
        products_found = 0
        
        for selector in product_selectors:
            elements = soup.select(selector)
            
            if elements and len(elements) > 3:
                print(f"✅ Usando seletor: {selector} ({len(elements)} elementos)")
                
                for i, element in enumerate(elements[:5]):  # Analisar primeiros 5
                    product_analysis = {
                        "url": url,
                        "product_index": i,
                        "product_selector": selector,
                        "price_elements": [],
                        "price_candidates": []
                    }
                    
                    # Encontrar todos elementos com classes relacionadas a preço
                    price_elements = element.find_all(attrs={
                        'class': lambda x: x and any(keyword in str(x).lower() for keyword in 
                                ['price', 'money', 'amount', 'cost', 'valor'])
                    })
                    
                    for price_elem in price_elements:
                        elem_info = {
                            "tag": price_elem.name,
                            "classes": price_elem.get('class', []),
                            "text": price_elem.get_text(strip=True),
                            "html": str(price_elem)[:200]  # Limitar tamanho
                        }
                        product_analysis["price_elements"].append(elem_info)
                        
                        # Identificar candidatos a preço original vs atual
                        text = price_elem.get_text(strip=True)
                        classes = ' '.join(price_elem.get('class', []))
                        
                        # Critérios para preço original (riscado)
                        is_original_candidate = any([
                            price_elem.name in ['s', 'del', 'strike'],
                            'previous' in classes.lower(),
                            'original' in classes.lower(), 
                            'old' in classes.lower(),
                            'strikethrough' in classes.lower(),
                            price_elem.parent and price_elem.parent.name in ['s', 'del']
                        ])
                        
                        # Critérios para preço atual
                        is_current_candidate = any([
                            'current' in classes.lower(),
                            'final' in classes.lower(),
                            'main' in classes.lower(),
                            not is_original_candidate
                        ])
                        
                        candidate_info = {
                            "element_selector": self._generate_css_selector(price_elem),
                            "text": text,
                            "type": "original" if is_original_candidate else ("current" if is_current_candidate else "unknown"),
                            "confidence": 0.8 if is_original_candidate or is_current_candidate else 0.3
                        }
                        
                        product_analysis["price_candidates"].append(candidate_info)
                    
                    if product_analysis["price_elements"]:
                        self.results["price_structures"].append(product_analysis)
                        products_found += 1
                
                break  # Usar primeiro seletor que funcionar
        
        print(f"📦 Analisados {products_found} produtos em {url}")
    
    def _generate_css_selector(self, element):
        """Gerar seletor CSS para um elemento"""
        try:
            selectors = []
            
            # Tag
            tag = element.name
            
            # Classes
            classes = element.get('class', [])
            if classes:
                class_str = '.' + '.'.join(classes)
                selectors.append(f"{tag}{class_str}")
            
            # Atributos especiais
            for attr in ['data-testid', 'data-cy', 'id']:
                if element.get(attr):
                    selectors.append(f"{tag}[{attr}='{element[attr]}']")
            
            # Seletor baseado no parent
            if element.parent:
                parent_classes = element.parent.get('class', [])
                if parent_classes:
                    parent_class = '.' + '.'.join(parent_classes[:2])  # Primeiras 2 classes
                    selectors.append(f"{parent_class} {tag}")
            
            return selectors[0] if selectors else tag
            
        except Exception:
            return str(element.name)
    
    async def _save_analysis(self):
        """Salvar análise em arquivo"""
        
        # Gerar recomendações baseadas na análise
        self._generate_recommendations()
        
        # Salvar JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"price_structure_analysis_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Análise salva em: {filename}")
        print(f"📊 Páginas analisadas: {len(self.results['pages_analyzed'])}")
        print(f"📦 Produtos analisados: {len(self.results['price_structures'])}")
        print(f"🎯 Candidatos a seletores: {len(self.results['selector_candidates'])}")
        
        # Mostrar primeiras recomendações
        print("\n🔧 PRINCIPAIS RECOMENDAÇÕES:")
        for i, rec in enumerate(self.results['recommendations'][:5], 1):
            print(f"{i}. {rec}")
    
    def _generate_recommendations(self):
        """Gerar recomendações baseadas na análise"""
        
        # Contar seletores mais frequentes
        selector_frequency = {}
        original_selectors = []
        current_selectors = []
        
        for product in self.results["price_structures"]:
            for candidate in product.get("price_candidates", []):
                selector = candidate["element_selector"]
                selector_frequency[selector] = selector_frequency.get(selector, 0) + 1
                
                if candidate["type"] == "original":
                    original_selectors.append(selector)
                elif candidate["type"] == "current":
                    current_selectors.append(selector)
        
        # Top seletores
        top_selectors = sorted(selector_frequency.items(), key=lambda x: x[1], reverse=True)
        
        self.results["selector_candidates"] = [
            {"selector": sel, "frequency": freq, "type": "general"} 
            for sel, freq in top_selectors[:10]
        ]
        
        # Recomendações
        recommendations = []
        
        if original_selectors:
            most_common_original = max(set(original_selectors), key=original_selectors.count)
            recommendations.append(f"Seletor para preço original: {most_common_original}")
        
        if current_selectors:
            most_common_current = max(set(current_selectors), key=current_selectors.count)
            recommendations.append(f"Seletor para preço atual: {most_common_current}")
        
        recommendations.extend([
            "Testar seletores em ordem de frequência encontrada",
            "Implementar validação: preço_original > preço_atual",
            "Adicionar fallbacks para diferentes tipos de página",
            "Usar BeautifulSoup para análise mais robusta de elementos riscados"
        ])
        
        self.results["recommendations"] = recommendations

async def main():
    """Função principal"""
    print("🔍 INICIANDO DEBUG DE ESTRUTURAS DE PREÇO DO ML")
    print("="*50)
    
    debugger = PriceStructureDebugger()
    await debugger.analyze_price_structures()
    
    print("\n✅ Debug concluído!")
    print("Verifique o arquivo JSON gerado para detalhes completos.")

if __name__ == "__main__":
    asyncio.run(main())