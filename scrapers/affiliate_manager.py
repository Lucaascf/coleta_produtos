"""
Sistema de Gerenciamento de Links de Afiliado - Mercado Pago
Integrado com PlaywrightEngine para automação do gerador de links
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich import box

from .engines.playwright_engine import PlaywrightEngine
from .utils.validators import Product
from .config import ScraperConfig

console = Console()

class AffiliateManager:
    """Gerenciador de links de afiliado do Mercado Pago"""
    
    def __init__(self):
        self.engine: Optional[PlaywrightEngine] = None
        self.config = ScraperConfig()
        self.affiliate_links: Dict[str, str] = {}
        
    async def __aenter__(self):
        """Context manager entry"""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
    
    async def start(self) -> None:
        """Inicializar engine em modo afiliado"""
        try:
            self.engine = PlaywrightEngine(affiliate_mode=True)
            await self.engine.start()
            console.print("✅ AffiliateManager iniciado com sucesso")
        except Exception as e:
            console.print(f"❌ Erro ao inicializar AffiliateManager: {e}")
            raise
    
    async def close(self) -> None:
        """Fechar recursos"""
        if self.engine:
            await self.engine.close()
            console.print("🔧 AffiliateManager fechado")
    
    async def login_and_setup(self, email: str = None, password: str = None) -> bool:
        """Login no Mercado Livre e configurar para geração de links"""
        try:
            console.print("🔑 Iniciando processo de login...")
            
            # Fazer login
            login_success = await self.engine.login_mercado_livre(email, password)
            
            if not login_success:
                console.print("❌ Falha no login")
                return False
            
            console.print("✅ Login realizado com sucesso")
            return True
            
        except Exception as e:
            console.print(f"❌ Erro durante setup: {e}")
            return False
    
    def load_products_from_file(self, filepath: str) -> List[Product]:
        """Carregar produtos de arquivo JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            products = []
            
            # Detectar formato do arquivo
            if 'produtos' in data and isinstance(data['produtos'], list):
                # Formato do sistema atual
                for product_data in data['produtos']:
                    try:
                        product = Product(
                            name=product_data.get('nome', ''),
                            price=product_data.get('preco', 0),
                            original_price=product_data.get('preco_original'),
                            url=product_data.get('url_completa', ''),
                            image_url=product_data.get('imagem_url'),
                            is_promotion=product_data.get('em_promocao', False),
                            free_shipping=product_data.get('frete_gratis', False),
                            product_id=product_data.get('produto_id'),
                            category=product_data.get('categoria'),
                            category_confidence=product_data.get('categoria_confianca', 0.0)
                        )
                        products.append(product)
                    except Exception as e:
                        console.print(f"⚠️ Erro ao processar produto: {e}")
                        continue
            
            console.print(f"✅ Carregados {len(products)} produtos de {filepath}")
            return products
            
        except FileNotFoundError:
            console.print(f"❌ Arquivo não encontrado: {filepath}")
            return []
        except json.JSONDecodeError:
            console.print(f"❌ Erro ao decodificar JSON: {filepath}")
            return []
        except Exception as e:
            console.print(f"❌ Erro ao carregar produtos: {e}")
            return []
    
    def list_available_product_files(self) -> List[str]:
        """Listar arquivos de produtos disponíveis"""
        data_dir = Path("data")
        if not data_dir.exists():
            return []
        
        product_files = []
        for file in data_dir.glob("produtos_*.json"):
            product_files.append(str(file))
        
        # Ordenar por data de modificação (mais recente primeiro)
        product_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return product_files
    
    async def generate_affiliate_links(self, products: List[Product]) -> Dict[str, Any]:
        """Gerar links de afiliado para lista de produtos"""
        if not products:
            console.print("❌ Nenhum produto fornecido")
            return {}
        
        console.print(f"🔗 Iniciando geração de {len(products)} links de afiliado em lote...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Gerando links...", total=len(products))
            
            def progress_callback(current, total, description):
                progress.update(task, completed=current, description=description)
            
            # Gerar links em lote único
            results = await self.engine.generate_affiliate_links_batch(
                products, 
                progress_callback
            )
        
        # Salvar resultados
        await self.save_affiliate_results(results)
        
        return results
    
    async def save_affiliate_results(self, results: Dict[str, Any]) -> str:
        """Salvar resultados dos links de afiliado"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Criar diretório se não existir
        os.makedirs("data", exist_ok=True)
        
        # Arquivo principal com dados completos
        json_filename = f"data/links_afiliado_{timestamp}.json"
        
        # Preparar dados para salvar
        results_data = {
            "info": {
                "total_produtos": len(results.get('product_mapping', [])),
                "links_gerados": results.get('success_count', 0),
                "links_falharam": results.get('error_count', 0),
                "taxa_sucesso": f"{(results.get('success_count', 0)/len(results.get('product_mapping', []))*100):.1f}%" if results.get('product_mapping') else "0%",
                "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "sistema": "AffiliateManager v2.0 - Lote Único",
                "processado_em": results.get('processed_at')
            },
            "produtos_com_links": results.get('product_mapping', [])
        }
        
        # Salvar arquivo JSON principal
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        # Arquivo simples só com os links (um por linha)
        txt_filename = f"data/links_simples_{timestamp}.txt"
        
        affiliate_links = []
        for product_mapping in results.get('product_mapping', []):
            if product_mapping.get('url_afiliado'):
                affiliate_links.append(product_mapping['url_afiliado'])
        
        if affiliate_links:
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(affiliate_links))
            
            console.print(f"💾 Links simples salvos em: {txt_filename}")
        
        console.print(f"💾 Dados completos salvos em: {json_filename}")
        console.print(f"📊 {results.get('success_count', 0)} links gerados de {len(results.get('product_mapping', []))} produtos")
        
        return json_filename
    
    def display_affiliate_results(self, results: Dict[str, Any]) -> None:
        """Exibir resultados dos links de afiliado"""
        # Estatísticas gerais
        stats_table = Table(show_header=False, box=box.SIMPLE)
        stats_table.add_column("Métrica", style="bold cyan")
        stats_table.add_column("Valor", style="white")
        
        total_products = len(results.get('product_mapping', []))
        success_count = results.get('success_count', 0)
        error_count = results.get('error_count', 0)
        
        stats_table.add_row("🔗 Total de produtos:", str(total_products))
        stats_table.add_row("✅ Links gerados:", str(success_count))
        stats_table.add_row("❌ Falhas:", str(error_count))
        
        if total_products > 0:
            success_rate = (success_count / total_products) * 100
            stats_table.add_row("📊 Taxa de sucesso:", f"{success_rate:.1f}%")
        
        stats_panel = Panel(
            stats_table,
            title="[bold]📈 Estatísticas dos Links de Afiliado[/bold]",
            border_style="green"
        )
        
        console.print(stats_panel)
        
        # Tabela de produtos com links
        product_mappings = results.get('product_mapping', [])
        if product_mappings:
            console.print("\n[bold cyan]🔗 Produtos com Links de Afiliado Gerados:[/bold cyan]")
            
            links_table = Table(box=box.ROUNDED)
            links_table.add_column("#", style="bold yellow", width=3)
            links_table.add_column("Produto", style="cyan", max_width=40)
            links_table.add_column("Preço", style="green", justify="right")
            links_table.add_column("Status", style="green", justify="center")
            
            for product_mapping in product_mappings[:10]:  # Mostrar primeiros 10
                name = product_mapping['nome']
                if len(name) > 37:
                    name = name[:37] + "..."
                
                price = f"R$ {product_mapping.get('preco', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                status = "✅ Link gerado" if product_mapping.get('url_afiliado') else "❌ Falhou"
                
                links_table.add_row(
                    str(product_mapping.get('ordem', '')),
                    name,
                    price,
                    status
                )
            
            console.print(links_table)
            
            if len(product_mappings) > 10:
                console.print(f"\n[dim]... e mais {len(product_mappings) - 10} produtos processados[/dim]")
        
        # Produtos que falharam
        failed_products = [p for p in product_mappings if not p.get('url_afiliado')]
        if failed_products:
            console.print(f"\n[bold red]❌ {len(failed_products)} produtos falharam:[/bold red]")
            for i, product in enumerate(failed_products[:5], 1):  # Mostrar apenas os primeiros 5
                name = product['nome'][:50] + "..." if len(product['nome']) > 50 else product['nome']
                console.print(f"  {i}. {name}")
            
            if len(failed_products) > 5:
                console.print(f"  ... e mais {len(failed_products) - 5} produtos")
    
    async def process_product_file(self, filepath: str) -> Dict[str, Any]:
        """Processar arquivo de produtos completo"""
        try:
            # Carregar produtos
            products = self.load_products_from_file(filepath)
            
            if not products:
                return {"error": "Nenhum produto carregado do arquivo"}
            
            # Configurar sistema de afiliados
            setup_success = await self.login_and_setup()
            if not setup_success:
                return {"error": "Falha na configuração do sistema de afiliados"}
            
            # Gerar links
            results = await self.generate_affiliate_links(products)
            
            # Exibir resultados
            self.display_affiliate_results(results)
            
            return results
            
        except Exception as e:
            console.print(f"❌ Erro ao processar arquivo: {e}")
            return {"error": str(e)}