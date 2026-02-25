# Missão Aurora Siger — Ignition Zero Core

Sistema de Verificação de Voo Embarcado para a Missão Aurora Siger.
Computação determinística e autônoma para operação durante a janela crítica de decolagem interplanetária.

---

## Contexto

O atraso de comunicação Terra–Marte pode chegar a **22 minutos**, tornando inviável qualquer intervenção humana em tempo real. O sistema embarcado deve ser **totalmente autônomo e determinístico**, operando sob a filosofia **Fail-Safe**: a decolagem só é autorizada quando **todas** as condições são nominais simultaneamente.

---

## Arquitetura do Sistema

```
aurora-siger/
├── aurora_siger.py       # Script principal — lógica de decisão modular
├── aurora_siger.ipynb    # Notebook com simulações e análises
└── README.md             # Documentação técnica
```

### Fluxo de Execução

```
Sensores → Validação de Entrada → Thresholding → AND Gate → Decisão
                                                     ↓
                                             Log Auditável (caixa-preta)
```

### Módulos

| Módulo | Função |
|---|---|
| `validar_entrada` | Verifica presença e tipo de todos os sensores obrigatórios |
| `digitalizar_sinais` | Thresholding: converte grandezas físicas em estados booleanos |
| `identificar_anomalias` | Gera log auditável de todas as anomalias detectadas |
| `calcular_autonomia` | Computa autonomia energética pós-decolagem |
| `validar_sistemas` | AND Gate — decisão determinística central (Fail-Safe) |
| `imprimir_relatorio` | Saída auditável estilo caixa-preta |

---

## Matriz de Variáveis Críticas

| Variável | Tipo | Faixa Nominal | Sensor |
|---|---|---|---|
| `temperatura` | `float` (°C) | ≤ 35.0°C | Termopar embarcado |
| `integridade` | `bool` (0/1) | == 1 | Extensômetros / ultrassônicos |
| `energia` | `float` (%) | ≥ 80% | Medidor de SoC |
| `pressao` | `float` (PSI) | 90.0 – 110.0 PSI | Piezoresistivo |
| `modulos` | `bool` (flag) | == 1 | Diagnóstico de módulos |

---

## Fórmula de Autonomia Energética

$$\text{Autonomia} = \frac{(\text{Capacidade Total} \times \text{Carga Atual}) - \text{Consumo Decolagem}}{\text{Perdas Energéticas}}$$

Parâmetros utilizados:

| Parâmetro | Valor |
|---|---|
| Capacidade Total | 500.0 kWh |
| Consumo na Decolagem | 120.0 kWh |
| Perdas Energéticas | 8% |

---

## Como Executar

### Pré-requisitos

- Python 3.8+ (sem dependências externas — apenas biblioteca padrão)

### Script Principal

```bash
python aurora_siger.py
```

### Notebook

```bash
jupyter notebook aurora_siger.ipynb
```

---

## Evidências de Execução

### Cenário 1 — Telemetria Nominal

```
============================================================
  AURORA SIGER — IGNITION ZERO CORE
  Timestamp UTC: 2025-06-15T12:00:00.000000
============================================================

  [RESULTADO]: STATUS: PRONTO PARA DECOLAR - SISTEMAS NOMINAIS

  LEITURAS DOS SENSORES:
    • Temperatura     : 28.5°C   (limite: ≤ 35.0°C)
    • Integridade     : 1         (esperado: 1)
    • Energia (SoC)   : 95.0%    (mínimo: 80.0%)
    • Pressão Tanques : 102.3 PSI  (faixa: 90.0–110.0 PSI)
    • Status Módulos  : 1         (esperado: 1)

  ANÁLISE ENERGÉTICA:
    • Capacidade Total     : 500.0 kWh
    • Carga Atual          : 95.0%
    • Consumo na Decolagem : 120.0 kWh
    • Perdas Energéticas   : 8.0%
    • Autonomia Estimada   : 8.88 horas

  INICIANDO SEQUÊNCIA DE IGNIÇÃO...
============================================================
```

### Cenário 2 — Múltiplas Falhas

```
============================================================
  AURORA SIGER — IGNITION ZERO CORE
============================================================

  [RESULTADO]: STATUS: DECOLAGEM ABORTADA - FALHA DE SEGURANÇA DETECTADA

  ANOMALIAS DETECTADAS (3):
    [1] TEMPERATURA CRÍTICA: 42.1°C (limite: 35.0°C)
    [2] ENERGIA INSUFICIENTE: 67.5% (mínimo: 80.0%)
    [3] PRESSÃO FORA DO NOMINAL: 85.0 PSI (faixa: 90.0–110.0 PSI)

  IGNIÇÃO BLOQUEADA. Aguardando correção dos sistemas.
============================================================
```

---

## Princípios de Engenharia Aplicados

| Princípio | Implementação |
|---|---|
| **Fail-Safe** | AND Gate — qualquer falha aborta a sequência |
| **Determinismo** | Ausência de estados ambíguos ou condicionais parciais |
| **Transparência** | Logs auditáveis identificam cada anomalia com valor e limite |
| **Modularidade** | Funções com responsabilidade única e type hints |
| **Footprint Mínimo** | Zero dependências externas — só biblioteca padrão Python |
| **Sem Input Interativo** | Dados via dicionários/streams — sem `input()` |
| **Code Longevity** | Dataclasses, type hints, docstrings, sem efeitos colaterais |

---

## Prompts de IA para Triagem

1. **Classificação de Risco:** *"Classifique estes logs de telemetria bruta em categorias de risco aeroespacial (Nominal, Degradado, Crítico)."*
2. **Identificação de Anomalias:** *"Analise padrões de micro-vibração nestes dados e identifique correlações com possíveis fadigas estruturais prematuras."*
3. **Mitigação Energética:** *"Sugira protocolos de redirecionamento de carga energética caso o módulo de propulsão apresente subpressão."*

---

*Missão Aurora Siger — Ignition Zero Core*
*Desenvolvido para a disciplina de Automação com Python e Fundamentos de IA — FIAP*
