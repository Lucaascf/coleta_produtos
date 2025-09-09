"""
Detector inteligente de produtos com adaptive learning
"""

import json
import re
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict, Counter
from bs4 import BeautifulSoup, Tag
import asyncio

class SmartProductDetector:
    """
    Detector que aprende dinamicamente os melhores seletores
    baseado no sucesso de extração de dados
    """
    
    def __init__(self):
        self.selector_success_rate: Dict[str, float] = {}
        self.selector_scores: Dict[str, int] = defaultdict(int)
        self.learned_patterns: Dict[str, List[str]] = {
            'product_containers': [],
            'titles': [],
            'prices': [],
            'images': [],
            'links': []
        }
        self.min_products_threshold = 5
        
    def analyze_page_structure(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Analisar estrutura da página para descobrir padrões"""
        
        candidates = {
            'product_containers': self._find_product_containers(soup),
            'titles': self._find_title_patterns(soup),
            'prices': self._find_price_patterns(soup),
            'images': self._find_image_patterns(soup),
            'links': self._find_link_patterns(soup)
        }
        
        return candidates
    
    def _find_product_containers(self, soup: BeautifulSoup) -> List[str]:
        """Encontrar containers de produtos"""
        potential_containers = []
        
        # Procurar por classes com nomes sugestivos
        product_keywords = [
            'product', 'item', 'result', 'card', 'listing',
            'search-result', 'ui-search', 'poly', 'andes'
        ]
        
        for keyword in product_keywords:
            # Classes que contém o keyword
            elements = soup.find_all(class_=re.compile(f'.*{keyword}.*', re.I))
            
            for element in elements:
                classes = element.get('class', [])
                for cls in classes:
                    if keyword.lower() in cls.lower():
                        selector = f'.{cls}'
                        if selector not in potential_containers:
                            potential_containers.append(selector)
        
        # Testar data-attributes
        data_elements = soup.find_all(attrs={'data-testid': True})
        for elem in data_elements:
            testid = elem.get('data-testid', '')
            if any(kw in testid.lower() for kw in ['item', 'product', 'result']):
                selector = f'[data-testid="{testid}"]'
                if selector not in potential_containers:
                    potential_containers.append(selector)
        
        # Ordenar por frequência
        container_counts = Counter()
        for selector in potential_containers:
            elements = soup.select(selector)
            if 5 <= len(elements) <= 100:  # Range realista para produtos
                container_counts[selector] = len(elements)
        
        return [selector for selector, _ in container_counts.most_common(10)]
    
    def _find_title_patterns(self, soup: BeautifulSoup) -> List[str]:
        """Encontrar padrões de títulos"""
        title_selectors = []
        
        # Headers tradicionais
        for tag in ['h1', 'h2', 'h3', 'h4']:
            if soup.select(tag):
                title_selectors.append(tag)
        
        # Classes com 'title'
        title_elements = soup.find_all(class_=re.compile(r'.*title.*', re.I))
        for elem in title_elements:
            classes = elem.get('class', [])
            for cls in classes:
                if 'title' in cls.lower():
                    selector = f'.{cls}'
                    if selector not in title_selectors:
                        title_selectors.append(selector)
        
        # Links com title attribute
        links_with_title = soup.find_all('a', title=True)
        if len(links_with_title) > 10:
            title_selectors.append('a[title]')
        
        return title_selectors
    
    def _find_price_patterns(self, soup: BeautifulSoup) -> List[str]:
        """Encontrar padrões de preços"""
        price_selectors = []
        
        # Procurar por classes com keywords de preço
        price_keywords = ['price', 'amount', 'money', 'fraction', 'cost', 'valor']
        
        for keyword in price_keywords:
            elements = soup.find_all(class_=re.compile(f'.*{keyword}.*', re.I))
            for elem in elements:
                classes = elem.get('class', [])
                for cls in classes:
                    if keyword.lower() in cls.lower():
                        selector = f'.{cls}'
                        if selector not in price_selectors:
                            price_selectors.append(selector)
        
        # Elementos que contêm símbolos de moeda
        currency_elements = soup.find_all(text=re.compile(r'R\$|USD|\$|€|£'))
        for elem in currency_elements:
            if hasattr(elem, 'parent') and elem.parent:
                parent_classes = elem.parent.get('class', [])
                for cls in parent_classes:
                    selector = f'.{cls}'
                    if selector not in price_selectors:
                        price_selectors.append(selector)
        
        return price_selectors
    
    def _find_image_patterns(self, soup: BeautifulSoup) -> List[str]:
        """Encontrar padrões de imagens"""
        image_selectors = ['img[src]', 'img[data-src]']
        
        # Classes específicas de imagem
        img_keywords = ['image', 'img', 'photo', 'picture', 'thumb']
        
        for keyword in img_keywords:
            elements = soup.find_all(class_=re.compile(f'.*{keyword}.*', re.I))
            for elem in elements:
                if elem.name == 'img' or elem.find('img'):
                    classes = elem.get('class', [])
                    for cls in classes:
                        if keyword.lower() in cls.lower():
                            selector = f'.{cls} img' if elem.name != 'img' else f'.{cls}'
                            if selector not in image_selectors:
                                image_selectors.append(selector)
        
        return image_selectors
    
    def _find_link_patterns(self, soup: BeautifulSoup) -> List[str]:
        """Encontrar padrões de links"""
        link_selectors = ['a[href]']
        
        # Links com classes específicas
        link_keywords = ['link', 'url', 'href', 'goto']
        
        for keyword in link_keywords:
            elements = soup.find_all('a', class_=re.compile(f'.*{keyword}.*', re.I))
            for elem in elements:
                classes = elem.get('class', [])
                for cls in classes:
                    if keyword.lower() in cls.lower():
                        selector = f'a.{cls}'
                        if selector not in link_selectors:
                            link_selectors.append(selector)
        
        return link_selectors
    
    def test_selectors(self, soup: BeautifulSoup, candidates: Dict[str, List[str]]) -> Dict[str, str]:
        """Testar seletores e escolher os melhores"""
        
        best_selectors = {}
        
        # Testar containers de produto
        container_selector = self._test_product_containers(soup, candidates['product_containers'])
        if container_selector:
            best_selectors['container'] = container_selector
            
            # Testar outros seletores dentro dos containers
            container_elements = soup.select(container_selector)[:10]  # Teste com primeiros 10
            
            if container_elements:
                best_selectors['title'] = self._test_element_selectors(
                    container_elements, candidates['titles']
                )
                best_selectors['price'] = self._test_price_selectors(
                    container_elements, candidates['prices']
                )
                best_selectors['image'] = self._test_element_selectors(
                    container_elements, candidates['images']
                )
                best_selectors['link'] = self._test_element_selectors(
                    container_elements, candidates['links']
                )
        
        return best_selectors
    
    def _test_product_containers(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Testar seletores de container e escolher o melhor"""
        
        best_selector = None
        best_score = 0
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                count = len(elements)
                
                if count < self.min_products_threshold:
                    continue
                
                # Calcular score baseado em diversos fatores
                score = 0
                
                # Quantidade (ideal entre 10-50 produtos)
                if 10 <= count <= 50:
                    score += 10
                elif 5 <= count < 10:
                    score += 5
                elif count > 50:
                    score += max(0, 10 - (count - 50) // 10)
                
                # Verificar se elementos têm conteúdo substancial
                substantial_elements = 0
                for elem in elements[:10]:
                    text_length = len(elem.get_text(strip=True))
                    if text_length > 20:  # Pelo menos 20 caracteres
                        substantial_elements += 1
                
                score += substantial_elements * 2
                
                # Verificar se contêm sub-elementos típicos
                for elem in elements[:5]:
                    if elem.find('img'):
                        score += 1
                    if elem.find('a'):
                        score += 1
                    if re.search(r'\d+', elem.get_text()):  # Contém números (preços)
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_selector = selector
                    
            except Exception:
                continue
        
        return best_selector
    
    def _test_element_selectors(self, container_elements: List, selectors: List[str]) -> Optional[str]:
        """Testar seletores de elementos específicos"""
        
        best_selector = None
        best_score = 0
        
        for selector in selectors:
            try:
                success_count = 0
                total_count = len(container_elements)
                
                for container in container_elements:
                    element = container.select_one(selector)
                    if element and element.get_text(strip=True):
                        success_count += 1
                
                # Taxa de sucesso
                success_rate = success_count / total_count if total_count > 0 else 0
                
                if success_rate > 0.5 and success_count > best_score:
                    best_score = success_count
                    best_selector = selector
                    
            except Exception:
                continue
        
        return best_selector
    
    def _test_price_selectors(self, container_elements: List, selectors: List[str]) -> Optional[str]:
        """Testar seletores de preço com validação específica"""
        
        best_selector = None
        best_score = 0
        
        for selector in selectors:
            try:
                success_count = 0
                
                for container in container_elements:
                    element = container.select_one(selector)
                    if element:
                        text = element.get_text(strip=True)
                        # Verificar se parece um preço
                        if re.search(r'\d+[,.]\d+|\d+', text) and len(text) <= 20:
                            success_count += 1
                
                if success_count > best_score and success_count >= 3:
                    best_score = success_count
                    best_selector = selector
                    
            except Exception:
                continue
        
        return best_selector
    
    def learn_from_page(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Aprender padrões de uma página"""
        
        print("🧠 Analisando estrutura da página...")
        
        # Analisar estrutura
        candidates = self.analyze_page_structure(soup)
        
        print(f"🔍 Encontrados {len(candidates['product_containers'])} containers candidatos")
        
        # Testar seletores
        best_selectors = self.test_selectors(soup, candidates)
        
        # Salvar aprendizado
        for key, selector in best_selectors.items():
            if selector:
                self.selector_scores[selector] += 1
                print(f"✅ Melhor seletor para {key}: {selector}")
        
        return best_selectors
    
    def get_best_selectors(self) -> Dict[str, List[str]]:
        """Retornar os melhores seletores aprendidos"""
        
        # Ordenar por score
        sorted_selectors = sorted(
            self.selector_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # Agrupar por tipo
        result = defaultdict(list)
        
        for selector, score in sorted_selectors:
            if score >= 2:  # Mínimo 2 sucessos
                # Categorizar seletor
                if any(kw in selector.lower() for kw in ['title', 'h1', 'h2', 'h3']):
                    result['titles'].append(selector)
                elif any(kw in selector.lower() for kw in ['price', 'amount', 'money']):
                    result['prices'].append(selector)
                elif 'img' in selector.lower():
                    result['images'].append(selector)
                elif selector.startswith('a'):
                    result['links'].append(selector)
                else:
                    result['containers'].append(selector)
        
        return dict(result)