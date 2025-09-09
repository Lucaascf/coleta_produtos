"""
Validadores e processadores de dados
"""

import re
from typing import Optional, Dict, Any
from pydantic import BaseModel, validator, Field
from datetime import datetime

class Product(BaseModel):
    """Modelo de produto com validação"""
    
    name: str = Field(..., min_length=3)
    price: Optional[float] = None
    original_price: Optional[float] = None
    discount_percentage: float = 0.0
    url: Optional[str] = None
    image_url: Optional[str] = None
    seller: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    is_promotion: bool = False
    free_shipping: bool = False
    product_id: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.now)
    
    @validator('name')
    def validate_name(cls, v):
        """Validar e limpar nome do produto"""
        if not v or len(v.strip()) < 3:
            raise ValueError("Nome do produto muito curto")
        
        # Limpar texto
        clean_name = re.sub(r'\s+', ' ', v.strip())
        clean_name = re.sub(r'[^\w\sÀ-ÿ\-\(\)\[\]\/\+\.]', '', clean_name)
        
        return clean_name
    
    @validator('price', 'original_price')
    def validate_price(cls, v):
        """Validar preços - Ajustado para formato brasileiro"""
        if v is not None:
            if v < 1.0:  # Preço mínimo: R$ 1,00
                raise ValueError(f"Preço muito baixo: R$ {v:.2f}")
            if v > 1000000:  # Preço máximo: R$ 1 milhão
                raise ValueError(f"Preço muito alto: R$ {v:.2f}")
        return v
    
    @validator('discount_percentage', always=True)
    def validate_discount(cls, v, values):
        """Calcular desconto automaticamente"""
        original = values.get('original_price')
        current = values.get('price')
        
        # Sempre calcular o desconto baseado nos preços, ignorando v
        if original and current and original > current:
            return round(((original - current) / original) * 100, 2)
        
        return 0.0
    
    @validator('url')
    def validate_url(cls, v):
        """Validar URL do produto"""
        if v and not v.startswith(('http://', 'https://')):
            v = f"https://www.mercadolivre.com.br{v}"
        return v

class DataProcessor:
    """Processador de dados extraídos"""
    
    @staticmethod
    def clean_price(price_text: str) -> Optional[float]:
        """Limpar e converter texto de preço para float - Formato brasileiro"""
        if not price_text:
            return None
        
        original_text = str(price_text).strip()
        # Debug desabilitado para saída mais limpa
        # print(f"🔍 DEBUG PREÇO: '{original_text}' →", end=" ")
        
        # Remover caracteres não numéricos exceto vírgulas e pontos
        clean_text = re.sub(r'[^\d,.]', '', original_text)
        
        if not clean_text:
            return None
        
        try:
            # FORMATO BRASILEIRO ESPECÍFICO
            if ',' in clean_text and '.' in clean_text:
                # Caso: 1.299,99 (formato brasileiro completo)
                if clean_text.rfind(',') > clean_text.rfind('.'):
                    # Brasileiro: 1.299,99 → 1299.99
                    result = clean_text.replace('.', '').replace(',', '.')
                    return float(result)
                else:
                    # Americano: 1,299.99 → 1299.99
                    result = clean_text.replace(',', '')
                    return float(result)
                    
            elif ',' in clean_text:
                # Só vírgula: pode ser 1299,99 ou número pequeno como 1,99
                if len(clean_text.split(',')[0]) >= 3:
                    # Assumir brasileiro: 1299,99
                    result = clean_text.replace(',', '.')
                    return float(result)
                else:
                    # Número pequeno: 1,99
                    result = clean_text.replace(',', '.')
                    return float(result)
                    
            elif '.' in clean_text:
                # CASO CRÍTICO: Só ponto - pode ser separador de milhares ou decimal
                parts = clean_text.split('.')
                
                if len(parts) == 2:
                    # Um só ponto
                    if len(parts[1]) <= 2 and int(parts[0]) < 100:
                        # Provavelmente decimal: 99.90
                        return float(clean_text)
                    else:
                        # Provavelmente milhares: 1.049 = 1049
                        result = clean_text.replace('.', '')
                        return float(result)
                else:
                    # Múltiplos pontos: 1.234.567
                    result = clean_text.replace('.', '')
                    return float(result)
            else:
                # Só números: 488
                return float(clean_text)
                
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def extract_product_id(url: str) -> Optional[str]:
        """Extrair ID do produto da URL"""
        if not url:
            return None
        
        # Padrões comuns de ID do ML
        patterns = [
            r'ML[AB]\d+',  # MLB123456789 ou MLA123456789
            r'/p/ML[AB]\d+',
            r'item[_-]?id[=:](\d+)',
            r'/(\d{10,})'  # IDs numéricos longos
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1) if pattern.startswith('/') else match.group(0)
        
        return None
    
    @staticmethod
    def extract_rating(rating_text: str) -> Optional[float]:
        """Extrair nota de avaliação"""
        if not rating_text:
            return None
        
        # Procurar números com ponto ou vírgula
        match = re.search(r'(\d+[,.]\d+)', rating_text)
        if match:
            try:
                return float(match.group(1).replace(',', '.'))
            except ValueError:
                pass
        
        # Procurar número inteiro
        match = re.search(r'(\d+)', rating_text)
        if match:
            try:
                rating = int(match.group(1))
                return float(rating) if rating <= 5 else None
            except ValueError:
                pass
        
        return None
    
    @staticmethod
    def extract_reviews_count(reviews_text: str) -> Optional[int]:
        """Extrair número de avaliações"""
        if not reviews_text:
            return None
        
        # Remover caracteres não numéricos
        numbers = re.sub(r'[^\d]', '', reviews_text)
        
        try:
            return int(numbers) if numbers else None
        except ValueError:
            return None
    
    @staticmethod
    def is_promotion_indicator(text: str) -> bool:
        """Verificar se o texto indica uma promoção"""
        if not text:
            return False
        
        promotion_keywords = [
            'desconto', 'promoção', 'oferta', 'liquidação',
            'sale', 'off', '%', 'economize', 'imperdível',
            'black friday', 'cyber monday', 'queima'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in promotion_keywords)
    
    @staticmethod
    def has_free_shipping(text: str) -> bool:
        """Verificar se tem frete grátis"""
        if not text:
            return False
        
        shipping_keywords = [
            'frete grátis', 'frete gratuito', 'grátis',
            'free shipping', 'sem custo de envio'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in shipping_keywords)