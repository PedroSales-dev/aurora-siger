"""
Aurora Siger - Ignition Zero Core
Sistema de Verificação de Voo Embarcado

Missão: Verificação determinística pré-decolagem com lógica Fail-Safe.
Arquitetura: Modular, tipada, auditável e livre de chamadas interativas.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Constantes de Limiarização (Thresholding / Safe Zones)
# ---------------------------------------------------------------------------

LIMITE_TEMP_MAX: float = 35.0       # Celsius
ENERGIA_MINIMA: float = 80.0        # SoC (%)
PRESSAO_MIN: float = 90.0           # PSI
PRESSAO_MAX: float = 110.0          # PSI

# Constantes para análise energética
CAPACIDADE_TOTAL_KWH: float = 500.0      # kWh (baterias de alta densidade)
CONSUMO_DECOLAGEM_KWH: float = 120.0     # kWh (pico motores + aviônicos)
PERDAS_ENERGETICAS: float = 0.08         # 8% de perda térmica/conversão


# ---------------------------------------------------------------------------
# Estrutura de Dados de Telemetria
# ---------------------------------------------------------------------------

@dataclass
class Telemetria:
    """Representa o pacote de dados de sensores embarcados."""
    temperatura: float    # Graus Celsius
    integridade: float    # Booleano: 1.0 = OK, 0.0 = FALHA
    energia: float        # State of Charge em %
    pressao: float        # PSI (piezoresistivo)
    modulos: float        # Flag: 1.0 = ATIVO, 0.0 = INATIVO
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ResultadoVerificacao:
    """Resultado auditável da verificação de sistemas."""
    pronto: bool
    status: str
    anomalias: List[str]
    timestamp: str
    telemetria: Telemetria
    autonomia_horas: float = 0.0


# ---------------------------------------------------------------------------
# Módulo 1: Validação de Entrada
# ---------------------------------------------------------------------------

SENSORES_OBRIGATORIOS: List[str] = [
    "temperatura", "integridade", "energia", "pressao", "modulos"
]


def validar_entrada(telemetria: Dict[str, float]) -> Tuple[bool, List[str]]:
    """
    Valida a presença e integridade dos campos de telemetria.

    Returns:
        Tuple[bool, List[str]]: (entrada_valida, lista_de_erros)
    """
    erros: List[str] = []

    for sensor in SENSORES_OBRIGATORIOS:
        if sensor not in telemetria:
            erros.append(f"Sensor ausente: '{sensor}'")
        elif not isinstance(telemetria[sensor], (int, float)):
            erros.append(f"Tipo inválido para sensor '{sensor}': {type(telemetria[sensor])}")

    return len(erros) == 0, erros


# ---------------------------------------------------------------------------
# Módulo 2: Thresholding - Digitalização de Sinais Analógicos
# ---------------------------------------------------------------------------

def digitalizar_sinais(telemetria: Dict[str, float]) -> Dict[str, bool]:
    """
    Converte grandezas físicas em estados lógicos booleanos.
    Implementa a estratégia de Thresholding (Limiarização).
    """
    return {
        "temp_ok":  telemetria["temperatura"] <= LIMITE_TEMP_MAX,
        "integ_ok": telemetria["integridade"] == 1.0,
        "ener_ok":  telemetria["energia"] >= ENERGIA_MINIMA,
        "press_ok": PRESSAO_MIN <= telemetria["pressao"] <= PRESSAO_MAX,
        "mod_ok":   telemetria["modulos"] == 1.0,
    }


# ---------------------------------------------------------------------------
# Módulo 3: Identificação de Anomalias
# ---------------------------------------------------------------------------

def identificar_anomalias(
    telemetria: Dict[str, float],
    estados: Dict[str, bool]
) -> List[str]:
    """
    Gera log auditável de todas as anomalias detectadas.
    Garante rastreabilidade (caixa-preta / black-box log).
    """
    anomalias: List[str] = []

    if not estados["temp_ok"]:
        anomalias.append(
            f"TEMPERATURA CRÍTICA: {telemetria['temperatura']}°C "
            f"(limite: {LIMITE_TEMP_MAX}°C)"
        )
    if not estados["integ_ok"]:
        anomalias.append(
            f"FALHA DE INTEGRIDADE ESTRUTURAL: flag={telemetria['integridade']}"
        )
    if not estados["ener_ok"]:
        anomalias.append(
            f"ENERGIA INSUFICIENTE: {telemetria['energia']}% "
            f"(mínimo: {ENERGIA_MINIMA}%)"
        )
    if not estados["press_ok"]:
        anomalias.append(
            f"PRESSÃO FORA DO NOMINAL: {telemetria['pressao']} PSI "
            f"(faixa: {PRESSAO_MIN}–{PRESSAO_MAX} PSI)"
        )
    if not estados["mod_ok"]:
        anomalias.append(
            f"MÓDULOS DE CONTROLE INATIVOS: flag={telemetria['modulos']}"
        )

    return anomalias


# ---------------------------------------------------------------------------
# Módulo 4: Análise Energética
# ---------------------------------------------------------------------------

def calcular_autonomia(carga_atual_pct: float) -> float:
    """
    Calcula autonomia operacional pós-decolagem.

    Fórmula:
        Autonomia = ((Capacidade_Total × Carga_Atual) - Consumo_Decolagem)
                    / Perdas_Energéticas

    Returns:
        float: Autonomia estimada em horas.
    """
    energia_disponivel = CAPACIDADE_TOTAL_KWH * (carga_atual_pct / 100.0)
    energia_util = energia_disponivel - CONSUMO_DECOLAGEM_KWH
    if energia_util <= 0:
        return 0.0
    # Divisão pela taxa de perda representa energia consumida por hora de operação
    autonomia = energia_util / (CAPACIDADE_TOTAL_KWH * PERDAS_ENERGETICAS)
    return round(autonomia, 2)


# ---------------------------------------------------------------------------
# Módulo 5: Lógica de Decisão Principal (AND Gate - Fail-Safe)
# ---------------------------------------------------------------------------

def validar_sistemas(telemetria_raw: Dict[str, float]) -> ResultadoVerificacao:
    """
    Executa verificação determinística completa.

    Filosofia Fail-Safe: decisão AND — todos os sistemas devem ser nominais.
    Qualquer anomalia resulta em DECOLAGEM ABORTADA.

    Args:
        telemetria_raw: Dicionário com leituras brutas dos sensores.

    Returns:
        ResultadoVerificacao: Resultado completo e auditável.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Etapa 1: Validação de entrada
    entrada_valida, erros_entrada = validar_entrada(telemetria_raw)
    if not entrada_valida:
        dados = Telemetria(**{k: 0.0 for k in SENSORES_OBRIGATORIOS})
        return ResultadoVerificacao(
            pronto=False,
            status="ERRO: DADOS DE TELEMETRIA INVÁLIDOS",
            anomalias=erros_entrada,
            timestamp=timestamp,
            telemetria=dados,
            autonomia_horas=0.0,
        )

    dados = Telemetria(
        temperatura=telemetria_raw["temperatura"],
        integridade=telemetria_raw["integridade"],
        energia=telemetria_raw["energia"],
        pressao=telemetria_raw["pressao"],
        modulos=telemetria_raw["modulos"],
        timestamp=timestamp,
    )

    # Etapa 2: Thresholding — digitalização
    estados = digitalizar_sinais(telemetria_raw)

    # Etapa 3: Identificação de anomalias (caixa-preta)
    anomalias = identificar_anomalias(telemetria_raw, estados)

    # Etapa 4: AND Gate — Decisão crítica
    pronto = all(estados.values())

    # Etapa 5: Análise energética
    autonomia = calcular_autonomia(telemetria_raw["energia"]) if pronto else 0.0

    status = (
        "STATUS: PRONTO PARA DECOLAR - SISTEMAS NOMINAIS"
        if pronto
        else "STATUS: DECOLAGEM ABORTADA - FALHA DE SEGURANÇA DETECTADA"
    )

    return ResultadoVerificacao(
        pronto=pronto,
        status=status,
        anomalias=anomalias,
        timestamp=timestamp,
        telemetria=dados,
        autonomia_horas=autonomia,
    )


# ---------------------------------------------------------------------------
# Módulo 6: Saída / Relatório de Log
# ---------------------------------------------------------------------------

def imprimir_relatorio(resultado: ResultadoVerificacao) -> None:
    """Exibe relatório auditável da verificação (log de caixa-preta)."""
    separador = "=" * 60
    print(separador)
    print("  AURORA SIGER — IGNITION ZERO CORE")
    print(f"  Timestamp UTC: {resultado.timestamp}")
    print(separador)
    print(f"\n  [RESULTADO]: {resultado.status}\n")

    t = resultado.telemetria
    print("  LEITURAS DOS SENSORES:")
    print(f"    • Temperatura     : {t.temperatura}°C   (limite: ≤ {LIMITE_TEMP_MAX}°C)")
    print(f"    • Integridade     : {int(t.integridade)}         (esperado: 1)")
    print(f"    • Energia (SoC)   : {t.energia}%    (mínimo: {ENERGIA_MINIMA}%)")
    print(f"    • Pressão Tanques : {t.pressao} PSI  (faixa: {PRESSAO_MIN}–{PRESSAO_MAX} PSI)")
    print(f"    • Status Módulos  : {int(t.modulos)}         (esperado: 1)")

    if resultado.pronto:
        print(f"\n  ANÁLISE ENERGÉTICA:")
        print(f"    • Capacidade Total     : {CAPACIDADE_TOTAL_KWH} kWh")
        print(f"    • Carga Atual          : {t.energia}%")
        print(f"    • Consumo na Decolagem : {CONSUMO_DECOLAGEM_KWH} kWh")
        print(f"    • Perdas Energéticas   : {PERDAS_ENERGETICAS * 100}%")
        print(f"    • Autonomia Estimada   : {resultado.autonomia_horas} horas")
        print("\n  INICIANDO SEQUÊNCIA DE IGNIÇÃO...")
    else:
        print(f"\n  ANOMALIAS DETECTADAS ({len(resultado.anomalias)}):")
        for i, anomalia in enumerate(resultado.anomalias, 1):
            print(f"    [{i}] {anomalia}")
        print("\n  IGNIÇÃO BLOQUEADA. Aguardando correção dos sistemas.")

    print(separador)


# ---------------------------------------------------------------------------
# Ponto de Entrada — Simulação de Telemetria
# ---------------------------------------------------------------------------

# Stream de dados nominal (cenário de sucesso)
TELEMETRIA_NOMINAL: Dict[str, float] = {
    "temperatura": 28.5,
    "integridade": 1.0,
    "energia": 95.0,
    "pressao": 102.3,
    "modulos": 1.0,
}

# Stream de dados com falha (cenário de abortagem)
TELEMETRIA_FALHA: Dict[str, float] = {
    "temperatura": 42.1,   # ACIMA DO LIMITE
    "integridade": 1.0,
    "energia": 67.5,       # ABAIXO DO MÍNIMO
    "pressao": 85.0,       # ABAIXO DA FAIXA
    "modulos": 1.0,
}


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  INICIANDO VERIFICAÇÃO DE SISTEMAS EMBARCADOS")
    print("  Missão Aurora Siger — Ignition Zero")
    print("=" * 60)

    print("\n>>> CENÁRIO 1: Telemetria Nominal")
    resultado_nominal = validar_sistemas(TELEMETRIA_NOMINAL)
    imprimir_relatorio(resultado_nominal)

    print("\n>>> CENÁRIO 2: Telemetria com Falhas")
    resultado_falha = validar_sistemas(TELEMETRIA_FALHA)
    imprimir_relatorio(resultado_falha)
