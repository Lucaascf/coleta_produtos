#!/usr/bin/env python3
"""
Debug - Verificar por que desconto não aparece na tabela
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.utils.validators import Product
from datetime import datetime

def test_discount_calculation():
    """Testar cálculo de desconto"""
    
    print("🧪 TESTANDO CÁLCULO DE DESCONTO")
    print("="*50)
    
    # Teste 1: Produto com desconto (Air fryer)
    print("\n📦 Teste 1: Air Fryer")
    product1 = Product(
        name="Fritadeira Air Fryer Mondial",
        price=488.00,
        original_price=899.00,
        url="https://exemplo.com"
    )
    
    print(f"   Preço atual: R$ {product1.price:.2f}")
    print(f"   Preço original: R$ {product1.original_price:.2f}")
    print(f"   Desconto calculado: {product1.discount_percentage:.2f}%")
    print(f"   Em promoção: {product1.is_promotion}")
    
    # Teste 2: Produto sem desconto
    print("\n📦 Teste 2: Produto sem desconto")
    product2 = Product(
        name="Produto Normal",
        price=100.00,
        url="https://exemplo.com"
    )
    
    print(f"   Preço atual: R$ {product2.price:.2f}")
    print(f"   Preço original: {product2.original_price}")
    print(f"   Desconto calculado: {product2.discount_percentage:.2f}%")
    print(f"   Em promoção: {product2.is_promotion}")
    
    # Teste 3: Simular como aparece na tabela
    print("\n📊 COMO APARECERIA NA TABELA:")
    print("-" * 50)
    
    for i, product in enumerate([product1, product2], 1):
        discount_str = f"{product.discount_percentage:.0f}%" if product.discount_percentage > 0 else "-"
        print(f"{i}. {product.name[:30]:<30} | Desconto: {discount_str:>8}")
    
    print(f"\n✅ Teste concluído!")

if __name__ == "__main__":
    test_discount_calculation()