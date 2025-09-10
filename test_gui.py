#!/usr/bin/env python3
"""
Teste simples da GUI para verificar se está funcionando
"""

import sys
import os

# Adicionar path do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from gui_main import MercadoLivreScraper
    
    print("🧪 Testando interface gráfica...")
    print("✅ Imports OK")
    
    # Tentar criar a aplicação
    app = MercadoLivreScraper()
    print("✅ Aplicação criada com sucesso")
    
    # Não executar mainloop no teste
    print("✅ Interface gráfica pronta para uso!")
    print("📝 Para executar: python gui_main.py")
    
except ImportError as e:
    print(f"❌ Erro de import: {e}")
    print("💡 Instale as dependências: pip install tkinter (pode já vir com Python)")
    
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
    print("💡 Verifique se todas as dependências estão instaladas")