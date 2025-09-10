# 🛒 Mercado Livre Scraper - Interface Gráfica

## ✨ Novidades v2.0

- **🖥️ Interface gráfica simples** com Tkinter
- **🏷️ Classificação automática** por categoria real do ML
- **📊 Filtros avançados** por preço e categoria
- **💾 Exportação Excel/JSON** com dados organizados
- **🔍 Breadcrumb scraping** para categorias exatas

## 🚀 Como usar

### 1. Executar Interface Gráfica
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar GUI
python gui_main.py
```

### 2. Interface CLI (antiga)
```bash
source venv/bin/activate
python main.py
```

## 📋 Funcionalidades

### 🔍 Busca de Produtos
- **Por termo**: Digite qualquer palavra (ex: "iphone")
- **Por categoria**: Escolha entre 13+ categorias
- **Ofertas**: Produtos em promoção com desconto

### 🏷️ Classificação Automática
- **Breadcrumb real**: Extrai categoria da página do produto
- **Fallback inteligente**: Usa palavras-chave se não encontrar
- **Categorias reais**: Nomes exatos como aparecem no ML

### 📊 Filtros
- **Preço**: Min/Max em R$
- **Categoria**: Filtrar por categoria específica
- **Tempo real**: Aplica filtros instantaneamente

### 💾 Exportação
- **Excel**: Arquivo .xlsx formatado
- **JSON**: Dados estruturados com metadata

## 🔧 Dependências Opcionais

Para exportação Excel:
```bash
pip install pandas openpyxl
```

## 📂 Estrutura de Arquivos

```
afiliado/
├── gui_main.py          # Interface gráfica (NOVA)
├── main.py              # Interface CLI (antiga)
├── scrapers/
│   ├── engines/         # Motor de scraping
│   ├── utils/           # Validadores e classificação
│   └── config.py        # Configurações
├── data/                # Arquivos exportados
└── cache/               # Cache do scraper
```

## 🎯 Categorias Suportadas

- 📱 Eletrônicos, Áudio e Vídeo
- 📱 Celulares e Telefones  
- 💻 Informática
- 🏠 Casa, Móveis e Decoração
- 🔌 Eletrodomésticos e Casa
- 👔 Roupas e Calçados
- ⚽ Esportes e Fitness
- 📚 Livros, Revistas e Comics
- 💄 Saúde e Beleza
- 🎮 Games
- 🚗 Carros, Motos e Outros
- ⌚ Relógios e Joias

## ⚡ Melhorias Implementadas

### 🏷️ Classificação Precisa
- ✅ Extração via **breadcrumb** do site
- ✅ **Cache de categorias** para performance
- ✅ **Nomes reais** como aparecem no ML
- ✅ **Fallback inteligente** com palavras-chave

### 🖥️ Interface Melhorada
- ✅ **GUI limpa** e intuitiva
- ✅ **Tabela organizada** com dados claros
- ✅ **Progress bar** durante coleta
- ✅ **Filtros funcionais** em tempo real

### 📊 Dados Organizados
- ✅ **Exportação Excel** formatada
- ✅ **JSON estruturado** com metadata
- ✅ **Estatísticas** por categoria
- ✅ **Links clicáveis** para produtos

## 🔍 Exemplo de Uso

1. **Abrir interface**: `python gui_main.py`
2. **Buscar**: Digite "notebook gamer" e quantidade "30"
3. **Classificação**: Produtos automaticamente categorizados como "Informática"
4. **Filtrar**: Preço entre 1000-5000, categoria "Informática"
5. **Exportar**: Salvar em Excel com formatação

## 💡 Dicas

- **Cache**: Primeiras buscas são mais lentas (criam cache)
- **Categorias**: Sistema híbrido usa breadcrumb + palavras-chave
- **Performance**: GUI mais rápida que CLI
- **Filtros**: Aplicar após coleta completa
- **Export**: Excel precisa pandas instalado