#!/usr/bin/env python3
"""
Sistema Moderno de Web Scraping - Mercado Livre v2.0
Interface CLI com Rich e funcionalidades avançadas
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Optional

# Adicionar path do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Rich imports para UI moderna
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich import box
import click

# Imports do sistema
from scrapers.engines.playwright_engine import PlaywrightEngine
from scrapers.utils.cache import ScraperCache
from scrapers.utils.validators import Product
from scrapers.config import ScraperConfig

console = Console()

class ModernScraperCLI:
    """Interface CLI moderna para o scraper"""
    
    def __init__(self):
        self.engine: Optional[PlaywrightEngine] = None
        self.cache: Optional[ScraperCache] = None
        self.config = ScraperConfig()
        
    def show_banner(self):
        """Exibir banner do sistema"""
        banner_text = Text()
        banner_text.append("🛒 MERCADO LIVRE SCRAPER v2.0\n", style="bold blue")
        banner_text.append("Sistema Moderno de Web Scraping\n", style="cyan")
        banner_text.append("Playwright + Anti-Detecção + Cache Inteligente", style="dim")
        
        banner_panel = Panel(
            Align.center(banner_text),
            box=box.DOUBLE,
            border_style="blue",
            padding=(1, 2)
        )
        
        console.print(banner_panel)
        console.print()
    
    def show_menu(self) -> str:
        """Exibir menu principal"""
        menu_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        menu_table.add_column("Opção", style="bold cyan", width=4)
        menu_table.add_column("Descrição", style="white")
        menu_table.add_column("Status", style="green")
        
        menu_options = [
            ("1", "🔍 Buscar produtos por termo", "✅ Disponível"),
            ("2", "🏷️ Buscar por categoria/nicho", "✅ Disponível"), 
            ("3", "🔥 Coletar ofertas e promoções", "✅ Disponível"),
            ("4", "📊 Ver estatísticas do cache", "✅ Disponível"),
            ("5", "🧹 Limpar cache antigo", "✅ Disponível"),
            ("6", "⚙️ Configurações do sistema", "✅ Disponível"),
            ("0", "❌ Sair", "")
        ]
        
        for option, description, status in menu_options:
            menu_table.add_row(option, description, status)
        
        menu_panel = Panel(
            menu_table,
            title="[bold]Menu Principal[/bold]",
            border_style="cyan",
            padding=(1, 1)
        )
        
        console.print(menu_panel)
        
        return Prompt.ask(
            "\n[bold cyan]➡️ Escolha uma opção[/bold cyan]",
            choices=["0", "1", "2", "3", "4", "5", "6"],
            default="1"
        )
    
    def show_categories(self) -> str:
        """Exibir categorias disponíveis"""
        categories_table = Table(show_header=False, box=box.SIMPLE)
        categories_table.add_column("ID", style="bold yellow", width=3)
        categories_table.add_column("Categoria", style="cyan")
        categories_table.add_column("Código ML", style="dim")
        
        for i, (name, code) in enumerate(self.config.CATEGORIES.items(), 1):
            categories_table.add_row(
                str(i),
                name.capitalize().replace('_', ' '),
                code
            )
        
        panel = Panel(
            categories_table,
            title="[bold]Categorias Disponíveis[/bold]",
            border_style="yellow"
        )
        
        console.print(panel)
        
        choice = Prompt.ask(
            "\n[yellow]Digite o número ou nome da categoria[/yellow]",
            default="1"
        )
        
        # Converter escolha
        try:
            if choice.isdigit():
                idx = int(choice) - 1
                categories = list(self.config.CATEGORIES.keys())
                if 0 <= idx < len(categories):
                    return categories[idx]
            else:
                choice_lower = choice.lower().replace(' ', '_')
                if choice_lower in self.config.CATEGORIES:
                    return choice_lower
        except:
            pass
        
        return "eletronicos"  # Default
    
    def get_search_params(self) -> tuple:
        """Obter parâmetros de busca"""
        max_products = IntPrompt.ask(
            "[green]Quantos produtos coletar?[/green]",
            default=20,
            show_default=True
        )
        
        use_cache = Confirm.ask(
            "[blue]Usar cache (mais rápido)?[/blue]",
            default=True
        )
        
        return max_products, use_cache
    
    async def display_products(self, products: List[Product], title: str = "Produtos Encontrados"):
        """Exibir produtos em tabela formatada"""
        if not products:
            console.print("[red]❌ Nenhum produto encontrado[/red]")
            return
        
        # Tabela de produtos
        table = Table(box=box.ROUNDED, title=f"[bold]{title}[/bold]")
        table.add_column("#", style="bold yellow", width=3)
        table.add_column("Nome", style="cyan", max_width=35)
        table.add_column("Preços", style="bold green", justify="right", width=18)
        table.add_column("Desconto", style="red", justify="center", width=10)
        table.add_column("Link", style="blue", justify="left", width=15)
        table.add_column("Frete", style="green", justify="center", width=8)
        
        for i, product in enumerate(products[:20], 1):  # Mostrar apenas primeiros 20
            # Nome (truncado para nova largura)
            name = product.name[:32] + "..." if len(product.name) > 35 else product.name
            
            # Preços - Mostrar de/por quando há desconto
            if product.original_price and product.original_price > product.price:
                # Formato: ~~R$ 899~~ R$ 488
                original_formatted = f"R$ {product.original_price:,.0f}".replace(',', '.')
                current_formatted = f"R$ {product.price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                from rich.text import Text
                price_display = Text()
                price_display.append(f"~~{original_formatted}~~", style="dim strikethrough")
                price_display.append(f" {current_formatted}", style="bold green")
            else:
                # Só preço atual
                price_display = f"R$ {product.price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if product.price else "N/A"
            
            # Desconto com emoji para destaque
            if product.discount_percentage > 0:
                if product.discount_percentage >= 50:
                    discount_str = f"🔥 {product.discount_percentage:.0f}%"
                elif product.discount_percentage >= 30:
                    discount_str = f"🟡 {product.discount_percentage:.0f}%"
                else:
                    discount_str = f"{product.discount_percentage:.0f}%"
                discount_style = "bold red"
            else:
                discount_str = "-"
                discount_style = "dim"
            
            # Link clicável do produto
            if product.url:
                # Criar link clicável usando hyperlink do Rich
                from rich.text import Text
                link_text = Text("🔗 Abrir", style="blue underline")
                link_text.stylize(f"link {product.url}")
                link_display = link_text
            else:
                link_display = Text("N/A", style="dim")
            
            # Frete
            shipping_str = "✅ Sim" if product.free_shipping else "❌ Não"
            shipping_style = "green" if product.free_shipping else "red"
            
            table.add_row(
                str(i),
                name,
                price_display,
                Text(discount_str, style=discount_style),
                link_display,
                Text(shipping_str, style=shipping_style)
            )
        
        console.print(table)
        
        # Estatísticas
        if len(products) > 1:
            prices = [p.price for p in products if p.price]
            with_discount = [p for p in products if p.discount_percentage > 0]
            promotions = len([p for p in products if p.is_promotion])
            free_shipping = len([p for p in products if p.free_shipping])
            
            stats_table = Table(show_header=False, box=box.SIMPLE)
            stats_table.add_column("Métrica", style="bold")
            stats_table.add_column("Valor", style="cyan")
            
            if prices:
                stats_table.add_row("💰 Preço médio:", f"R$ {sum(prices)/len(prices):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                stats_table.add_row("📈 Maior preço:", f"R$ {max(prices):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                stats_table.add_row("📉 Menor preço:", f"R$ {min(prices):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            
            # Estatísticas de desconto
            if with_discount:
                avg_discount = sum(p.discount_percentage for p in with_discount) / len(with_discount)
                max_discount = max(p.discount_percentage for p in with_discount)
                stats_table.add_row("🏷️ Produtos com desconto:", f"{len(with_discount)} ({len(with_discount)/len(products)*100:.1f}%)")
                stats_table.add_row("📊 Desconto médio:", f"{avg_discount:.1f}%")
                stats_table.add_row("🔥 Maior desconto:", f"{max_discount:.1f}%")
                
                # Economia total
                total_saved = sum((p.original_price - p.price) for p in with_discount if p.original_price)
                if total_saved > 0:
                    stats_table.add_row("💵 Economia total:", f"R$ {total_saved:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            
            stats_table.add_row("🚚 Frete grátis:", f"{free_shipping} ({free_shipping/len(products)*100:.1f}%)")
            
            stats_panel = Panel(
                stats_table,
                title="[bold]📊 Estatísticas[/bold]",
                border_style="green",
                width=50
            )
            
            console.print()
            console.print(stats_panel)
        
        # Instruções sobre links clicáveis
        console.print("\n[dim]💡 Dica: Clique nos links '🔗 Abrir' para acessar os produtos no navegador![/dim]")
        
        # Opções simplificadas
        await self.show_simple_post_collection_menu(products)
    
    async def show_simple_post_collection_menu(self, products: List[Product]):
        """Menu simplificado pós-coleta"""
        
        console.print()
        save_choice = Prompt.ask(
            "[cyan]Deseja salvar os resultados em arquivo?[/cyan]",
            choices=["s", "n"],
            default="s"
        )
        
        if save_choice.lower() == "s":
            await self.save_products(products, "coleta")
            
        console.print("\n[green]✅ Pronto! Use os links clicáveis acima para acessar os produtos.[/green]")
    
    async def show_post_collection_menu(self, products: List[Product]):
        """Menu interativo pós-coleta para ver links e opções adicionais"""
        
        while True:
            console.print()
            choices = [
                "💾 Salvar resultados em arquivo",
                "🔗 Ver links completos dos produtos", 
                "🌐 Abrir produto específico no navegador",
                "📋 Exportar apenas URLs para arquivo",
                "↩️  Voltar ao menu principal"
            ]
            
            choice = Prompt.ask(
                "\n[cyan]O que deseja fazer?[/cyan]",
                choices=[str(i) for i in range(1, len(choices) + 1)],
                default="1"
            )
            
            choice = int(choice)
            
            if choice == 1:
                await self.save_products(products, "coleta")
            elif choice == 2:
                self.show_complete_urls(products)
            elif choice == 3:
                await self.open_product_in_browser(products)
            elif choice == 4:
                self.export_urls_only(products)
            elif choice == 5:
                break
    
    def show_complete_urls(self, products: List[Product]):
        """Mostrar URLs completas dos produtos com links clicáveis"""
        console.print("\n[bold cyan]🔗 Links Completos dos Produtos[/bold cyan]")
        console.print()
        
        for i, product in enumerate(products[:20], 1):
            if product.url:
                # Nome truncado
                name = product.name[:45] + "..." if len(product.name) > 45 else product.name
                console.print(f"[yellow]{i:2d}.[/yellow] [cyan]{name}[/cyan]")
                
                # URL clicável
                from rich.text import Text
                url_text = Text(product.url, style="blue underline")
                url_text.stylize(f"link {product.url}")
                console.print(f"    ", end="")
                console.print(url_text)
                console.print()
        
        input("\n[dim]Pressione Enter para continuar...[/dim]")
    
    async def open_product_in_browser(self, products: List[Product]):
        """Abrir produto específico no navegador"""
        try:
            num = Prompt.ask(
                f"\n[cyan]Digite o número do produto (1-{len(products[:20])})[/cyan]",
                default="1"
            )
            
            product_num = int(num) - 1
            
            if 0 <= product_num < len(products):
                product = products[product_num]
                if product.url:
                    console.print(f"\n[green]🌐 Abrindo produto no navegador...[/green]")
                    console.print(f"[cyan]{product.name}[/cyan]")
                    
                    import webbrowser
                    webbrowser.open(product.url)
                    
                    console.print(f"[green]✅ Produto aberto no seu navegador padrão![/green]")
                else:
                    console.print("[red]❌ URL não disponível para este produto[/red]")
            else:
                console.print("[red]❌ Número de produto inválido[/red]")
                
        except ValueError:
            console.print("[red]❌ Por favor, digite um número válido[/red]")
        except Exception as e:
            console.print(f"[red]❌ Erro ao abrir navegador: {e}[/red]")
    
    def export_urls_only(self, products: List[Product]):
        """Exportar apenas URLs para arquivo texto"""
        from pathlib import Path
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/urls_produtos_{timestamp}.txt"
        
        # Criar diretório se não existir
        Path("data").mkdir(exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# URLs dos Produtos do Mercado Livre\n")
            f.write(f"# Extraído em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"# Total de produtos: {len(products)}\n\n")
            
            for i, product in enumerate(products, 1):
                if product.url:
                    f.write(f"{i:2d}. {product.name}\n")
                    f.write(f"    {product.url}\n\n")
        
        console.print(f"\n[green]✅ URLs exportadas para: {filename}[/green]")
    
    async def save_products(self, products: List[Product], search_type: str):
        """Salvar produtos em arquivo"""
        if not products:
            return
        
        save_file = Confirm.ask(
            "\n[blue]Salvar resultados em arquivo?[/blue]",
            default=True
        )
        
        if save_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/produtos_{search_type}_{timestamp}.json"
            
            # Criar diretório se não existir
            os.makedirs("data", exist_ok=True)
            
            # Salvar como JSON com formato melhorado
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                products_data = []
                for i, product in enumerate(products, 1):
                    data = {
                        "numero": i,
                        "nome": product.name,
                        "preco": product.price,
                        "preco_original": product.original_price,
                        "desconto_percentual": product.discount_percentage,
                        "url_completa": product.url,
                        "produto_id": product.product_id,
                        "imagem_url": product.image_url,
                        "frete_gratis": product.free_shipping,
                        "em_promocao": product.is_promotion,
                        "coletado_em": product.scraped_at.isoformat() if hasattr(product, 'scraped_at') else datetime.now().isoformat()
                    }
                    products_data.append(data)
                
                final_data = {
                    "info": {
                        "total_produtos": len(products),
                        "coletado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "tipo_busca": search_type
                    },
                    "produtos": products_data
                }
                
                json.dump(final_data, f, ensure_ascii=False, indent=2)
            
            console.print(f"[green]✅ Produtos salvos em: {filename}[/green]")
    
    async def search_by_term(self):
        """Buscar produtos por termo"""
        search_term = Prompt.ask("[cyan]Digite o termo de busca[/cyan]")
        max_products, use_cache = self.get_search_params()
        
        # Verificar cache primeiro
        if use_cache:
            async with ScraperCache() as cache:
                cached_products = await cache.get_cached_search(
                    "search_term", 
                    {"term": search_term, "max": max_products}
                )
                
                if cached_products:
                    console.print("[yellow]📦 Usando resultados do cache[/yellow]")
                    await self.display_products(cached_products, f"Busca: {search_term}")
                    await self.save_products(cached_products, f"busca_{search_term.replace(' ', '_')}")
                    return
        
        # Buscar com engine
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task(f"🔍 Buscando '{search_term}'...", total=None)
            
            async with PlaywrightEngine() as engine:
                products = await engine.search_products(search_term, max_products)
            
            progress.update(task, completed=True)
        
        if products:
            # Salvar no cache
            if use_cache:
                async with ScraperCache() as cache:
                    await cache.cache_search_results(
                        "search_term",
                        {"term": search_term, "max": max_products},
                        products
                    )
                    await cache.save_product_history(products)
            
            await self.display_products(products, f"Busca: {search_term}")
            await self.save_products(products, f"busca_{search_term.replace(' ', '_')}")
        else:
            console.print("[red]❌ Nenhum produto encontrado[/red]")
    
    async def search_by_category(self):
        """Buscar produtos por categoria"""
        category = self.show_categories()
        max_products, use_cache = self.get_search_params()
        
        # Verificar cache primeiro  
        if use_cache:
            async with ScraperCache() as cache:
                cached_products = await cache.get_cached_search(
                    "category",
                    {"category": category, "max": max_products}
                )
                
                if cached_products:
                    console.print("[yellow]📦 Usando resultados do cache[/yellow]")
                    await self.display_products(cached_products, f"Categoria: {category.capitalize()}")
                    await self.save_products(cached_products, f"categoria_{category}")
                    return
        
        # Buscar com engine
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task(f"🏷️ Buscando categoria '{category}'...", total=None)
            
            async with PlaywrightEngine() as engine:
                products = await engine.search_category(category, max_products)
            
            progress.update(task, completed=True)
        
        if products:
            # Salvar no cache
            if use_cache:
                async with ScraperCache() as cache:
                    await cache.cache_search_results(
                        "category",
                        {"category": category, "max": max_products},
                        products
                    )
                    await cache.save_product_history(products)
            
            await self.display_products(products, f"Categoria: {category.capitalize()}")
            await self.save_products(products, f"categoria_{category}")
        else:
            console.print("[red]❌ Nenhum produto encontrado[/red]")
    
    async def search_offers(self):
        """Buscar ofertas e promoções"""
        max_products, use_cache = self.get_search_params()
        
        # Verificar cache primeiro
        if use_cache:
            async with ScraperCache() as cache:
                cached_products = await cache.get_cached_search(
                    "offers",
                    {"max": max_products}
                )
                
                if cached_products:
                    console.print("[yellow]📦 Usando resultados do cache[/yellow]")
                    await self.display_products(cached_products, "🔥 Ofertas e Promoções")
                    await self.save_products(cached_products, "ofertas")
                    return
        
        # Buscar com engine
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("🔥 Buscando ofertas...", total=None)
            
            async with PlaywrightEngine() as engine:
                products = await engine.search_offers(max_products)
            
            progress.update(task, completed=True)
        
        if products:
            # Salvar no cache
            if use_cache:
                async with ScraperCache() as cache:
                    await cache.cache_search_results(
                        "offers",
                        {"max": max_products},
                        products
                    )
                    await cache.save_product_history(products)
            
            await self.display_products(products, "🔥 Ofertas e Promoções")
            await self.save_products(products, "ofertas")
        else:
            console.print("[red]❌ Nenhuma oferta encontrada[/red]")
    
    async def show_cache_stats(self):
        """Mostrar estatísticas do cache"""
        async with ScraperCache() as cache:
            stats = await cache.get_cache_stats()
        
        if not stats:
            console.print("[red]❌ Erro ao obter estatísticas[/red]")
            return
        
        stats_table = Table(box=box.ROUNDED, title="[bold]📊 Estatísticas do Cache[/bold]")
        stats_table.add_column("Métrica", style="bold cyan")
        stats_table.add_column("Valor", style="white", justify="right")
        
        metrics = [
            ("🔍 Total de buscas em cache", stats.get('total_cached_searches', 0)),
            ("✅ Buscas válidas no cache", stats.get('valid_cached_searches', 0)),
            ("📦 Total de produtos rastreados", stats.get('total_products_tracked', 0)),
            ("🆔 Produtos únicos", stats.get('unique_products', 0))
        ]
        
        for metric, value in metrics:
            stats_table.add_row(metric, str(value))
        
        console.print(stats_table)
    
    async def cleanup_cache(self):
        """Limpar cache antigo"""
        days = IntPrompt.ask(
            "[yellow]Remover cache mais antigo que quantos dias?[/yellow]",
            default=7
        )
        
        confirm = Confirm.ask(f"[red]Confirma remoção de cache com mais de {days} dias?[/red]")
        
        if confirm:
            async with ScraperCache() as cache:
                await cache.cleanup_old_cache(days)
            console.print("[green]✅ Cache limpo com sucesso[/green]")
        else:
            console.print("[yellow]Operação cancelada[/yellow]")
    
    def show_settings(self):
        """Mostrar configurações do sistema"""
        settings_table = Table(box=box.ROUNDED, title="[bold]⚙️ Configurações do Sistema[/bold]")
        settings_table.add_column("Configuração", style="bold cyan")
        settings_table.add_column("Valor", style="white")
        
        settings = [
            ("🌐 URL Base", self.config.BASE_URL),
            ("⏱️ Delay mínimo", f"{self.config.MIN_DELAY}s"),
            ("⏱️ Delay máximo", f"{self.config.MAX_DELAY}s"),
            ("🔄 Tentativas máximas", str(self.config.MAX_RETRIES)),
            ("📄 Produtos por página", str(self.config.MAX_PRODUCTS_PER_PAGE)),
            ("📚 Páginas máximas", str(self.config.MAX_PAGES_PER_SEARCH)),
            ("💾 TTL do cache", f"{60} minutos"),
            ("🏷️ Categorias disponíveis", str(len(self.config.CATEGORIES)))
        ]
        
        for setting, value in settings:
            settings_table.add_row(setting, value)
        
        console.print(settings_table)
    
    async def run(self):
        """Executar interface principal"""
        try:
            self.show_banner()
            
            while True:
                try:
                    choice = self.show_menu()
                    
                    if choice == "0":
                        console.print("\n[bold blue]👋 Obrigado por usar o ML Scraper v2.0![/bold blue]")
                        break
                    elif choice == "1":
                        await self.search_by_term()
                    elif choice == "2":
                        await self.search_by_category()
                    elif choice == "3":
                        await self.search_offers()
                    elif choice == "4":
                        await self.show_cache_stats()
                    elif choice == "5":
                        await self.cleanup_cache()
                    elif choice == "6":
                        self.show_settings()
                    
                    if choice != "0":
                        console.print("\n[dim]Pressione Enter para continuar...[/dim]")
                        input()
                        console.clear()
                        self.show_banner()
                
                except KeyboardInterrupt:
                    console.print("\n[yellow]⚠️ Operação cancelada pelo usuário[/yellow]")
                    continue
                except Exception as e:
                    console.print(f"\n[red]❌ Erro inesperado: {e}[/red]")
                    continue
        
        except KeyboardInterrupt:
            console.print("\n\n[bold red]👋 Sistema encerrado pelo usuário[/bold red]")
        except Exception as e:
            console.print(f"\n[bold red]❌ Erro crítico: {e}[/bold red]")

def main():
    """Função principal"""
    try:
        app = ModernScraperCLI()
        asyncio.run(app.run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Sistema interrompido[/yellow]")
    except Exception as e:
        console.print(f"[red]Erro crítico: {e}[/red]")

if __name__ == "__main__":
    main()