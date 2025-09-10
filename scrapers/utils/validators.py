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
    category: Optional[str] = None
    category_confidence: float = 0.0
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

class ProductClassifier:
    """Classificador automático de produtos por categoria"""
    
    # Mapeamento de palavras-chave para categorias (baseado em categorias reais do ML)
    CATEGORY_KEYWORDS = {
        'Eletrônicos, Áudio e Vídeo': {
            'keywords': [
                'tv', 'televisão', 'televisor', 'smart tv', 'led', 'lcd', 'oled', 'qled',
                'eletrônico', 'eletronico', 'som', 'audio', 'áudio', 'fone', 'headset',
                'speaker', 'caixa de som', 'amplificador', 'receiver', 'home theater',
                'câmera', 'camera', 'fotografia', 'filmadora', 'drone', 'gopro',
                'soundbar', 'subwoofer', 'toca-discos', 'vinil', 'cd player',
                'microfone', 'mixer', 'estúdio', 'gravação'
            ],
            'weight': 1.0
        },
        'Celulares e Telefones': {
            'keywords': [
                'smartphone', 'celular', 'iphone', 'samsung galaxy', 'xiaomi', 'motorola',
                'lg', 'huawei', 'oneplus', 'pixel', 'telefone', 'mobile', 'android', 'ios',
                'capinha', 'película', 'carregador', 'cabo usb', 'power bank', 'bateria',
                'fone bluetooth', 'airpods', 'earbuds', 'smartwatch', 'apple watch',
                'celular desbloqueado', 'dual chip', '5g', '4g', 'smartphone android'
            ],
            'weight': 1.0
        },
        'Informática': {
            'keywords': [
                'notebook', 'laptop', 'computador', 'pc', 'desktop', 'all in one',
                'processador', 'cpu', 'intel', 'amd', 'ryzen', 'core i3', 'core i5', 'core i7',
                'placa de vídeo', 'gpu', 'nvidia', 'radeon', 'geforce', 'gtx', 'rtx',
                'memória ram', 'ddr4', 'ddr5', 'ssd', 'hd', 'disco rígido', 'storage',
                'placa mãe', 'motherboard', 'fonte', 'gabinete', 'cooler', 'monitor',
                'teclado', 'mouse', 'mousepad', 'webcam', 'microfone', 'impressora',
                'scanner', 'roteador', 'modem', 'wi-fi', 'cabo de rede', 'switch',
                'pendrive', 'hd externo', 'backup', 'software', 'windows', 'office',
                'ultrabook', 'chromebook', 'macbook'
            ],
            'weight': 1.0
        },
        'Casa, Móveis e Decoração': {
            'keywords': [
                'móvel', 'movel', 'sofá', 'sofa', 'poltrona', 'cadeira', 'mesa', 'cama',
                'guarda-roupa', 'armário', 'armario', 'estante', 'rack', 'aparador',
                'colchão', 'colchao', 'travesseiro', 'lençol', 'lencol', 'edredom',
                'cortina', 'persiana', 'tapete', 'carpete', 'luminária', 'luminaria',
                'abajur', 'lustre', 'pendente', 'espelho', 'quadro', 'decoração', 'decoracao',
                'vaso', 'planta', 'jardim', 'cozinha', 'banheiro', 'quarto', 'sala',
                'panela', 'frigideira', 'utensílio', 'utensilio', 'talheres', 'pratos',
                'xícara', 'xicara', 'copo', 'garrafa', 'organizador', 'gaveta',
                'criado-mudo', 'cômoda', 'penteadeira', 'painel tv'
            ],
            'weight': 1.0
        },
        'Eletrodomésticos e Casa': {
            'keywords': [
                'ar condicionado', 'ventilador', 'aquecedor', 'micro-ondas', 'microondas',
                'geladeira', 'refrigerador', 'freezer', 'lava-louça', 'lavadora',
                'fogão', 'cooktop', 'forno elétrico', 'aspirador', 'liquidificador',
                'batedeira', 'processador', 'cafeteira', 'sanduicheira', 'grill',
                'ferro de passar', 'secadora', 'lava e seca'
            ],
            'weight': 1.0
        },
        'Roupas e Calçados': {
            'keywords': [
                'roupa', 'vestuário', 'vestuario', 'camiseta', 'camisa', 'blusa', 'top',
                'vestido', 'saia', 'short', 'bermuda', 'calça', 'calca', 'jeans',
                'legging', 'moletom', 'casaco', 'jaqueta', 'blazer', 'colete',
                'sapato', 'tênis', 'tenis', 'sandália', 'sandalia', 'chinelo', 'bota',
                'sapatênis', 'sapatenis', 'scarpin', 'salto', 'rasteirinha',
                'bolsa', 'mochila', 'carteira', 'necessaire', 'mala', 'pochete',
                'masculino', 'feminino', 'infantil', 'bebê', 'bebe',
                'polo', 'regata', 'cropped', 'midi', 'maxi'
            ],
            'weight': 1.0
        },
        'Esportes e Fitness': {
            'keywords': [
                'esporte', 'fitness', 'academia', 'ginástica', 'ginastica', 'musculação', 'musculacao',
                'futebol', 'bola', 'chuteira', 'camisa de time', 'basquete', 'vôlei', 'volei',
                'tênis esportivo', 'corrida', 'maratona', 'caminhada', 'running',
                'bicicleta', 'bike', 'ciclismo', 'capacete', 'natação', 'natacao', 'piscina',
                'halteres', 'peso', 'anilha', 'barra', 'esteira', 'elíptico', 'eliptico',
                'yoga', 'pilates', 'colchonete', 'faixa elástica', 'suplemento', 'whey',
                'creatina', 'bcaa', 'surf', 'prancha', 'skate', 'patins', 'patinete',
                'crossfit', 'treino funcional', 'kettlebell'
            ],
            'weight': 1.0
        },
        'Livros, Revistas e Comics': {
            'keywords': [
                'livro', 'ebook', 'literatura', 'romance', 'ficção', 'ficcao', 'biografia',
                'autoajuda', 'auto-ajuda', 'negócios', 'negocios', 'economia', 'política', 'politica',
                'história', 'historia', 'geografia', 'ciência', 'ciencia', 'matemática', 'matematica',
                'física', 'fisica', 'química', 'quimica', 'biologia', 'medicina',
                'psicologia', 'filosofia', 'sociologia', 'educação', 'educacao',
                'infantil', 'juvenil', 'didático', 'didatico', 'apostila', 'curso',
                'revista', 'gibi', 'mangá', 'manga', 'hq', 'quadrinhos', 'comic'
            ],
            'weight': 1.0
        },
        'Saúde e Beleza': {
            'keywords': [
                'maquiagem', 'cosméticos', 'cosmeticos', 'batom', 'base', 'corretivo',
                'rímel', 'rimel', 'sombra', 'blush', 'pó', 'po', 'primer', 'gloss',
                'perfume', 'colônia', 'colonia', 'desodorante', 'antitranspirante',
                'shampoo', 'condicionador', 'máscara capilar', 'mascara capilar',
                'creme', 'hidratante', 'protetor solar', 'sabonete', 'esfoliante',
                'sérum', 'serum', 'tônico', 'tonico', 'demaquilante', 'água micelar', 'agua micelar',
                'escova', 'pente', 'secador', 'chapinha', 'babyliss', 'depilador',
                'nail art', 'esmalte', 'acetona', 'lixa', 'alicate',
                'vitamina', 'suplemento', 'medicamento'
            ],
            'weight': 1.0
        },
        'Games': {
            'keywords': [
                'video game', 'videogame', 'console', 'playstation', 'ps5', 'ps4', 'ps3',
                'xbox', 'nintendo', 'switch', 'controle', 'joystick', 'gamepad',
                'jogo', 'game', 'cd', 'dvd', 'blu-ray', 'digital', 'steam', 'epic',
                'pc gamer', 'gaming', 'headset gamer', 'teclado gamer', 'mouse gamer',
                'cadeira gamer', 'mesa gamer', 'monitor gamer', 'placa de captura',
                'streamer', 'twitch', 'youtube', 'fps', 'rpg', 'mmorpg', 'battle royale',
                'minecraft', 'fortnite', 'gta', 'fifa', 'pes', 'call of duty'
            ],
            'weight': 1.0
        },
        'Carros, Motos e Outros': {
            'keywords': [
                'carro', 'automóvel', 'automovel', 'veículo', 'veiculo', 'auto', 'motor',
                'pneu', 'roda', 'aro', 'calota', 'freio', 'pastilha', 'disco', 'amortecedor',
                'óleo', 'oleo', 'filtro', 'bateria', 'alternador', 'radiador', 'vela',
                'correia', 'escapamento', 'para-choque', 'para-brisa', 'farol', 'lanterna',
                'retrovisor', 'banco', 'volante', 'câmbio', 'cambio', 'embreagem',
                'som automotivo', 'alarme', 'trava', 'película', 'cera', 'enceradeira',
                'aspirador automotivo', 'suporte', 'carregador veicular', 'gps', 'dvr',
                'moto', 'motocicleta', 'capacete moto'
            ],
            'weight': 1.0
        },
        'Relógios e Joias': {
            'keywords': [
                'relógio', 'relogio', 'smartwatch', 'apple watch', 'citizen', 'casio',
                'óculos', 'oculos', 'colar', 'pulseira', 'anel', 'brinco',
                'joia', 'jóia', 'ouro', 'prata', 'folheado', 'semi-joia'
            ],
            'weight': 1.0
        }
    }
    
    # Categorias reverso (para lookup por ID do ML)
    ML_CATEGORY_IDS = {
        'MLB1000': 'Eletrônicos, Áudio e Vídeo',
        'MLB1055': 'Celulares e Telefones', 
        'MLB1648': 'Informática',
        'MLB1574': 'Casa, Móveis e Decoração',
        'MLB1556': 'Eletrodomésticos e Casa',
        'MLB1430': 'Roupas e Calçados',
        'MLB1276': 'Esportes e Fitness',
        'MLB3025': 'Livros, Revistas e Comics',
        'MLB263532': 'Saúde e Beleza',
        'MLB1144': 'Games',
        'MLB1743': 'Carros, Motos e Outros',
        'MLB1137': 'Relógios e Joias'
    }
    
    @classmethod
    def classify_by_url(cls, url: str) -> tuple[Optional[str], float]:
        """Classificar produto baseado na URL do Mercado Livre"""
        if not url:
            return None, 0.0
        
        # Procurar por ID de categoria na URL
        import re
        
        # Padrão: /c/MLB1000 ou similar
        category_pattern = r'/c/(MLB\d+)'
        match = re.search(category_pattern, url)
        
        if match:
            category_id = match.group(1)
            category = cls.ML_CATEGORY_IDS.get(category_id)
            if category:
                return category, 1.0  # Alta confiança quando vem da URL
        
        return None, 0.0
    
    @classmethod
    def classify_by_keywords(cls, product_name: str, product_description: str = "") -> tuple[Optional[str], float]:
        """Classificar produto baseado em palavras-chave no nome e descrição"""
        if not product_name:
            return None, 0.0
        
        # Combinar nome e descrição para análise
        text_to_analyze = f"{product_name} {product_description}".lower()
        
        # Calcular score para cada categoria
        category_scores = {}
        
        for category, data in cls.CATEGORY_KEYWORDS.items():
            score = 0.0
            keyword_matches = 0
            
            for keyword in data['keywords']:
                if keyword.lower() in text_to_analyze:
                    score += data['weight']
                    keyword_matches += 1
            
            # Normalizar score pelo número de palavras-chave da categoria
            if keyword_matches > 0:
                category_scores[category] = (score, keyword_matches)
        
        # Encontrar categoria com maior score
        if not category_scores:
            return None, 0.0
        
        best_category = max(category_scores.items(), key=lambda x: (x[1][0], x[1][1]))
        category_name = best_category[0]
        score, matches = best_category[1]
        
        # Calcular confiança baseada no número de matches
        # Mais matches = maior confiança
        confidence = min(0.1 + (matches * 0.15), 0.95)  # Entre 0.1 e 0.95
        
        return category_name, confidence
    
    @classmethod
    def classify_product(cls, name: str, url: str = "", description: str = "") -> tuple[Optional[str], float]:
        """Classificar produto usando múltiplos métodos"""
        
        # Método 1: Por URL (maior confiança)
        category_url, confidence_url = cls.classify_by_url(url)
        if category_url and confidence_url > 0.8:
            return category_url, confidence_url
        
        # Método 2: Por palavras-chave
        category_keywords, confidence_keywords = cls.classify_by_keywords(name, description)
        
        # Escolher melhor resultado
        if category_url and category_keywords:
            # Se ambos concordam, usar maior confiança
            if category_url == category_keywords:
                return category_url, max(confidence_url, confidence_keywords)
            else:
                # Se discordam, usar o de maior confiança
                if confidence_url > confidence_keywords:
                    return category_url, confidence_url
                else:
                    return category_keywords, confidence_keywords
        
        # Retornar o que tiver
        if category_url:
            return category_url, confidence_url
        elif category_keywords:
            return category_keywords, confidence_keywords
        
        return None, 0.0