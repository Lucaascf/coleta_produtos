#!/usr/bin/env python3
"""
Interface Gráfica para Mercado Livre Scraper
Tkinter GUI simples e limpa
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import asyncio
import threading
from datetime import datetime
import json
import os
import webbrowser
from typing import List, Optional

# Imports do sistema
from scrapers.engines.playwright_engine import PlaywrightEngine
from scrapers.utils.validators import Product
from scrapers.config import ScraperConfig
from scrapers.affiliate_manager import AffiliateManager

class MercadoLivreScraper:
    """Interface gráfica principal para o scraper"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🛒 Mercado Livre Scraper v2.0")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")
        
        # Variáveis
        self.products: List[Product] = []
        self.config = ScraperConfig()
        self.is_scraping = False
        self.product_urls = {}  # Mapear item_id -> URL dos produtos
        
        # Setup da interface
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interface do usuário"""
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Título
        title_label = ttk.Label(
            main_frame, 
            text="🛒 Mercado Livre Scraper",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Frame de busca
        search_frame = ttk.LabelFrame(main_frame, text="Buscar Produtos", padding="10")
        search_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        # Campo de busca
        ttk.Label(search_frame, text="Termo:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.search_entry = ttk.Entry(search_frame, width=50)
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Quantidade
        ttk.Label(search_frame, text="Qtd:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.quantity_var = tk.StringVar(value="20")
        self.quantity_spin = ttk.Spinbox(
            search_frame, 
            from_=1, 
            to=100, 
            textvariable=self.quantity_var,
            width=5
        )
        self.quantity_spin.grid(row=0, column=3, padx=(0, 10))
        
        # Botões de ação
        self.search_btn = ttk.Button(
            search_frame, 
            text="🔍 Buscar Termo",
            command=self.search_products,
            style="Accent.TButton"
        )
        self.search_btn.grid(row=0, column=4, padx=5)
        
        self.category_btn = ttk.Button(
            search_frame, 
            text="🏷️ Por Categoria",
            command=self.search_category
        )
        self.category_btn.grid(row=0, column=5, padx=5)
        
        self.offers_btn = ttk.Button(
            search_frame, 
            text="🔥 Ofertas",
            command=self.search_offers
        )
        self.offers_btn.grid(row=0, column=6, padx=5)
        
        # Frame de filtros
        filter_frame = ttk.LabelFrame(main_frame, text="Filtros", padding="10")
        filter_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        filter_frame.columnconfigure(3, weight=1)
        
        # Filtro de preço
        ttk.Label(filter_frame, text="Preço Min:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.min_price_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.min_price_var, width=10).grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(filter_frame, text="Preço Max:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.max_price_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.max_price_var, width=10).grid(row=0, column=3, padx=(0, 10))
        
        # Filtro de categoria
        ttk.Label(filter_frame, text="Categoria:").grid(row=0, column=4, sticky=tk.W, padx=(10, 5))
        self.category_filter_var = tk.StringVar(value="Todas")
        self.category_filter = ttk.Combobox(
            filter_frame, 
            textvariable=self.category_filter_var,
            values=[
                "Todas", 
                "Eletrônicos, Áudio e Vídeo", 
                "Celulares e Telefones", 
                "Informática", 
                "Casa, Móveis e Decoração",
                "Eletrodomésticos e Casa",
                "Roupas e Calçados",
                "Esportes e Fitness",
                "Livros, Revistas e Comics",
                "Saúde e Beleza",
                "Games",
                "Carros, Motos e Outros",
                "Relógios e Joias"
            ],
            state="readonly",
            width=20
        )
        self.category_filter.grid(row=0, column=5, padx=(0, 10))
        
        # Botão aplicar filtros
        ttk.Button(
            filter_frame, 
            text="🔄 Aplicar Filtros",
            command=self.apply_filters
        ).grid(row=0, column=6, padx=5)
        
        # Frame dos resultados
        results_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="10")
        results_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Treeview para produtos
        columns = ("nome", "categoria", "preco", "desconto", "frete", "link")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)
        
        # Definir cabeçalhos
        self.tree.heading("nome", text="Nome do Produto")
        self.tree.heading("categoria", text="Categoria")
        self.tree.heading("preco", text="Preço")
        self.tree.heading("desconto", text="Desconto")
        self.tree.heading("frete", text="Frete Grátis")
        self.tree.heading("link", text="Link")
        
        # Definir larguras das colunas
        self.tree.column("nome", width=300)  # Reduzido para dar espaço ao link
        self.tree.column("categoria", width=120)
        self.tree.column("preco", width=180)  # Maior para mostrar preço de/por
        self.tree.column("desconto", width=80)
        self.tree.column("frete", width=80)
        self.tree.column("link", width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid treeview e scrollbars
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Bind para cliques na coluna de link
        self.tree.bind("<Button-1>", self.on_treeview_click)
        
        # Frame de ações
        actions_frame = ttk.Frame(main_frame, padding="5")
        actions_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        # Botões de ação
        ttk.Button(
            actions_frame, 
            text="💾 Exportar Excel",
            command=self.export_excel
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            actions_frame, 
            text="📄 Exportar JSON",
            command=self.export_json
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            actions_frame, 
            text="🔗 Gerar Links Afiliado",
            command=self.generate_affiliate_links
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            actions_frame, 
            text="🗑️ Limpar",
            command=self.clear_results
        ).pack(side=tk.LEFT, padx=5)
        
        # Label de status
        self.status_var = tk.StringVar(value="Pronto para buscar produtos")
        self.status_label = ttk.Label(actions_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(actions_frame, mode="determinate", length=200)
        self.progress.pack(side=tk.RIGHT, padx=(0, 10))
        
    def update_status(self, message: str):
        """Atualizar status na interface"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def start_progress(self, max_value=100):
        """Iniciar progress bar"""
        self.progress['maximum'] = max_value
        self.progress['value'] = 0
        self.is_scraping = True
        
        # Desabilitar botões durante scraping
        for widget in [self.search_btn, self.category_btn, self.offers_btn]:
            widget.configure(state="disabled")
    
    def update_progress(self, current_value, max_value=None, message=""):
        """Atualizar progresso"""
        if max_value:
            self.progress['maximum'] = max_value
        self.progress['value'] = current_value
        
        # Calcular porcentagem
        percentage = (current_value / self.progress['maximum']) * 100 if self.progress['maximum'] > 0 else 0
        
        # Atualizar status com informações detalhadas
        if message:
            status_msg = f"{message} {current_value}/{int(self.progress['maximum'])} ({percentage:.0f}%)"
            self.update_status(status_msg)
        
        self.root.update_idletasks()
    
    def stop_progress(self):
        """Parar progress bar"""
        self.progress['value'] = 0
        self.is_scraping = False
        
        # Reabilitar botões
        for widget in [self.search_btn, self.category_btn, self.offers_btn]:
            widget.configure(state="normal")
    
    def add_products_to_tree(self, products: List[Product]):
        """Adicionar produtos à tabela"""
        for product in products:
            # Formatação dos dados
            nome = product.name[:50] + "..." if len(product.name) > 50 else product.name
            categoria = product.category or "Indefinido"
            
            # Formatação de preço (de/por)
            if product.original_price and product.original_price > product.price:
                # Mostrar: "De R$ 899,00 → R$ 599,00"
                preco_original = f"R$ {product.original_price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                preco_atual = f"R$ {product.price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                preco = f"De {preco_original} → {preco_atual}"
            else:
                # Só preço atual
                preco = f"R$ {product.price:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if product.price else "N/A"
            
            desconto = f"{product.discount_percentage:.0f}%" if product.discount_percentage > 0 else "-"
            frete = "✅ Sim" if product.free_shipping else "❌ Não"
            
            # Link - botão clicável
            link_display = "📋 Copiar" if product.url else "N/A"
            
            # Inserir na tree
            item_id = self.tree.insert("", "end", values=(nome, categoria, preco, desconto, frete, link_display))
            
            # Armazenar URL no dicionário para acesso posterior
            if product.url:
                self.product_urls[item_id] = product.url
    
    def clear_results(self):
        """Limpar resultados"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.products.clear()
        self.product_urls.clear()  # Limpar URLs também
        self.update_status("Resultados limpos")
    
    def on_treeview_click(self, event):
        """Handler para cliques na TreeView"""
        # Identificar onde foi o clique
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        
        # Identificar item e coluna
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        # Verificar se clicou na coluna de link (6ª coluna = #6)
        if column == "#6" and item:
            # Obter URL do dicionário
            url = self.product_urls.get(item)
            if url:
                self.show_link_menu(event, url)
    
    def show_link_menu(self, event, url):
        """Mostrar menu de opções para o link"""
        # Criar menu popup
        popup_menu = tk.Menu(self.root, tearoff=0)
        
        # Função para fechar menu e executar ação
        def close_menu_and_copy():
            popup_menu.unpost()
            popup_menu.destroy()
            self.copy_to_clipboard(url)
        
        def close_menu_and_open():
            popup_menu.unpost()
            popup_menu.destroy()
            self.open_in_browser(url)
        
        popup_menu.add_command(
            label="📋 Copiar Link", 
            command=close_menu_and_copy
        )
        popup_menu.add_command(
            label="🌐 Abrir no Navegador", 
            command=close_menu_and_open
        )
        
        # Função para fechar menu ao clicar fora
        def close_on_click_outside(e):
            # Verificar se clique foi fora do menu
            try:
                if popup_menu.winfo_exists():
                    popup_menu.unpost()
                    popup_menu.destroy()
            except:
                pass
            # Remover bind após uso
            self.root.unbind("<Button-1>")
        
        # Mostrar menu na posição do mouse
        try:
            popup_menu.tk_popup(event.x_root, event.y_root)
            popup_menu.grab_set()  # Capturar eventos
            
            # Bind para fechar ao clicar fora (com delay para não interferir com o clique atual)
            self.root.after(100, lambda: self.root.bind("<Button-1>", close_on_click_outside))
            
        except Exception:
            # Se der erro, tentar fechar menu
            try:
                popup_menu.unpost()
                popup_menu.destroy()
            except:
                pass
    
    def copy_to_clipboard(self, url):
        """Copiar URL para clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self.root.update()  # Garantir que o clipboard seja atualizado
        self.update_status("Link copiado para a área de transferência")
    
    def open_in_browser(self, url):
        """Abrir URL no navegador padrão"""
        try:
            webbrowser.open(url)
            self.update_status("Link aberto no navegador")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o link: {e}")
    
    def search_products(self):
        """Buscar produtos por termo"""
        search_term = self.search_entry.get().strip()
        if not search_term:
            messagebox.showwarning("Aviso", "Digite um termo de busca")
            return
        
        quantity = int(self.quantity_var.get())
        
        # Executar busca em thread separada
        thread = threading.Thread(
            target=self._run_search,
            args=(search_term, quantity, "term")
        )
        thread.daemon = True
        thread.start()
    
    def search_category(self):
        """Buscar produtos por múltiplas categorias"""
        quantity = int(self.quantity_var.get())
        
        # Diálogo para escolher categorias
        category_window = tk.Toplevel(self.root)
        category_window.title("Escolher Categorias")
        category_window.geometry("350x500")
        category_window.transient(self.root)
        
        ttk.Label(category_window, text="Selecione uma ou mais categorias:", font=("Arial", 12)).pack(pady=10)
        
        # Frame com scroll para as categorias
        canvas = tk.Canvas(category_window)
        scrollbar = ttk.Scrollbar(category_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Lista de categorias com checkboxes
        categories = list(self.config.CATEGORIES.keys())
        category_vars = {}
        
        for category in categories:
            var = tk.BooleanVar()
            category_vars[category] = var
            ttk.Checkbutton(
                scrollable_frame,
                text=category.capitalize().replace('_', ' '),
                variable=var
            ).pack(anchor="w", padx=20, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")
        
        # Frame para botões
        button_frame = ttk.Frame(category_window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        def select_all():
            for var in category_vars.values():
                var.set(True)
        
        def select_none():
            for var in category_vars.values():
                var.set(False)
        
        def on_search():
            # Obter categorias selecionadas
            selected_categories = [
                category for category, var in category_vars.items() 
                if var.get()
            ]
            
            if not selected_categories:
                messagebox.showwarning("Aviso", "Selecione pelo menos uma categoria")
                return
            
            category_window.destroy()
            
            # Executar busca para múltiplas categorias
            thread = threading.Thread(
                target=self._run_search,
                args=(selected_categories, quantity, "categories")
            )
            thread.daemon = True
            thread.start()
        
        # Botões de ação
        ttk.Button(button_frame, text="Selecionar Todas", command=select_all).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Limpar Seleção", command=select_none).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Buscar", command=on_search).pack(side="right", padx=5)
    
    def search_offers(self):
        """Buscar ofertas"""
        quantity = int(self.quantity_var.get())
        
        thread = threading.Thread(
            target=self._run_search,
            args=("", quantity, "offers")
        )
        thread.daemon = True
        thread.start()
    
    def _run_search(self, term, quantity: int, search_type: str):
        """Executar busca (roda em thread separada)"""
        try:
            # Atualizar UI
            self.root.after(0, self.start_progress, quantity)
            self.root.after(0, self.update_status, f"Iniciando busca...")
            
            # Callback para atualizar progresso
            def progress_callback(current, total, message="Buscando..."):
                self.root.after(0, self.update_progress, current, total, message)
            
            # Executar busca assíncrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def search():
                async with PlaywrightEngine() as engine:
                    if search_type == "term":
                        if hasattr(engine, 'search_products_with_progress'):
                            return await engine.search_products_with_progress(term, quantity, progress_callback)
                        else:
                            return await engine.search_products(term, quantity)
                    elif search_type == "category":
                        if hasattr(engine, 'search_category_with_progress'):
                            return await engine.search_category_with_progress(term, quantity, progress_callback)
                        else:
                            return await engine.search_category(term, quantity)
                    elif search_type == "categories":
                        # Busca por múltiplas categorias
                        all_products = []
                        for i, category in enumerate(term):
                            self.root.after(0, self.update_status, f"Buscando categoria {i+1}/{len(term)}: {category}")
                            if hasattr(engine, 'search_category_with_progress'):
                                category_products = await engine.search_category_with_progress(
                                    category, quantity // len(term), progress_callback
                                )
                            else:
                                category_products = await engine.search_category(category, quantity // len(term))
                            if category_products:
                                all_products.extend(category_products)
                        return all_products
                    elif search_type == "offers":
                        if hasattr(engine, 'search_offers_with_progress'):
                            return await engine.search_offers_with_progress(quantity, progress_callback)
                        else:
                            return await engine.search_offers(quantity)
            
            products = loop.run_until_complete(search())
            loop.close()
            
            # Atualizar UI com resultados
            if products:
                self.products.extend(products)
                self.root.after(0, self.add_products_to_tree, products)
                
                # Salvar automaticamente
                self.root.after(0, self._auto_save_products, products, search_type)
                
                self.root.after(0, self.update_status, f"✅ Concluído! {len(products)} produtos encontrados e salvos")
            else:
                self.root.after(0, self.update_status, "❌ Nenhum produto encontrado")
                self.root.after(0, messagebox.showinfo, "Resultado", "Nenhum produto encontrado")
            
        except Exception as e:
            self.root.after(0, self.update_status, f"❌ Erro: {str(e)}")
            self.root.after(0, messagebox.showerror, "Erro", f"Erro ao buscar produtos:\n{str(e)}")
        
        finally:
            self.root.after(0, self.stop_progress)
    
    def apply_filters(self):
        """Aplicar filtros aos resultados"""
        if not self.products:
            messagebox.showwarning("Aviso", "Nenhum produto para filtrar")
            return
        
        # Obter critérios de filtro
        min_price_text = self.min_price_var.get().strip()
        max_price_text = self.max_price_var.get().strip()
        category_filter = self.category_filter_var.get()
        
        # Converter preços
        min_price = None
        max_price = None
        
        try:
            if min_price_text:
                min_price = float(min_price_text.replace(',', '.'))
        except ValueError:
            messagebox.showerror("Erro", "Preço mínimo inválido")
            return
        
        try:
            if max_price_text:
                max_price = float(max_price_text.replace(',', '.'))
        except ValueError:
            messagebox.showerror("Erro", "Preço máximo inválido")
            return
        
        # Aplicar filtros
        filtered_products = []
        
        for product in self.products:
            # Filtro de preço
            if min_price and product.price and product.price < min_price:
                continue
            if max_price and product.price and product.price > max_price:
                continue
            
            # Filtro de categoria
            if category_filter != "Todas":
                if not product.category or product.category != category_filter:
                    continue
            
            filtered_products.append(product)
        
        # Limpar e mostrar produtos filtrados
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.add_products_to_tree(filtered_products)
        
        self.update_status(f"Filtros aplicados: {len(filtered_products)} produtos encontrados")
    
    def export_excel(self):
        """Exportar para Excel"""
        if not self.products:
            messagebox.showwarning("Aviso", "Nenhum produto para exportar")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Salvar como Excel"
        )
        
        if filename:
            try:
                # Tentar importar pandas para Excel
                try:
                    import pandas as pd
                except ImportError:
                    messagebox.showerror("Erro", "Pandas não instalado.\nInstale com: pip install pandas openpyxl")
                    return
                
                # Preparar dados para DataFrame
                data = []
                for i, product in enumerate(self.products, 1):
                    data.append({
                        'Número': i,
                        'Nome': product.name,
                        'Categoria': product.category or 'Indefinido',
                        'Preço': product.price,
                        'Preço Original': product.original_price,
                        'Desconto %': product.discount_percentage,
                        'URL': product.url,
                        'Frete Grátis': 'Sim' if product.free_shipping else 'Não',
                        'Em Promoção': 'Sim' if product.is_promotion else 'Não',
                        'Confiança Categoria': f"{product.category_confidence:.2f}"
                    })
                
                # Criar DataFrame e salvar
                df = pd.DataFrame(data)
                
                # Salvar no Excel com formatação
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Produtos ML', index=False)
                    
                    # Obter worksheet para formatação
                    worksheet = writer.sheets['Produtos ML']
                    
                    # Ajustar largura das colunas
                    for column in worksheet.columns:
                        max_length = 0
                        column = [cell for cell in column]
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
                
                messagebox.showinfo("Sucesso", f"Dados exportados para:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar:\n{str(e)}")
    
    def _auto_save_products(self, products, search_type):
        """Salvar produtos automaticamente após busca"""
        if not products:
            return
            
        try:
            from datetime import datetime
            import os
            
            # Criar diretório se não existir
            os.makedirs("data", exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/produtos_{search_type}_{timestamp}.json"
            
            # Preparar dados para salvar
            products_data = []
            for i, product in enumerate(products, 1):
                data = {
                    "numero": i,
                    "nome": product.name,
                    "categoria": product.category,
                    "categoria_confianca": product.category_confidence,
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
            
            # Calcular estatísticas de categoria
            categories_stats = {}
            for product in products:
                if product.category:
                    if product.category not in categories_stats:
                        categories_stats[product.category] = {
                            "total": 0,
                            "confianca_media": 0.0,
                            "confiancas": []
                        }
                    categories_stats[product.category]["total"] += 1
                    categories_stats[product.category]["confiancas"].append(product.category_confidence)
            
            # Calcular confiança média
            for category, stats in categories_stats.items():
                if stats["confiancas"]:
                    stats["confianca_media"] = sum(stats["confiancas"]) / len(stats["confiancas"])
                    del stats["confiancas"]
            
            final_data = {
                "info": {
                    "total_produtos": len(products),
                    "coletado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "tipo_busca": search_type,
                    "categorias_encontradas": categories_stats
                },
                "produtos": products_data
            }
            
            # Salvar arquivo
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
                
            messagebox.showinfo("Auto-salvo", f"Produtos salvos automaticamente:\n{filename}\n\n🔗 Use 'Gerar Links Afiliado' para criar os links!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar automaticamente:\n{str(e)}")
    
    def export_json(self):
        """Exportar para JSON"""
        if not self.products:
            messagebox.showwarning("Aviso", "Nenhum produto para exportar")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Salvar como JSON"
        )
        
        if filename:
            try:
                # Preparar dados
                export_data = {
                    "info": {
                        "total_produtos": len(self.products),
                        "exportado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    },
                    "produtos": []
                }
                
                for i, product in enumerate(self.products, 1):
                    export_data["produtos"].append({
                        "numero": i,
                        "nome": product.name,
                        "categoria": product.category,
                        "preco": product.price,
                        "preco_original": product.original_price,
                        "desconto_percentual": product.discount_percentage,
                        "url": product.url,
                        "frete_gratis": product.free_shipping,
                        "em_promocao": product.is_promotion
                    })
                
                # Salvar arquivo
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("Sucesso", f"Dados exportados para:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar:\n{str(e)}")
    
    def generate_affiliate_links(self):
        """Gerar links de afiliado a partir de arquivos de produtos"""
        # Verificar se há arquivos de produtos disponíveis
        data_dir = "data"
        if not os.path.exists(data_dir):
            messagebox.showwarning("Aviso", "Pasta 'data' não encontrada.\nExecute primeiro uma coleta de produtos.")
            return
        
        # Buscar arquivos JSON de produtos
        product_files = []
        for file in os.listdir(data_dir):
            if file.startswith("produtos_") and file.endswith(".json"):
                product_files.append(os.path.join(data_dir, file))
        
        if not product_files:
            messagebox.showwarning("Aviso", "Nenhum arquivo de produtos encontrado na pasta 'data'.\nExecute primeiro uma coleta de produtos (opções de busca).")
            return
        
        # Ordenar por data de modificação (mais recente primeiro)
        product_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Mostrar janela de seleção
        self._show_affiliate_window(product_files)
    
    def _show_affiliate_window(self, product_files):
        """Mostrar janela para seleção de arquivo e processamento"""
        # Criar janela modal
        affiliate_window = tk.Toplevel(self.root)
        affiliate_window.title("🔗 Gerador de Links de Afiliado")
        affiliate_window.geometry("700x500")
        affiliate_window.transient(self.root)
        affiliate_window.grab_set()
        
        # Centralizar janela
        affiliate_window.update_idletasks()
        x = (affiliate_window.winfo_screenwidth() // 2) - (700 // 2)
        y = (affiliate_window.winfo_screenheight() // 2) - (500 // 2)
        affiliate_window.geometry(f"700x500+{x}+{y}")
        
        # Frame principal
        main_frame = ttk.Frame(affiliate_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título e descrição
        title_label = ttk.Label(
            main_frame,
            text="🔗 Gerador de Links de Afiliado",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        desc_label = ttk.Label(
            main_frame,
            text="Esta ferramenta converte links de produtos em links de afiliado do Mercado Pago",
            font=("Arial", 10)
        )
        desc_label.pack(pady=(0, 20))
        
        # Frame para lista de arquivos
        files_frame = ttk.LabelFrame(main_frame, text="Arquivos de Produtos Disponíveis", padding="10")
        files_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeview para arquivos
        columns = ("arquivo", "data", "produtos")
        files_tree = ttk.Treeview(files_frame, columns=columns, show="headings", height=8)
        
        # Definir cabeçalhos
        files_tree.heading("arquivo", text="Nome do Arquivo")
        files_tree.heading("data", text="Data de Criação")
        files_tree.heading("produtos", text="Produtos")
        
        # Definir larguras
        files_tree.column("arquivo", width=300)
        files_tree.column("data", width=150)
        files_tree.column("produtos", width=100)
        
        # Scrollbar para a lista
        files_scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=files_tree.yview)
        files_tree.configure(yscrollcommand=files_scrollbar.set)
        
        # Grid
        files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Preencher lista de arquivos
        for file_path in product_files[:10]:  # Mostrar até 10 arquivos
            filename = os.path.basename(file_path)
            file_date = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%d/%m/%Y %H:%M")
            
            # Tentar contar produtos no arquivo
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    product_count = len(data.get('produtos', []))
            except:
                product_count = "?"
            
            files_tree.insert("", "end", values=(filename, file_date, product_count))
        
        # Frame de informações importantes
        info_frame = ttk.LabelFrame(main_frame, text="⚠️ Informações Importantes", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_text = """• O navegador será aberto para fazer login no Mercado Livre
• Você precisa ter uma conta de vendedor/afiliado ativa
• O processo pode demorar alguns minutos dependendo da quantidade de produtos
• Faça login manualmente quando solicitado"""
        
        ttk.Label(info_frame, text=info_text, font=("Arial", 9)).pack(anchor="w")
        
        # Frame de progresso (inicialmente oculto)
        self.affiliate_progress_frame = ttk.LabelFrame(main_frame, text="Progresso", padding="10")
        
        # Progress bar para afiliados
        self.affiliate_progress_var = tk.StringVar(value="Pronto para processar...")
        self.affiliate_progress_label = ttk.Label(self.affiliate_progress_frame, textvariable=self.affiliate_progress_var)
        self.affiliate_progress_label.pack(pady=(0, 5))
        
        self.affiliate_progress_bar = ttk.Progressbar(self.affiliate_progress_frame, mode="determinate", length=400)
        self.affiliate_progress_bar.pack(pady=(0, 5))
        
        # Label de estatísticas
        self.affiliate_stats_var = tk.StringVar()
        self.affiliate_stats_label = ttk.Label(self.affiliate_progress_frame, textvariable=self.affiliate_stats_var)
        self.affiliate_stats_label.pack()
        
        # Frame de botões
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Variáveis de controle
        self.affiliate_processing = False
        
        def on_process():
            # Obter arquivo selecionado
            selection = files_tree.selection()
            if not selection:
                messagebox.showwarning("Aviso", "Selecione um arquivo para processar")
                return
            
            # Obter o arquivo correspondente
            item = files_tree.item(selection[0])
            filename = item['values'][0]
            selected_file = None
            
            for file_path in product_files:
                if os.path.basename(file_path) == filename:
                    selected_file = file_path
                    break
            
            if not selected_file:
                messagebox.showerror("Erro", "Arquivo selecionado não encontrado")
                return
            
            # Confirmar processamento
            product_count = item['values'][2]
            confirm = messagebox.askyesno(
                "Confirmar Processamento",
                f"Processar arquivo '{filename}' com {product_count} produtos?\n\nEsta operação pode demorar alguns minutos."
            )
            
            if not confirm:
                return
            
            # Mostrar frame de progresso
            self.affiliate_progress_frame.pack(fill=tk.X, pady=(10, 0))
            
            # Desabilitar botão
            process_btn.configure(state="disabled")
            close_btn.configure(text="Cancelar", command=lambda: self._cancel_affiliate_processing(affiliate_window))
            
            # Executar processamento em thread
            thread = threading.Thread(
                target=self._run_affiliate_generation,
                args=(selected_file, affiliate_window, process_btn, close_btn)
            )
            thread.daemon = True
            thread.start()
        
        def on_close():
            if not self.affiliate_processing:
                affiliate_window.destroy()
            else:
                if messagebox.askyesno("Confirmar", "Processamento em andamento.\nDeseja realmente fechar?"):
                    self.affiliate_processing = False
                    affiliate_window.destroy()
        
        # Botões
        process_btn = ttk.Button(buttons_frame, text="🚀 Processar Arquivo", command=on_process)
        process_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        close_btn = ttk.Button(buttons_frame, text="Fechar", command=on_close)
        close_btn.pack(side=tk.RIGHT)
        
        # Protocolo de fechamento
        affiliate_window.protocol("WM_DELETE_WINDOW", on_close)
    
    def _run_affiliate_generation(self, file_path, window, process_btn, close_btn):
        """Executar geração de links em thread separada"""
        try:
            self.affiliate_processing = True
            
            # Callback para atualizar progresso
            def progress_callback(current, total, message="Processando..."):
                window.after(0, self._update_affiliate_progress, current, total, message)
            
            # Atualizar UI inicial
            window.after(0, self._update_affiliate_progress, 0, 100, "Iniciando processamento...")
            
            # Executar processamento assíncrono
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def process():
                async with AffiliateManager() as affiliate_manager:
                    return await affiliate_manager.process_product_file(file_path)
            
            results = loop.run_until_complete(process())
            loop.close()
            
            # Verificar resultados
            if "error" in results:
                window.after(0, lambda: messagebox.showerror("Erro", f"Erro durante processamento:\n{results['error']}"))
            else:
                success_count = results.get('success_count', 0)
                error_count = results.get('error_count', 0)
                total_products = success_count + error_count
                
                # Estatísticas finais
                stats_msg = f"✅ Concluído! {success_count}/{total_products} links gerados"
                if error_count > 0:
                    stats_msg += f" ({error_count} falhas)"
                
                window.after(0, self.affiliate_stats_var.set, stats_msg)
                window.after(0, self.affiliate_progress_var.set, "Processamento concluído!")
                window.after(0, lambda: self.affiliate_progress_bar.configure(value=100))
                
                # Mostrar resultado
                window.after(0, lambda: messagebox.showinfo(
                    "Sucesso",
                    f"Processamento concluído!\n\n"
                    f"✅ Links gerados: {success_count}\n"
                    f"❌ Falhas: {error_count}\n"
                    f"📁 Resultados salvos na pasta 'data'"
                ))
        
        except Exception as e:
            window.after(0, lambda: messagebox.showerror("Erro", f"Erro inesperado:\n{str(e)}"))
            window.after(0, self.affiliate_progress_var.set, f"Erro: {str(e)}")
        
        finally:
            self.affiliate_processing = False
            # Reabilitar botões
            window.after(0, lambda: process_btn.configure(state="normal"))
            window.after(0, lambda: close_btn.configure(text="Fechar"))
    
    def _update_affiliate_progress(self, current, total, message=""):
        """Atualizar progresso da geração de links"""
        if total > 0:
            percentage = (current / total) * 100
            self.affiliate_progress_bar.configure(value=percentage)
        
        if message:
            progress_text = f"{message}"
            if total > 0:
                progress_text += f" ({current}/{total} - {percentage:.0f}%)"
            self.affiliate_progress_var.set(progress_text)
    
    def _cancel_affiliate_processing(self, window):
        """Cancelar processamento de links de afiliado"""
        if messagebox.askyesno("Cancelar", "Deseja realmente cancelar o processamento?"):
            self.affiliate_processing = False
            window.destroy()
    
    def run(self):
        """Executar aplicação"""
        self.root.mainloop()

def main():
    """Função principal"""
    app = MercadoLivreScraper()
    app.run()

if __name__ == "__main__":
    main()