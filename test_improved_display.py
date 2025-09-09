#!/usr/bin/env python3
"""
Teste da Interface Melhorada - Ofertas e Promoções
"""

import asyncio
import sys
import os

# Adicionar path do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.engines.playwright_engine import PlaywrightEngine

async def test_improved_display():
    """Testar a interface melhorada"""
    
    print("🧪 TESTANDO INTERFACE MELHORADA - OFERTAS")
    print("="*50)
    
    # Testar com ofertas (onde há mais produtos com desconto)
    test_url = "https://www.mercadolivre.com.br/ofertas"
    
    async with PlaywrightEngine() as engine:
        print(f"🔍 Testando interface melhorada...")
        
        # Extrair apenas 5 produtos para teste rápido
        products = await engine.search_offers(5)
        
        if not products:
            print("❌ Nenhum produto extraído")
            return
        
        # Simular a função display_products do main.py
        from main import ModernScraperCLI
        app = ModernScraperCLI()
        
        print(f"\n📦 PRODUTOS EXTRAÍDOS: {len(products)}")
        print("="*60)
        
        # Mostrar produtos com nova interface
        await app.display_products(products, "🧪 TESTE - Ofertas e Promoções")
        
        print(f"\n✅ TESTE CONCLUÍDO!")
        print(f"Verifique se:")
        print(f"  - Descontos aparecem na coluna 'Desconto'")
        print(f"  - Preços originais aparecem riscados")
        print(f"  - Emojis destacam descontos altos (🔥 >50%, 🟡 >30%)")
        print(f"  - Estatísticas mostram economia total")

async def main():
    """Função principal"""
    try:
        await test_improved_display()
    except KeyboardInterrupt:
        print("\n🛑 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())