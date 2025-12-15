# Cálculo de Sobrepreço - Correção Implementada

## 📊 Problema Identificado

A API Intelipost **JÁ retorna os valores com 135% de sobrepreço aplicado**.

### Exemplo Prático
- **Valor retornado pela API:** R$ 16,38
- **Este valor já inclui:** 135% de acréscimo sobre o valor base
- **Precisamos calcular:** O valor base (sem sobrepreço)

## 🔢 Lógica de Cálculo

### Entendendo o Sobrepreço de 135%

Quando dizemos que um valor tem **135% de sobrepreço**, significa:
```
Valor Final = Valor Base × (1 + 1.35)
Valor Final = Valor Base × 2.35
```

### Cálculo Reverso (API → Valor Base)

Para obter o **valor base** a partir do valor que a API retorna:
```
Valor Base = Valor API ÷ 2.35
```

**Exemplo:**
```
Valor API = R$ 16,38
Valor Base = 16,38 ÷ 2.35 = R$ 6,97
```

### Aplicando o Sobrepreço Configurado

Depois de obter o valor base, aplicamos o sobrepreço configurado pelo usuário:
```
Valor com Sobrepreço = Valor Base × (1 + Sobrepreço% ÷ 100)
```

**Exemplo com sobrepreço de 140%:**
```
Valor Base = R$ 6,97
Valor com Sobrepreço = 6,97 × (1 + 140/100)
Valor com Sobrepreço = 6,97 × 2.40
Valor com Sobrepreço = R$ 16,73
```

## 📋 Colunas na Planilha de Resultado

A planilha Excel gerada agora contém **3 colunas de preço**:

| Coluna | Descrição | Exemplo |
|--------|-----------|---------|
| `final_shipping_cost_api` | Valor retornado pela API Intelipost (com 135% já aplicado) | R$ 16,38 |
| `final_shipping_cost_base` | Valor base calculado (sem nenhum sobrepreço) | R$ 6,97 |
| `final_shipping_cost_com_sobrepreco` | Valor com o sobrepreço configurado pelo usuário aplicado | R$ 16,73 |

## 💡 Casos de Uso

### Caso 1: Usar o sobrepreço padrão da Intelipost (135%)
**Configuração:** Sobrepreço = 135%

```
Valor API: R$ 16,38
Valor Base: R$ 16,38 ÷ 2.35 = R$ 6,97
Valor Final: R$ 6,97 × 2.35 = R$ 16,38 (igual ao da API)
```

### Caso 2: Aumentar o sobrepreço para 150%
**Configuração:** Sobrepreço = 150%

```
Valor API: R$ 16,38
Valor Base: R$ 16,38 ÷ 2.35 = R$ 6,97
Valor Final: R$ 6,97 × 2.50 = R$ 17,43
```

### Caso 3: Reduzir o sobrepreço para 100%
**Configuração:** Sobrepreço = 100%

```
Valor API: R$ 16,38
Valor Base: R$ 16,38 ÷ 2.35 = R$ 6,97
Valor Final: R$ 6,97 × 2.00 = R$ 13,94
```

### Caso 4: Usar apenas o valor base (0% de sobrepreço)
**Configuração:** Sobrepreço = 0%

```
Valor API: R$ 16,38
Valor Base: R$ 16,38 ÷ 2.35 = R$ 6,97
Valor Final: R$ 6,97 × 1.00 = R$ 6,97
```

## 🔧 Implementação no Código

### Backend (`/app/backend/server.py`)

```python
# Obter valor da API (já com 135% aplicado)
final_cost_api = menor_opcao.get("final_shipping_cost")

if final_cost_api is not None:
    # Calcular valor base (remover o sobrepreço de 135%)
    final_cost_base = final_cost_api / 2.35
    
    # Aplicar o sobrepreço configurado pelo usuário
    final_cost_com_sobrepreco = final_cost_base * (1 + sobrepreco / 100)
```

### Estrutura do Resultado

```python
resultados.append({
    "sku": row["sku"],
    "final_shipping_cost_api": final_cost_api,        # Ex: 16.38
    "final_shipping_cost_base": final_cost_base,      # Ex: 6.97
    "final_shipping_cost_com_sobrepreco": final_cost_com_sobrepreco,  # Ex: 16.73
    "carrier": carrier_nome,
    # ... outros campos
})
```

## 📊 Interpretando os Resultados

### Logs Durante Processamento

Os logs agora mostram ambos os valores:
```
[SUCCESS] Linha 1: Transportadora XYZ - Base: R$ 6,97 | Com sobrepreço: R$ 16,73
```

### Planilha Excel

Ao abrir a planilha resultante, você verá:

| SKU | final_shipping_cost_api | final_shipping_cost_base | final_shipping_cost_com_sobrepreco | carrier |
|-----|------------------------|--------------------------|-----------------------------------|---------|
| PROD001 | 16.38 | 6.97 | 16.73 | Transportadora XYZ |
| PROD002 | 22.45 | 9.55 | 22.92 | Transportadora ABC |

**Interpretação:**
- Coluna 1: Valor que a Intelipost retornou
- Coluna 2: **Valor real do frete** (sem markup)
- Coluna 3: **Valor que você deve cobrar** do cliente (com seu sobrepreço)

## ✅ Validação

### Teste Manual

1. Configure um sobrepreço de **135%** (igual ao da API)
2. Processe uma cotação
3. Compare: `final_shipping_cost_api` deve ser **≈ igual** a `final_shipping_cost_com_sobrepreco`
4. A diferença mínima é devido a arredondamentos

### Fórmula de Verificação

```
final_shipping_cost_api ÷ 2.35 × 2.35 ≈ final_shipping_cost_api
```

## 🎯 Benefícios da Correção

1. **Transparência:** Você vê o valor base real do frete
2. **Flexibilidade:** Pode aplicar qualquer sobrepreço desejado
3. **Precisão:** Cálculos matemáticos corretos
4. **Rastreabilidade:** Três valores para análise e auditoria

## 📝 Notas Importantes

- O valor de **135%** é fixo (retornado pela API Intelipost)
- O **sobrepreço configurável** pelo usuário é aplicado sobre o valor base
- Todos os valores são arredondados para 2 casas decimais no display
- Os cálculos internos mantêm precisão de ponto flutuante
