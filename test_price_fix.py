#!/usr/bin/env python3
"""
Teste Rápido - Verificar Correção de Preços De/Por
"""

import asyncio
import sys
import os

# Adicionar path do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.engines.playwright_engine import PlaywrightEngine

async def test_price_extraction():
    """Testar extração de preços com as correções"""
    
    print("🧪 TESTANDO CORREÇÃO DE PREÇOS DE/POR")
    print("="*50)
    
    # Testar com ofertas (onde há mais produtos com desconto)
    test_url = "https://www.mercadolivre.com.br/ofertas"
    
    async with PlaywrightEngine() as engine:
        print(f"🔍 Testando em: {test_url}")
        products = await engine.extract_products_from_page(test_url)
        
        if not products:
            print("❌ Nenhum produto extraído")
            return
        
        print(f"\n📦 PRODUTOS EXTRAÍDOS: {len(products)}")
        print("-" * 60)
        
        promotion_count = 0
        
        for i, product in enumerate(products[:10], 1):  # Mostrar primeiros 10
            print(f"\n{i}. {product.name[:50]}...")
            print(f"   💰 Preço atual: R$ {product.price:.2f}")
            
            if product.original_price:
                promotion_count += 1
                discount = ((product.original_price - product.price) / product.original_price) * 100
                print(f"   🔥 Preço original: R$ {product.original_price:.2f}")
                print(f"   📉 Desconto: {discount:.1f}% OFF")
                print(f"   ✅ CAPTURA DE PREÇO DE/POR: FUNCIONANDO!")
            else:
                print(f"   ⚪ Sem preço original (não está em promoção)")
            
            print(f"   🔗 URL: {product.url[:80]}..." if product.url else "   ❌ Sem URL")
        
        print(f"\n📊 RESUMO:")
        print(f"   Total de produtos: {len(products[:10])}")
        print(f"   Produtos em promoção: {promotion_count}")
        print(f"   Taxa de captura de preço original: {(promotion_count/len(products[:10]))*100:.1f}%")
        
        if promotion_count > 0:
            print(f"\n🎉 SUCESSO! O sistema está capturando preços de/por corretamente!")
        else:
            print(f"\n⚠️ Nenhum produto em promoção encontrado. Pode ser normal.")

async def main():
    """Função principal"""
    try:
        await test_price_extraction()
    except KeyboardInterrupt:
        print("\n🛑 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro no teste: {e}")

if __name__ == "__main__":
    asyncio.run(main())