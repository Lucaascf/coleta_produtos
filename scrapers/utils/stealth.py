"""
Utilitários para evitar detecção de bot
"""

import asyncio
import random
from typing import Any
from playwright.async_api import Page, Browser

class StealthMode:
    """Classe para implementar funcionalidades stealth"""
    
    @staticmethod
    async def setup_stealth(page: Page) -> None:
        """Configura a página para modo stealth"""
        
        # Remover indicadores de webdriver
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mascarar Chrome automation
            window.chrome = {
                runtime: {},
            };
            
            // Simular plugins reais
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Simular idiomas
            Object.defineProperty(navigator, 'languages', {
                get: () => ['pt-BR', 'pt', 'en'],
            });
            
            // Mascarar permissões
            const originalQuery = window.navigator.permissions.query;
            return window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        # Configurar viewport realista
        await page.set_viewport_size({
            "width": random.randint(1200, 1920), 
            "height": random.randint(800, 1080)
        })
        
        # Headers extras
        await page.set_extra_http_headers({
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
        })
    
    @staticmethod
    async def human_like_delay(min_seconds: float = 0.5, max_seconds: float = 2.0) -> None:
        """Delay que simula comportamento humano"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    @staticmethod
    async def random_mouse_movement(page: Page) -> None:
        """Simula movimento aleatório do mouse"""
        try:
            viewport = await page.viewport_size()
            if viewport:
                x = random.randint(100, viewport['width'] - 100)
                y = random.randint(100, viewport['height'] - 100)
                await page.mouse.move(x, y)
                await StealthMode.human_like_delay(0.1, 0.3)
        except:
            pass
    
    @staticmethod
    async def human_scroll(page: Page) -> None:
        """Simula scroll humano na página"""
        try:
            # Scroll em partes pequenas
            for _ in range(random.randint(2, 5)):
                scroll_distance = random.randint(200, 800)
                await page.mouse.wheel(0, scroll_distance)
                await StealthMode.human_like_delay(0.3, 0.8)
            
            # Pequena pausa
            await StealthMode.human_like_delay(1.0, 2.0)
            
            # Scroll de volta um pouco
            await page.mouse.wheel(0, -random.randint(100, 400))
            await StealthMode.human_like_delay(0.5, 1.0)
            
        except Exception as e:
            pass
    
    @staticmethod
    async def wait_for_page_load(page: Page, timeout: int = 30000) -> bool:
        """Aguarda o carregamento completo da página"""
        try:
            # Aguardar network idle
            await page.wait_for_load_state('networkidle', timeout=timeout)
            
            # Aguardar JavaScript terminar
            await page.wait_for_function(
                "document.readyState === 'complete'",
                timeout=timeout
            )
            
            # Pequeno delay extra para garantir
            await StealthMode.human_like_delay(1.0, 2.0)
            
            return True
            
        except Exception as e:
            print(f"⚠️ Timeout aguardando carregamento: {e}")
            return False
    
    @staticmethod
    async def bypass_cloudflare(page: Page) -> bool:
        """Tenta contornar proteção do Cloudflare"""
        try:
            # Verificar se há challenge do Cloudflare
            cf_selectors = [
                '[id*="cloudflare"]',
                '[class*="cf-"]', 
                'div[data-ray]',
                '#challenge-running',
                '.challenge-loading'
            ]
            
            for selector in cf_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        print("🔄 Cloudflare detectado, aguardando...")
                        # Aguardar até 30 segundos para o challenge passar
                        await page.wait_for_selector(selector, state='detached', timeout=30000)
                        await StealthMode.human_like_delay(2.0, 4.0)
                        return True
                except:
                    continue
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao contornar Cloudflare: {e}")
            return False