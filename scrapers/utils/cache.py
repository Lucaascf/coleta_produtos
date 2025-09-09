"""
Sistema de cache com SQLite para otimizar performance
"""

import sqlite3
import json
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import aiosqlite
from pathlib import Path

from .validators import Product

class ScraperCache:
    """Cache inteligente para scraping com SQLite"""
    
    def __init__(self, db_path: str = "cache/scraper_cache.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ttl_hours = 2  # Cache válido por 2 horas
        
    async def __aenter__(self):
        """Context manager entry"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        pass
    
    async def initialize(self) -> None:
        """Inicializar tabelas do cache"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE,
                    query_type TEXT,
                    query_params TEXT,
                    products_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS product_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT,
                    name TEXT,
                    price REAL,
                    original_price REAL,
                    url TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS selector_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    selector TEXT,
                    selector_type TEXT,
                    success_count INTEGER DEFAULT 0,
                    total_attempts INTEGER DEFAULT 0,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.commit()
            print("✅ Cache SQLite inicializado")
    
    def _generate_cache_key(self, query_type: str, params: Dict[str, Any]) -> str:
        """Gerar chave única para cache"""
        cache_data = f"{query_type}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    async def get_cached_search(self, query_type: str, params: Dict[str, Any]) -> Optional[List[Product]]:
        """Recuperar busca do cache"""
        cache_key = self._generate_cache_key(query_type, params)
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT products_json, expires_at FROM search_cache 
                    WHERE cache_key = ? AND expires_at > datetime('now')
                """, (cache_key,)) as cursor:
                    
                    row = await cursor.fetchone()
                    if row:
                        products_json, expires_at = row
                        products_data = json.loads(products_json)
                        
                        # Converter de volta para objetos Product
                        products = [Product(**data) for data in products_data]
                        
                        print(f"💾 Cache hit: {len(products)} produtos recuperados")
                        return products
            
        except Exception as e:
            print(f"⚠️ Erro ao ler cache: {e}")
        
        return None
    
    async def cache_search_results(self, query_type: str, params: Dict[str, Any], products: List[Product]) -> None:
        """Salvar resultados no cache"""
        cache_key = self._generate_cache_key(query_type, params)
        expires_at = datetime.now() + timedelta(hours=self.ttl_hours)
        
        try:
            # Converter produtos para JSON
            products_data = [product.dict() for product in products]
            products_json = json.dumps(products_data, default=str)
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO search_cache 
                    (cache_key, query_type, query_params, products_json, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    cache_key, 
                    query_type, 
                    json.dumps(params), 
                    products_json, 
                    expires_at
                ))
                
                await db.commit()
                print(f"💾 Cache salvo: {len(products)} produtos")
                
        except Exception as e:
            print(f"⚠️ Erro ao salvar cache: {e}")
    
    async def save_product_history(self, products: List[Product]) -> None:
        """Salvar histórico de produtos para análise de preços"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                for product in products:
                    await db.execute("""
                        INSERT INTO product_history 
                        (product_id, name, price, original_price, url)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        product.product_id,
                        product.name,
                        product.price,
                        product.original_price,
                        product.url
                    ))
                
                await db.commit()
                print(f"📊 Histórico salvo: {len(products)} produtos")
                
        except Exception as e:
            print(f"⚠️ Erro ao salvar histórico: {e}")
    
    async def get_price_history(self, product_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Recuperar histórico de preços de um produto"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT name, price, original_price, scraped_at 
                    FROM product_history 
                    WHERE product_id = ? AND scraped_at > datetime('now', '-{} days')
                    ORDER BY scraped_at DESC
                """.format(days), (product_id,)) as cursor:
                    
                    rows = await cursor.fetchall()
                    
                    history = []
                    for row in rows:
                        name, price, original_price, scraped_at = row
                        history.append({
                            'name': name,
                            'price': price,
                            'original_price': original_price,
                            'scraped_at': scraped_at
                        })
                    
                    return history
                    
        except Exception as e:
            print(f"⚠️ Erro ao recuperar histórico: {e}")
            return []
    
    async def update_selector_performance(self, selector: str, selector_type: str, success: bool) -> None:
        """Atualizar performance de um seletor"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Verificar se seletor já existe
                async with db.execute("""
                    SELECT success_count, total_attempts FROM selector_performance 
                    WHERE selector = ? AND selector_type = ?
                """, (selector, selector_type)) as cursor:
                    
                    row = await cursor.fetchone()
                    
                    if row:
                        success_count, total_attempts = row
                        new_success = success_count + (1 if success else 0)
                        new_total = total_attempts + 1
                        
                        await db.execute("""
                            UPDATE selector_performance 
                            SET success_count = ?, total_attempts = ?, last_used = datetime('now')
                            WHERE selector = ? AND selector_type = ?
                        """, (new_success, new_total, selector, selector_type))
                    else:
                        await db.execute("""
                            INSERT INTO selector_performance 
                            (selector, selector_type, success_count, total_attempts)
                            VALUES (?, ?, ?, 1)
                        """, (selector, selector_type, 1 if success else 0))
                
                await db.commit()
                
        except Exception as e:
            print(f"⚠️ Erro ao atualizar performance: {e}")
    
    async def get_best_selectors(self, selector_type: str, min_attempts: int = 5) -> List[Dict[str, Any]]:
        """Recuperar os melhores seletores por tipo"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT selector, success_count, total_attempts,
                           CAST(success_count AS FLOAT) / total_attempts as success_rate
                    FROM selector_performance 
                    WHERE selector_type = ? AND total_attempts >= ?
                    ORDER BY success_rate DESC, total_attempts DESC
                    LIMIT 10
                """, (selector_type, min_attempts)) as cursor:
                    
                    rows = await cursor.fetchall()
                    
                    selectors = []
                    for row in rows:
                        selector, success_count, total_attempts, success_rate = row
                        selectors.append({
                            'selector': selector,
                            'success_count': success_count,
                            'total_attempts': total_attempts,
                            'success_rate': success_rate
                        })
                    
                    return selectors
                    
        except Exception as e:
            print(f"⚠️ Erro ao recuperar seletores: {e}")
            return []
    
    async def cleanup_old_cache(self, days_old: int = 7) -> None:
        """Limpar cache antigo"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Remover cache expirado
                await db.execute("""
                    DELETE FROM search_cache 
                    WHERE expires_at < datetime('now')
                """)
                
                # Remover histórico muito antigo
                await db.execute("""
                    DELETE FROM product_history 
                    WHERE scraped_at < datetime('now', '-{} days')
                """.format(days_old))
                
                await db.commit()
                print("🧹 Cache antigo limpo")
                
        except Exception as e:
            print(f"⚠️ Erro ao limpar cache: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do cache"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                stats = {}
                
                # Estatísticas de cache
                async with db.execute("SELECT COUNT(*) FROM search_cache") as cursor:
                    row = await cursor.fetchone()
                    stats['total_cached_searches'] = row[0] if row else 0
                
                async with db.execute("""
                    SELECT COUNT(*) FROM search_cache 
                    WHERE expires_at > datetime('now')
                """) as cursor:
                    row = await cursor.fetchone()
                    stats['valid_cached_searches'] = row[0] if row else 0
                
                # Estatísticas de histórico
                async with db.execute("SELECT COUNT(*) FROM product_history") as cursor:
                    row = await cursor.fetchone()
                    stats['total_products_tracked'] = row[0] if row else 0
                
                async with db.execute("""
                    SELECT COUNT(DISTINCT product_id) FROM product_history
                """) as cursor:
                    row = await cursor.fetchone()
                    stats['unique_products'] = row[0] if row else 0
                
                return stats
                
        except Exception as e:
            print(f"⚠️ Erro ao obter estatísticas: {e}")
            return {}