# Processador de Planilhas Excel

Aplicação web profissional para automatizar processamento de planilhas Excel com duas funcionalidades principais:

1. **Cotação de Frete via Intelipost** - Com sobrepreço configurável e mapeamento DE-PARA de transportadoras
2. **Busca de Bairro/Cidade/UF por CEP** - Usando a API ViaCEP

## 🎯 Funcionalidades

### Módulo de Cotação Intelipost

- Upload de planilha Excel (.xlsx) com dados de produtos e destinos
- Consulta automática à API Intelipost para cotação de frete
- Seleção automática da melhor opção (menor custo)
- Cálculo de valor base (API Intelipost retorna com 135% já aplicado)
- Aplicação de sobrepreço configurável sobre o valor base
- Suporte a planilha DE-PARA para mapeamento de transportadoras
- Download do resultado em Excel com 3 colunas de preço (API, Base, Com Sobrepreço)
- Transparência total dos valores para análise

**Colunas obrigatórias na planilha de entrada:**
- `sku` - Código do produto
- `ceporigem` - CEP de origem
- `cepdestino` - CEP de destino
- `peso` - Peso em kg
- `precoproduto` - Preço do produto
- `comprimento` - Comprimento em cm
- `altura` - Altura em cm
- `largura` - Largura em cm

**Planilha DE-PARA (opcional):**
- `intelipost` ou `transportadora` - Nome da transportadora retornado pela Intelipost
- `erp` ou `transportadora_erp` - Nome no seu ERP
- `codigo_erp` - Código da transportadora no ERP

### Módulo de Busca de CEP

- Upload de planilha Excel (.xlsx) com lista de CEPs
- Consulta automática à API ViaCEP
- Retorno de Bairro, Cidade e UF para cada CEP
- Tratamento de CEPs inválidos em aba separada
- Download do resultado enriquecido em Excel

**Colunas obrigatórias na planilha de entrada:**
- `CEP` - Lista de CEPs a serem consultados

### Histórico de Processamentos

- Visualização de todos os processamentos realizados
- Informações detalhadas: tipo, arquivo, status, quantidade de linhas processadas e erros
- Data e hora de cada processamento

## 🚀 Como Usar

### 1. Configuração Inicial

1. Clique no botão **"Configurações"** no canto superior direito
2. Insira sua **API Key da Intelipost**
3. Configure o **Sobrepreço Padrão** (exemplo: 135% = 2,35x o valor base)
   - **IMPORTANTE:** A API Intelipost já retorna valores com 135% aplicado
   - O sistema calcula automaticamente o valor base e aplica seu sobrepreço
4. Clique em **"Salvar Configuração"**

### 2. Cotação de Frete

1. Acesse a aba **"Cotação Intelipost"**
2. Configure o sobrepreço (ou use o padrão)
3. (Opcional) Faça upload da planilha DE-PARA
4. Arraste ou selecione o arquivo Excel com os dados
5. Clique em **"Executar Cotações"**
6. Acompanhe o progresso e os logs em tempo real
7. O arquivo será baixado automaticamente ao concluir

### 3. Busca de CEP

1. Acesse a aba **"Busca CEP"**
2. Arraste ou selecione o arquivo Excel com os CEPs
3. Clique em **"Buscar Bairros"**
4. Acompanhe o progresso e os logs em tempo real
5. O arquivo será baixado automaticamente ao concluir

### 4. Consultar Histórico

1. Acesse a aba **"Histórico"**
2. Visualize todos os processamentos anteriores
3. Veja detalhes como status, quantidade de linhas e erros

## 🎨 Design

A aplicação segue um design profissional corporativo com:

- **Cores principais:** Azul (#2563EB) e Cinza Slate
- **Tipografia:** Manrope (títulos), Inter (corpo), JetBrains Mono (logs)
- **Layout limpo e organizado** com foco em usabilidade
- **Feedback visual** durante processamento (barra de progresso e logs)
- **Responsivo** para diferentes tamanhos de tela

## 📋 Requisitos Técnicos

- **Backend:** FastAPI (Python) com pandas, openpyxl, xlsxwriter
- **Frontend:** React com Shadcn/UI, Tailwind CSS
- **Banco de dados:** MongoDB (para configurações e histórico)
- **APIs externas:**
  - Intelipost API (cotação de frete)
  - ViaCEP API (consulta de endereços)

## 🔒 Segurança

- API Keys armazenadas no backend (não expostas no frontend)
- Mascaramento de API Key na interface (exibe apenas primeiros e últimos 4 caracteres)
- Validação de dados antes do processamento
- Tratamento de erros com mensagens claras

## 📊 Limites

- Processamento otimizado para até 100 linhas por execução
- Timeout de 60 segundos por requisição
- Retry automático para erros temporários (429, 5xx)
- Delay entre requisições para evitar rate limiting

## 🆘 Troubleshooting

### Erro "Configure a API Key da Intelipost primeiro"
- Acesse Configurações e insira sua API Key

### Erro "Colunas obrigatórias faltando"
- Verifique se sua planilha contém todas as colunas obrigatórias
- Os nomes das colunas devem corresponder exatamente (ignorando maiúsculas/minúsculas)

### CEPs sem retorno
- CEPs inválidos ou não cadastrados no ViaCEP serão listados na aba "falhas" do arquivo de resultado

### Processamento lento
- A velocidade depende das APIs externas (Intelipost e ViaCEP)
- Há delays intencionais entre requisições para respeitar rate limits

## 🎯 Próximas Melhorias Sugeridas

Gostaria de expandir a aplicação? Considere:

1. **Exportação de relatórios analíticos** - Gráficos de custos por região, comparativo de transportadoras
2. **Processamento em lote** - Upload de múltiplos arquivos simultaneamente
3. **Agendamento de processamentos** - Executar automaticamente em horários específicos
4. **Notificações por email** - Avisar quando processamento for concluído
5. **Integração com outras APIs de frete** - Melhor Envio, Correios, etc.

## 📝 Notas

- A aplicação não requer autenticação (acesso aberto)
- Os arquivos processados não são armazenados permanentemente
- O histórico persiste no banco de dados
- Todos os processamentos são síncronos com feedback em tempo real
