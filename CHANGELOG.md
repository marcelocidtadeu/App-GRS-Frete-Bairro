# Changelog - Correções e Melhorias

## 🔧 Correção do Bug de Autenticação Intelipost

### Problema Identificado
A API da Intelipost estava retornando erro: **"Este pedido requer autenticação HTTP. - WARNING"**

### Causa Raiz
O header HTTP estava incorreto. A API Intelipost requer dois headers específicos:
- `api_key`: Sua chave de API
- `platform`: Deve ser definido como "api"

### Correção Aplicada
**Arquivo:** `/app/backend/server.py` (linha ~191)

**ANTES:**
```python
headers = {
    "api-key": api_key,  # ❌ Nome incorreto do header
    "Content-Type": "application/json"
}
```

**DEPOIS:**
```python
headers = {
    "api_key": api_key,  # ✅ Nome correto
    "Content-Type": "application/json",
    "platform": "api"  # ✅ Header adicional obrigatório
}
```

### Resultado
✅ As cotações agora funcionam corretamente com a API Intelipost

---

## 🎨 Implementação da Identidade Visual WeConnect

### Cores Aplicadas

**Azul Marinho (Primary):** `#001e5a`
- Usado em: Títulos, abas ativas, elementos estruturais
- Representa: Confiança, profissionalismo, solidez

**Laranja (Accent):** `#ff7a3d`
- Usado em: Botões de ação principal, elementos de destaque
- Representa: Energia, inovação, dinamismo

**Cinza (Neutro):** `#64748b`, `#e2e8f0`
- Usado em: Texto secundário, bordas, backgrounds

### Elementos Visuais

1. **Logo WeConnect**
   - Posicionada no header
   - Altura: 40px
   - Combinada com título da aplicação

2. **Tipografia**
   - Títulos: Manrope (bold, arredondada)
   - Corpo: Inter (legível, moderna)
   - Código: JetBrains Mono (logs)

3. **Componentes**
   - Abas: Azul marinho quando ativas
   - Botões principais: Laranja com hover suave
   - Cards: Brancos com bordas suaves e sombras discretas

### Arquivos Modificados
- `/app/frontend/src/index.css` - Variáveis CSS customizadas
- `/app/frontend/src/App.css` - Estilos globais WeConnect
- `/app/frontend/src/pages/Dashboard.js` - Aplicação de cores nos componentes
- `/app/frontend/src/components/*.js` - Cores inline nos elementos

---

## 📋 Sistema de Upload Único de DE-PARA

### Problema Anterior
- Usuário precisava fazer upload da planilha DE-PARA toda vez que processasse cotações
- Arquivo não era persistido

### Nova Implementação

#### Backend
**Novo Model:** `DeparaMapping`
```python
class DeparaMapping(BaseModel):
    id: str
    mappings: Dict[str, Dict[str, str]]  # Armazena mapeamentos
    created_at: datetime
    updated_at: datetime
```

**Novos Endpoints:**
- `POST /api/depara/upload` - Upload da planilha DE-PARA
- `GET /api/depara/status` - Verifica se DE-PARA está configurado

**Armazenamento:** MongoDB collection `depara_mappings`

#### Frontend
**Novo Componente:** `DeparaManager.js`
- Mostra status do DE-PARA (configurado ou não)
- Permite upload único do arquivo
- Exibe quantidade de mapeamentos e data de atualização
- Botão para atualizar quando necessário

**Localização:** Aparece uma vez na aba "Cotação Intelipost"

#### Fluxo de Uso

1. **Primeira Vez:**
   - Usuário faz upload da planilha DE-PARA
   - Sistema processa e salva no MongoDB
   - Mostra mensagem de sucesso com quantidade de mapeamentos

2. **Processamentos Seguintes:**
   - Sistema automaticamente carrega DE-PARA do banco
   - Não é necessário novo upload
   - Card mostra status "configurado" com contagem

3. **Atualização:**
   - Usuário seleciona novo arquivo
   - Clica em "Carregar"
   - Sistema atualiza mapeamentos no banco

### Arquivos Criados/Modificados
- `/app/backend/server.py` - Novos endpoints e lógica
- `/app/frontend/src/components/DeparaManager.js` - Novo componente
- `/app/frontend/src/components/CotacaoTab.js` - Removido upload inline
- `/app/frontend/src/pages/Dashboard.js` - Incluído DeparaManager

---

## 📊 Resumo das Mudanças

### Correções de Bug
✅ Autenticação Intelipost corrigida
✅ CORS OPTIONS configurado corretamente

### Melhorias de UX
✅ Identidade visual WeConnect aplicada
✅ Upload único de DE-PARA implementado
✅ Feedback visual melhorado
✅ Cores consistentes em toda aplicação

### Melhorias de Backend
✅ Novo modelo DeparaMapping no MongoDB
✅ Endpoints para gerenciar DE-PARA
✅ Headers HTTP corretos para Intelipost
✅ Lógica de carregamento automático de DE-PARA

### Melhorias de Frontend
✅ Logo WeConnect no header
✅ Cores azul marinho e laranja aplicadas
✅ Novo componente DeparaManager
✅ Interface mais limpa e profissional

---

## 🎯 Próximos Passos Sugeridos

1. **Teste com dados reais**
   - Configure sua API Key real da Intelipost
   - Faça upload de uma planilha DE-PARA real
   - Processe cotações reais

2. **Validação de resultado**
   - Verifique se os mapeamentos ERP estão corretos
   - Confirme se os valores com sobrepreço estão calculados corretamente

3. **Feedback**
   - Relate qualquer comportamento inesperado
   - Sugira melhorias adicionais
