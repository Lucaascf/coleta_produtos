# 🛒 Sistema Moderno de Web Scraping - Mercado Livre v2.0

Sistema completamente refatorado para coleta automatizada de produtos do Mercado Livre com tecnologias modernas, anti-detecção avançada e interface CLI profissional.

## ✨ Funcionalidades Principais

### 🔍 **Busca Inteligente de Produtos**
- **Busca por termo**: Encontre produtos específicos por palavra-chave
- **Busca por categoria**: Explore produtos por categorias predefinidas
- **Coleta de ofertas**: Foque em produtos em promoção automaticamente
- **Cache inteligente**: Resultados salvos para consultas mais rápidas

### 🛡️ **Anti-Detecção Avançada**
- **Playwright Engine**: Browser real com JavaScript completo
- **Fingerprint Masking**: Esconde indicadores de automação
- **Comportamento Humano**: Movimentos de mouse e scroll realistas
- **Headers Dinâmicos**: Rotação automática de User-Agents e headers
- **Bypass Cloudflare**: Contorna proteções anti-bot automaticamente

### 💾 **Sistema de Cache SQLite**
- **Cache Temporal**: Resultados válidos por 2 horas
- **Histórico de Preços**: Rastreamento de mudanças de preço
- **Performance Analytics**: Métricas de seletores mais eficazes
- **Limpeza Automática**: Remove dados antigos automaticamente

### 🎨 **Interface CLI Moderna**
- **Rich Terminal UI**: Interface colorida e interativa
- **Tabelas Formatadas**: Visualização clara dos produtos
- **Progress Indicators**: Acompanhe o progresso das operações
- **Estatísticas Detalhadas**: Análise completa dos resultados

## 🚀 Instalação e Uso

### Pré-requisitos
- Python 3.8 ou superior
- Conexão com internet
- Sistema Linux/MacOS/Windows

### Instalação

```bash
# 1. Clonar/baixar o projeto
cd afiliado

# 2. Ativar ambiente virtual
source venv/bin/activate

# 3. Instalar dependências (já feito)
pip install -r requirements.txt

# 4. Instalar browsers do Playwright (já feito)
playwright install chromium
```

### Executar o Sistema

```bash
# Executar interface principal
python main.py
```

## 📋 Menu Principal

```
🛒 MERCADO LIVRE SCRAPER v2.0
Sistema Moderno de Web Scraping
Playwright + Anti-Detecção + Cache Inteligente

┌─────────────────────────────────────────────────┐
│                Menu Principal                   │
├─────┬─────────────────────────────────┬─────────┤
│  1  │ 🔍 Buscar produtos por termo    │ ✅ Disp │
│  2  │ 🏷️ Buscar por categoria/nicho  │ ✅ Disp │
│  3  │ 🔥 Coletar ofertas e promoções │ ✅ Disp │
│  4  │ 📊 Ver estatísticas do cache   │ ✅ Disp │
│  5  │ 🧹 Limpar cache antigo         │ ✅ Disp │
│  6  │ ⚙️ Configurações do sistema    │ ✅ Disp │
│  0  │ ❌ Sair                        │         │
└─────┴─────────────────────────────────┴─────────┘
```

## 📊 Dados Coletados

Para cada produto, o sistema extrai:

- **Nome completo** do produto
- **Preço atual** e **preço original** (se em promoção)
- **Percentual de desconto** calculado automaticamente
- **URL** direta para o produto
- **URL da imagem** principal
- **Status de frete grátis**
- **Indicador de promoção**
- **ID único** do produto no ML
- **Timestamp** da coleta

## 🏗️ Arquitetura do Sistema

```
afiliado/
├── scrapers/                    # Core do sistema
│   ├── engines/                # Engines de scraping
│   │   └── playwright_engine.py   # Engine principal
│   ├── detectors/              # Detectores inteligentes
│   │   └── smart_detector.py     # Auto-learning de seletores
│   ├── utils/                  # Utilitários
│   │   ├── stealth.py             # Anti-detecção
│   │   ├── validators.py          # Validação de dados
│   │   └── cache.py               # Sistema de cache
│   └── config.py               # Configurações centrais
├── main.py                     # Interface CLI principal
├── cache/                      # Cache SQLite
├── data/                       # Arquivos de saída
└── requirements.txt            # Dependências
```

## ⚙️ Configurações

### Categorias Disponíveis
- 📱 **Eletrônicos** (MLB1000)
- 📞 **Celulares** (MLB1055)
- 💻 **Informática** (MLB1648)
- 🏠 **Casa** (MLB1574)
- 👕 **Moda** (MLB1430)
- ⚽ **Esportes** (MLB1276)
- 📚 **Livros** (MLB3025)
- 💄 **Beleza** (MLB263532)
- 🎮 **Games** (MLB1144)
- 🚗 **Automotivo** (MLB1743)

### Parâmetros Configuráveis
```python
MIN_DELAY = 1.0              # Delay mínimo entre requisições
MAX_DELAY = 3.0              # Delay máximo entre requisições
MAX_RETRIES = 3              # Tentativas em caso de falha
CACHE_TTL = 2 horas         # Tempo de vida do cache
MAX_PRODUCTS_PER_PAGE = 50   # Produtos por página
MAX_PAGES_PER_SEARCH = 10    # Páginas máximas por busca
```

## 📈 Recursos Avançados

### 🧠 **Detector Inteligente**
- Aprende automaticamente os melhores seletores CSS
- Adapta-se a mudanças na estrutura do site
- Melhora a precisão com o uso contínuo

### 🚀 **Performance**
- Cache SQLite para consultas instantâneas
- Requisições assíncronas para melhor velocidade
- Fallback automático entre diferentes estratégias

### 🔒 **Segurança e Ética**
- Rate limiting respeitoso
- Headers realistas para evitar sobrecarga do servidor
- Comportamento que simula usuário real

## 📁 Saída de Dados

### Formatos Suportados
- **JSON**: Estruturado para processamento automático
- **Cache SQLite**: Para consultas e análise histórica

### Exemplo de Produto
```json
{
  "name": "Smartphone Samsung Galaxy A54 128GB",
  "price": 1299.99,
  "original_price": 1599.99,
  "discount_percentage": 18.75,
  "url": "https://produto.mercadolivre.com.br/MLB...",
  "image_url": "https://http2.mlstatic.com/...",
  "is_promotion": true,
  "free_shipping": true,
  "product_id": "MLB123456789",
  "scraped_at": "2025-01-09T12:30:00"
}
```

## 🔧 Solução de Problemas

### Problemas Comuns

**1. "Engine Playwright não iniciou"**
```bash
# Reinstalar browsers
playwright install chromium
```

**2. "Erro de importação de módulos"**
```bash
# Verificar ambiente virtual
source venv/bin/activate
pip install -r requirements.txt
```

**3. "Nenhum produto encontrado"**
- O site pode estar bloqueando temporariamente
- Aguarde alguns minutos e tente novamente
- Use cache se disponível

**4. "Erro de timeout"**
- Conexão lenta - aumente timeouts em `config.py`
- Site sobrecarregado - tente mais tarde

### Logs e Debug

O sistema mantém logs detalhados de todas as operações:
- Sucessos e falhas de extração
- Performance de seletores
- Estatísticas de cache
- Tempos de resposta

## 🤝 Contribuição e Suporte

### Melhorias Sugeridas
1. **Proxies rotativos** para maior anonimato
2. **API REST** para integração externa
3. **Dashboard web** para monitoramento
4. **Alertas de preço** por email/webhook
5. **Suporte a mais marketplaces**

### Uso Responsável

⚠️ **IMPORTANTE**: Use este sistema de forma ética e responsável:

- Respeite os termos de uso do Mercado Livre
- Não sobrecarregue os servidores com muitas requisições
- Use delays apropriados entre consultas
- Considere usar APIs oficiais quando disponíveis
- Este sistema é para fins educacionais e pessoais

## 📄 Licença

Este projeto é fornecido "como está" para fins educacionais. O uso é por sua conta e risco. Sempre verifique e respeite os termos de uso dos sites que você fizer scraping.

---

**Sistema desenvolvido com:**
- 🎭 **Playwright** - Browser automation
- 🎨 **Rich** - Terminal UI moderna  
- 🗄️ **SQLite** - Cache inteligente
- 🔧 **Pydantic** - Validação de dados
- ⚡ **AsyncIO** - Operações assíncronas