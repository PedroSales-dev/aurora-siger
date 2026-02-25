"""
Gerador de Relatório PDF — Missão Aurora Siger
Executa: python3 gerar_relatorio.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Preformatted
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from aurora_siger import (
    validar_sistemas, calcular_autonomia,
    LIMITE_TEMP_MAX, ENERGIA_MINIMA, PRESSAO_MIN, PRESSAO_MAX,
    CAPACIDADE_TOTAL_KWH, CONSUMO_DECOLAGEM_KWH, PERDAS_ENERGETICAS,
    TELEMETRIA_NOMINAL, TELEMETRIA_FALHA,
)

# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
styles = getSampleStyleSheet()

AZUL_ESCURO = colors.HexColor("#0D1B2A")
AZUL_MEDIO = colors.HexColor("#1B4F72")
AZUL_CLARO = colors.HexColor("#2E86C1")
CINZA_CLARO = colors.HexColor("#F2F3F4")
VERMELHO = colors.HexColor("#C0392B")
VERDE = colors.HexColor("#1E8449")

titulo_style = ParagraphStyle(
    "Titulo", parent=styles["Title"],
    fontSize=20, textColor=AZUL_ESCURO, alignment=TA_CENTER,
    spaceAfter=4,
)
subtitulo_style = ParagraphStyle(
    "Subtitulo", parent=styles["Normal"],
    fontSize=11, textColor=AZUL_MEDIO, alignment=TA_CENTER,
    spaceAfter=2,
)
h1_style = ParagraphStyle(
    "H1", parent=styles["Heading1"],
    fontSize=13, textColor=AZUL_ESCURO, spaceBefore=14, spaceAfter=4,
    borderPad=2,
)
h2_style = ParagraphStyle(
    "H2", parent=styles["Heading2"],
    fontSize=11, textColor=AZUL_MEDIO, spaceBefore=10, spaceAfter=3,
)
body_style = ParagraphStyle(
    "Body", parent=styles["Normal"],
    fontSize=9.5, leading=14, alignment=TA_JUSTIFY, spaceAfter=6,
)
mono_style = ParagraphStyle(
    "Mono", parent=styles["Code"],
    fontSize=8, leading=12, fontName="Courier", leftIndent=18,
    backColor=CINZA_CLARO, borderPad=6, spaceAfter=8,
)
label_verde = ParagraphStyle(
    "LabelVerde", parent=styles["Normal"],
    fontSize=9, textColor=VERDE, fontName="Helvetica-Bold",
)
label_vermelho = ParagraphStyle(
    "LabelVermelho", parent=styles["Normal"],
    fontSize=9, textColor=VERMELHO, fontName="Helvetica-Bold",
)


def tabela(dados, col_widths=None, header=True):
    t = Table(dados, colWidths=col_widths)
    cmd = [
        ("BACKGROUND", (0, 0), (-1, 0 if header else -1), AZUL_MEDIO),
        ("TEXTCOLOR", (0, 0), (-1, 0 if header else -1), colors.white),
        ("FONTNAME", (0, 0), (-1, 0 if header else -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BDC3C7")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]
    t.setStyle(TableStyle(cmd))
    return t


# ---------------------------------------------------------------------------
# Conteúdo
# ---------------------------------------------------------------------------

def build_pdf(path="Relatorio_Aurora_Siger.pdf"):
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=2.2*cm, rightMargin=2.2*cm,
        topMargin=2.2*cm, bottomMargin=2.2*cm,
    )
    story = []

    # Capa
    story += [
        Spacer(1, 1.5*cm),
        Paragraph("MISSÃO AURORA SIGER", titulo_style),
        Paragraph("Ignition Zero Core — Relatório Técnico", subtitulo_style),
        Paragraph("Sistema de Verificação de Voo Embarcado", subtitulo_style),
        Spacer(1, 0.3*cm),
        HRFlowable(width="100%", thickness=1.5, color=AZUL_CLARO),
        Spacer(1, 0.2*cm),
        Paragraph(
            "Repositório: <link href='https://github.com/henriquepe/aurora-siger' "
            "color='blue'>https://github.com/henriquepe/aurora-siger</link>",
            ParagraphStyle("link", parent=styles["Normal"], fontSize=9, alignment=TA_CENTER)
        ),
        Spacer(1, 1*cm),
    ]

    # 1. Contextualização
    story.append(Paragraph("1. Contextualização da Missão", h1_style))
    story.append(Paragraph(
        "Na Nova Corrida Espacial, liderada por NASA, ESA e SpaceX, a Missão Aurora Siger "
        "estabelece o estado da arte em exploração interplanetária. O atraso de comunicação "
        "Terra–Marte pode atingir <b>22 minutos</b>, tornando inviável qualquer intervenção "
        "humana durante a janela crítica de decolagem. O sistema deve ser <b>determinístico e "
        "autônomo</b>, operando sob a filosofia <b>Fail-Safe</b>: a decolagem só é autorizada "
        "quando todas as condições são nominais simultaneamente (lógica AND).",
        body_style
    ))

    # 2. Matriz de Variáveis
    story.append(Paragraph("2. Matriz de Variáveis Críticas de Telemetria", h1_style))
    story.append(Paragraph(
        "A telemetria transforma grandezas físicas em sinais digitais via Thresholding "
        "(Limiarização). Cada sensor possui faixa nominal definida; qualquer desvio é "
        "convertido em estado lógico de falha (0/False).",
        body_style
    ))
    story.append(tabela([
        ["Variável", "Descrição Técnica", "Tipo", "Faixa Nominal"],
        ["temperatura", "Monitoramento térmico de sistemas críticos", "float (°C)", f"≤ {LIMITE_TEMP_MAX}°C"],
        ["integridade", "Extensômetros e sensores ultrassônicos", "bool (0/1)", "== 1"],
        ["energia", "State of Charge (SoC) das baterias", "% float", f"≥ {ENERGIA_MINIMA}%"],
        ["pressao", "Sensores piezoresistivos nos tanques", "float (PSI)", f"{PRESSAO_MIN} – {PRESSAO_MAX} PSI"],
        ["modulos", "Diagnóstico de prontidão dos módulos", "bool (flag)", "== 1"],
    ], col_widths=[3.2*cm, 6.2*cm, 2.8*cm, 3.6*cm]))
    story.append(Spacer(1, 0.3*cm))

    # 3. Pseudocódigo
    story.append(Paragraph("3. Pseudocódigo Estruturado — AND Gate", h1_style))
    pseudo = (
        "INÍCIO\n"
        "    LER telemetria_bruta\n"
        "    VALIDAR presença e tipo de todos os sensores obrigatórios\n"
        "    SE dados inválidos → ABORTAR com log de erro\n\n"
        "    CONSTANTE LIMITE_TEMP_MAX  = 35.0   // °C\n"
        "    CONSTANTE ENERGIA_MINIMA   = 80.0   // %\n"
        "    CONSTANTE PRESSAO_MIN      = 90.0   // PSI\n"
        "    CONSTANTE PRESSAO_MAX      = 110.0  // PSI\n\n"
        "    // Thresholding: digitalização\n"
        "    temp_ok  ← temperatura  <= LIMITE_TEMP_MAX\n"
        "    integ_ok ← integridade  == 1\n"
        "    ener_ok  ← energia      >= ENERGIA_MINIMA\n"
        "    press_ok ← PRESSAO_MIN <= pressao <= PRESSAO_MAX\n"
        "    mod_ok   ← modulos      == 1\n\n"
        "    SE temp_ok E integ_ok E ener_ok E press_ok E mod_ok ENTÃO\n"
        "        GERAR_LOG \"STATUS: PRONTO PARA DECOLAR\"\n"
        "        CALCULAR autonomia_energetica(energia)\n"
        "        INICIAR SEQUÊNCIA_IGNICAO\n"
        "    SENÃO\n"
        "        GERAR_LOG \"STATUS: DECOLAGEM ABORTADA\"\n"
        "        IDENTIFICAR_ANOMALIA(telemetria, estados)\n"
        "        BLOQUEAR_IGNICAO\n"
        "    FIM SE\n"
        "FIM"
    )
    story.append(Preformatted(pseudo, mono_style))

    # 4. Implementação Python
    story.append(Paragraph("4. Implementação em Python", h1_style))
    story.append(Paragraph(
        "Script modularizado com <b>Type Hinting</b>, sem chamadas interativas (<i>input()</i>). "
        "Os dados são consumidos via dicionários de sensores (streams JSON-compatíveis). "
        "Seis módulos independentes garantem separação de responsabilidades:",
        body_style
    ))
    story.append(tabela([
        ["Módulo", "Responsabilidade"],
        ["validar_entrada()", "Verifica presença e tipo de todos os sensores antes de qualquer lógica"],
        ["digitalizar_sinais()", "Thresholding: converte leituras físicas em estados booleanos"],
        ["identificar_anomalias()", "Log auditável com valor medido, limite e descrição da falha"],
        ["calcular_autonomia()", "Aplica fórmula de autonomia energética operacional"],
        ["validar_sistemas()", "AND Gate central — retorna ResultadoVerificacao completo"],
        ["imprimir_relatorio()", "Saída estruturada estilo caixa-preta (black-box log)"],
    ], col_widths=[5.5*cm, 10.3*cm]))
    story.append(Spacer(1, 0.3*cm))

    # 5. Simulações
    story.append(Paragraph("5. Simulação de Cenários", h1_style))

    # Cenário 1
    story.append(Paragraph("5.1 Cenário Nominal — Decolagem Autorizada", h2_style))
    r1 = validar_sistemas(TELEMETRIA_NOMINAL)
    dados_c1 = [
        ["Sensor", "Valor", "Limite", "Status"],
        ["temperatura", f"{TELEMETRIA_NOMINAL['temperatura']}°C", f"≤ {LIMITE_TEMP_MAX}°C", "NOMINAL"],
        ["integridade", str(int(TELEMETRIA_NOMINAL['integridade'])), "== 1", "NOMINAL"],
        ["energia", f"{TELEMETRIA_NOMINAL['energia']}%", f"≥ {ENERGIA_MINIMA}%", "NOMINAL"],
        ["pressao", f"{TELEMETRIA_NOMINAL['pressao']} PSI", f"{PRESSAO_MIN}–{PRESSAO_MAX} PSI", "NOMINAL"],
        ["modulos", str(int(TELEMETRIA_NOMINAL['modulos'])), "== 1", "NOMINAL"],
    ]
    t_c1 = Table(dados_c1, colWidths=[3.5*cm, 3.5*cm, 4*cm, 4.8*cm])
    cmd_c1 = [
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_MEDIO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ("TEXTCOLOR", (3, 1), (3, -1), VERDE),
        ("FONTNAME", (3, 1), (3, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BDC3C7")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]
    t_c1.setStyle(TableStyle(cmd_c1))
    story.append(t_c1)
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"<b>Resultado:</b> <font color='#1E8449'>PRONTO PARA DECOLAR</font> — "
        f"Autonomia estimada: {r1.autonomia_horas} horas",
        body_style
    ))

    # Cenário 2
    story.append(Paragraph("5.2 Cenário com Falhas — Decolagem Abortada", h2_style))
    r2 = validar_sistemas(TELEMETRIA_FALHA)
    story.append(Paragraph(
        f"<b>Resultado:</b> <font color='#C0392B'>DECOLAGEM ABORTADA</font> — "
        f"{len(r2.anomalias)} anomalia(s) detectada(s):",
        body_style
    ))
    for a in r2.anomalias:
        story.append(Paragraph(f"• {a}", ParagraphStyle(
            "item", parent=styles["Normal"], fontSize=9,
            textColor=VERMELHO, leftIndent=18, spaceAfter=2
        )))
    story.append(Spacer(1, 0.3*cm))

    # 6. Análise Energética
    story.append(Paragraph("6. Análise Energética", h1_style))
    story.append(Paragraph(
        "A fórmula de autonomia operacional quantifica a capacidade de operação autônoma "
        "após a decolagem, considerando o pico de consumo dos motores e as perdas "
        "térmicas de conversão:",
        body_style
    ))
    story.append(Paragraph(
        "<b>Autonomia = ((Capacidade_Total × Carga_Atual) − Consumo_Decolagem) "
        "/ (Capacidade_Total × Perdas_Energéticas)</b>",
        ParagraphStyle("formula", parent=styles["Normal"], fontSize=10,
                       alignment=TA_CENTER, spaceBefore=6, spaceAfter=10,
                       backColor=CINZA_CLARO, borderPad=8)
    ))
    story.append(tabela([
        ["Parâmetro", "Valor", "Descrição"],
        ["Capacidade Total", f"{CAPACIDADE_TOTAL_KWH} kWh", "Potencial nominal das células"],
        ["Carga Atual (SoC)", "variável (%)", "Estado real disponível"],
        ["Consumo na Decolagem", f"{CONSUMO_DECOLAGEM_KWH} kWh", "Pico de demanda dos motores e aviônicos"],
        ["Perdas Energéticas", f"{PERDAS_ENERGETICAS*100:.0f}%", "Eficiência de conversão e dissipação térmica"],
    ], col_widths=[4.5*cm, 3.5*cm, 7.8*cm]))
    story.append(Spacer(1, 0.3*cm))

    cargas = [60, 70, 80, 90, 95, 100]
    rows = [["SoC (%)", "Energia Disponível (kWh)", "Energia Útil (kWh)", "Autonomia (horas)"]]
    for c in cargas:
        disp = CAPACIDADE_TOTAL_KWH * (c / 100.0)
        util = disp - CONSUMO_DECOLAGEM_KWH
        aut = calcular_autonomia(c)
        rows.append([f"{c}%", f"{disp:.1f}", f"{max(util,0):.1f}", f"{aut:.2f}"])
    story.append(tabela(rows, col_widths=[3*cm, 5*cm, 4.5*cm, 4.3*cm]))
    story.append(Spacer(1, 0.3*cm))

    # 7. IA
    story.append(Paragraph("7. Triagem Estratégica Assistida por IA", h1_style))
    story.append(Paragraph(
        "A IA opera como camada analítica <b>probabilística</b>, complementar à lógica "
        "<b>determinística</b> do script Python. A IA <u>não</u> autoriza decolagens — "
        "ela identifica tendências e padrões que algoritmos de regra fixa podem ignorar.",
        body_style
    ))
    story.append(tabela([
        ["Tipo de Análise", "Prompt de IA"],
        ["Classificação de Risco", "\"Classifique estes logs de telemetria bruta em categorias de risco aeroespacial (Nominal, Degradado, Crítico).\""],
        ["Detecção de Anomalias", "\"Analise padrões de micro-vibração nestes dados e identifique correlações com possíveis fadigas estruturais prematuras.\""],
        ["Mitigação Energética", "\"Sugira protocolos de redirecionamento de carga energética caso o módulo de propulsão apresente subpressão.\""],
    ], col_widths=[4*cm, 11.8*cm]))
    story.append(Spacer(1, 0.3*cm))

    # 8. Ética
    story.append(Paragraph("8. Ética, Sustentabilidade e Code Longevity", h1_style))
    story.append(tabela([
        ["Princípio", "Implementação no Projeto"],
        ["Transparência Algorítmica", "Logs auditáveis identificam cada anomalia com valor medido e limite"],
        ["Determinismo", "AND Gate — ausência completa de estados ambíguos"],
        ["Fail-Safe", "Qualquer falha resulta em abortagem (padrão conservador)"],
        ["Footprint Mínimo", "Zero dependências externas — apenas biblioteca padrão Python 3.8+"],
        ["Code Longevity", "Type Hints, dataclasses, docstrings e funções sem efeitos colaterais"],
        ["Sem Input Interativo", "Dados consumidos via dicionários/streams — sem input()"],
    ], col_widths=[5*cm, 10.8*cm]))
    story.append(Spacer(1, 0.3*cm))

    # 9. Repositório
    story.append(Paragraph("9. Repositório e Entregáveis", h1_style))
    story.append(tabela([
        ["Entregável", "Status", "Local"],
        ["aurora_siger.py", "Entregue", "Raiz do repositório"],
        ["aurora_siger.ipynb", "Entregue", "Raiz do repositório"],
        ["README.md", "Entregue", "Raiz do repositório"],
        ["Relatório PDF", "Entregue", "Raiz do repositório"],
        ["Repositório GitHub (Público)", "Entregue", "https://github.com/henriquepe/aurora-siger"],
    ], col_widths=[5*cm, 2.8*cm, 8*cm]))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.8, color=AZUL_CLARO))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Missão Aurora Siger — Ignition Zero Core | FIAP",
        ParagraphStyle("rodape", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    print(f"PDF gerado: {path}")


if __name__ == "__main__":
    build_pdf("Relatorio_Aurora_Siger.pdf")
