import io
import datetime
import logging
import os

logger = logging.getLogger(__name__)

# --- Safe imports: сервер стартує навіть якщо бібліотеки відсутні ---
_MISSING_LIBS = []

try:
    import qrcode
except ImportError:
    qrcode = None
    _MISSING_LIBS.append("qrcode")

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table,
        TableStyle, PageBreak, Image, KeepTogether
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.units import mm, cm
except ImportError:
    _MISSING_LIBS.append("reportlab")

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    plt = None
    np = None
    _MISSING_LIBS.append("matplotlib/numpy")

if _MISSING_LIBS:
    logger.warning(
        "PDF generation libraries missing: %s. "
        "Run: pip install qrcode[pil] reportlab matplotlib numpy",
        ", ".join(_MISSING_LIBS)
    )

# Налаштування шрифтів
font_regular = 'Helvetica'
font_bold = 'Helvetica-Bold'

def register_fonts():
    global font_regular, font_bold
    font_paths = [
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "arial.ttf"
    ]
    font_bold_paths = [
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\tahomabd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "arialbd.ttf"
    ]
    
    registered_reg = False
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('CyrillicFont', path))
                font_regular = 'CyrillicFont'
                registered_reg = True
                logger.info(f"Registered regular Cyrillic font: {path}")
                break
            except Exception as e:
                pass
                
    for path in font_bold_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('CyrillicFont-Bold', path))
                font_bold = 'CyrillicFont-Bold'
                logger.info(f"Registered bold Cyrillic font: {path}")
                break
            except Exception as e:
                pass

register_fonts()

# Кольори (жовтий, чорний, смарагдовий)
LEGO_YELLOW = colors.HexColor("#facc15")
LEGO_BLACK = colors.HexColor("#0f172a")
LEGO_EMERALD = colors.HexColor("#059669")
LEGO_GRAY = colors.HexColor("#f1f5f9")
LEGO_DARK_GRAY = colors.HexColor("#475569")

def create_radar_chart(characteristics: dict) -> io.BytesIO:
    label_map = {
        "speed": "Швидкість", "force": "Сила", "economy": "Економність", "endurance": "Витривалість", "eco": "Еко"
    }
    
    labels = [label_map.get(k.lower(), k.capitalize()) for k in characteristics.keys()]
    values = list(characteristics.values())
    values = [float(v) for v in values]
    
    num_vars = len(labels)
    if num_vars < 3:
        return None

    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]
    
    try:
        # Шрифти з підтримкою кирилиці для matplotlib
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Tahoma']
        fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor('none')
        ax.set_facecolor('#f8fafc')
        ax.fill(angles, values, color='#059669', alpha=0.3)
        ax.plot(angles, values, color='#059669', linewidth=2.5)
        
        ax.set_yticklabels([])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, size=9, color='#0f172a', weight='bold')
        ax.spines['polar'].set_color('#94a3b8')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=150)
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception as e:
        logger.error(f"Radar chart error: {e}")
        return None

def create_qr_code(config_id) -> io.BytesIO:
    try:
        url = f"http://localhost:5173/history?id={config_id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0f172a", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf
    except Exception as e:
        logger.error(f"QR code error: {e}")
        return None

def generate_robot_passport(config_data: dict) -> bytes:
    buffer = io.BytesIO()
    
    if _MISSING_LIBS:
        raise RuntimeError(
            f"Неможливо згенерувати PDF — відсутні бібліотеки: {', '.join(_MISSING_LIBS)}. "
            f"Активуйте venv та виконайте: pip install qrcode[pil] reportlab matplotlib numpy"
        )
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=15*mm, 
        leftMargin=15*mm, 
        topMargin=35*mm, 
        bottomMargin=25*mm
    )
    
    req_data = config_data.get("request", {})
    res_data = config_data.get("result", {})
    config_id = config_data.get("id", "N/A")
    timestamp = config_data.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    algorithm_name = "Генетичний Алгоритм" if config_data.get('algorithm') == 'genetic' else "Жадібний Алгоритм"
    
    # Шапка та підвал сторінки
    def header_footer(canvas, doc):
        canvas.saveState()
        
        # Фонова сітка
        canvas.setStrokeColor(colors.HexColor("#e2e8f0"))
        canvas.setLineWidth(0.5)
        for i in range(0, int(A4[0]), 10):
            canvas.line(i, 0, i, A4[1])
        for i in range(0, int(A4[1]), 10):
            canvas.line(0, i, A4[0], i)
            
        # Блок заголовка
        canvas.setFillColor(LEGO_YELLOW)
        canvas.rect(15*mm, A4[1] - 25*mm, A4[0] - 30*mm, 15*mm, fill=1, stroke=0)
        
        # Малюємо просту іконку LEGO-цеглини з прямокутників
        canvas.setFillColor(LEGO_BLACK)
        # Тіло цеглини
        canvas.rect(18*mm, A4[1] - 20*mm, 12*mm, 6*mm, fill=1, stroke=0)
        # Шипи (studs)
        canvas.rect(19*mm, A4[1] - 14*mm, 2*mm, 1.5*mm, fill=1, stroke=0)
        canvas.rect(23*mm, A4[1] - 14*mm, 2*mm, 1.5*mm, fill=1, stroke=0)
        canvas.rect(27*mm, A4[1] - 14*mm, 2*mm, 1.5*mm, fill=1, stroke=0)
        
        canvas.setFont(font_bold, 14)
        canvas.drawString(33*mm, A4[1] - 16*mm, "LegoConfigurator")
        
        canvas.setFont(font_regular, 10)
        canvas.drawRightString(A4[0] - 20*mm, A4[1] - 14*mm, f"ID: {config_id}")
        canvas.drawRightString(A4[0] - 20*mm, A4[1] - 18*mm, f"Дата: {timestamp[:10]}")
        canvas.drawRightString(A4[0] - 20*mm, A4[1] - 22*mm, f"Режим: {algorithm_name}")
        
        canvas.setFont(font_bold, 12)
        canvas.drawString(33*mm, A4[1] - 22*mm, "Технічна Специфікація")
        
        # Блок підвалу
        canvas.setFillColor(LEGO_GRAY)
        canvas.rect(15*mm, 10*mm, A4[0] - 30*mm, 10*mm, fill=1, stroke=0)
        
        canvas.setFillColor(LEGO_DARK_GRAY)
        canvas.setFont(font_regular, 9)
        canvas.drawString(20*mm, 13*mm, "Згенеровано системою LegoConfigurator")
        canvas.drawRightString(A4[0] - 20*mm, 13*mm, f"Сторінка {doc.page}")
        
        canvas.restoreState()

    styles = getSampleStyleSheet()
    
    h1_style = ParagraphStyle(
        'CustomH1', parent=styles['Heading1'], fontName=font_bold, fontSize=14,
        textColor=LEGO_BLACK, spaceBefore=15, spaceAfter=10, 
        borderPadding=5, backColor=LEGO_YELLOW
    )
    normal_style = ParagraphStyle(
        'CustomNormal', parent=styles['Normal'], fontName=font_regular, fontSize=10,
        textColor=LEGO_BLACK, spaceAfter=6, leading=14
    )
    bold_style = ParagraphStyle(
        'CustomBold', parent=styles['Normal'], fontName=font_bold, fontSize=10,
        textColor=LEGO_BLACK, spaceAfter=6
    )
    tips_style = ParagraphStyle(
        'TipsStyle', parent=styles['Normal'], fontName=font_regular, fontSize=10,
        textColor=LEGO_BLACK, spaceBefore=5, spaceAfter=5, leftIndent=10, rightIndent=10,
        backColor=LEGO_GRAY, borderPadding=8, borderRadius=5, borderColor=LEGO_EMERALD, borderWidth=1
    )

    story = []
    
    # 1. Загальний огляд конфігурації
    story.append(Paragraph("1. Аналітичне резюме", h1_style))
    
    ga_stats = res_data.get("ga_stats", {})
    fitness_score = ga_stats.get('final_fitness', 'N/A') if config_data.get('algorithm') == 'genetic' else 'N/A'
    total_price = config_data.get('total_price', 0)
    total_weight = config_data.get('total_weight', 0)
    
    summary_data = [
        ["Критерій", "Значення"],
        ["Підсумковий Fitness Score", str(fitness_score)],
        ["Загальна вартість", f"{total_price:.2f} грн"],
        ["Фінальна вага", f"{total_weight:.1f} г"],
        ["Залишок бюджету", f"{config_data.get('remaining_budget', 0):.2f} грн"]
    ]
    t_summary = Table(summary_data, colWidths=[80*mm, 50*mm])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), LEGO_BLACK),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('FONTNAME', (0, 1), (-1, -1), font_regular),
        ('BACKGROUND', (0, 1), (-1, -1), LEGO_GRAY),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    
    weights = req_data.get("weights", {})
    chart_img = None
    if weights:
        chart_buf = create_radar_chart(weights)
        if chart_buf:
            chart_img = Image(chart_buf, width=60*mm, height=60*mm)
            
    if chart_img:
        chart_table = Table([[t_summary, chart_img]], colWidths=[130*mm, 50*mm])
        chart_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        story.append(chart_table)
    else:
        story.append(t_summary)
        
    story.append(Spacer(1, 10))
    
    terrain = req_data.get("terrain", "indoor")
    terrain_map = {"indoor": "приміщень", "outdoor_flat": "вулиці (рівне покриття)", "offroad": "бездоріжжя", "water_pool": "водойм"}
    terrain_ua = terrain_map.get(terrain, "вказаних умов")
    
    priority = req_data.get("powerProfile", "balanced")
    priority_ua = {"long_runtime": "максимальної автономності", "balanced": "балансу характеристик", "performance": "максимальної потужності"}.get(priority, "оптимальної роботи")
    
    func_list = req_data.get("functions", [])
    sub_funcs = req_data.get("subFunctions", {})
    func_parts = []
    func_labels = {"їздити": "Їздити", "літати": "Літати", "плавати": "Плавати", "маніпулювати": "Маніпулювати", "сканувати": "Сканувати"}
    for f in func_list:
        label = func_labels.get(f, f)
        sub = sub_funcs.get(f, "")
        func_parts.append(f"{label} ({sub})" if sub else label)
    func_str = ", ".join(func_parts) if func_parts else "не визначено"
    
    verdict = (
        f"<b>Системний аналіз:</b> Конфігурація для функцій: {func_str}. "
        f"Оптимізація спрямована на {priority_ua}. "
        f"Призначена для умов {terrain_ua}. "
        f"Підібрані деталі відповідають заданим обмеженням бюджету ({req_data.get('budget', 'N/A')} грн) та маси ({req_data.get('weight', 'N/A')} г)."
    )
    story.append(Paragraph(verdict, tips_style))
    story.append(Spacer(1, 10))
    
    # 2. BOM
    story.append(Paragraph("2. Специфікація деталей (BOM)", h1_style))
    
    components = res_data.get("selected", [])
    comp_map = {}
    for c in components:
        c_id = c.get("id")
        if c_id in comp_map:
            comp_map[c_id]["qty"] += 1
        else:
            comp_map[c_id] = {
                "name": c.get("name", ""),
                "art": c.get("lego_number", "N/A"),
                "qty": 1,
                "cat": c.get("category", ""),
                "price": c.get("price", 0),
                "param": f"{c.get('weight', 0)}g"
            }
            
    bom_data = [["Назва", "Артикул", "К-ть", "Ціна шт.", "Параметр"]]
    for item in comp_map.values():
        bom_data.append([
            Paragraph(item["name"], ParagraphStyle('s', fontName=font_regular, fontSize=8)),
            str(item["art"]),
            str(item["qty"]),
            f"{item['price']} ₴",
            item["param"]
        ])
        
    t_bom = Table(bom_data, colWidths=[70*mm, 25*mm, 15*mm, 30*mm, 30*mm])
    t_bom.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), LEGO_BLACK),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), font_regular),
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('GRID', (0, 0), (-1, -1), 0.5, LEGO_DARK_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LEGO_GRAY]),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_bom)
    
    story.append(PageBreak())
    
    # 3. Схема підключень
    story.append(Paragraph("3. Мапа технічних з'єднань (Connection Map)", h1_style))
    story.append(Paragraph("Схема портів Хабу:", bold_style))
    
    ports = ["A", "B", "C", "D", "E", "F"]
    port_idx = 0
    connections = []
    total_power = 0
    
    for item in comp_map.values():
        cat = item["cat"].lower()
        if cat in ["motor", "sensor"]:
            for i in range(item["qty"]):
                if port_idx < len(ports):
                    func_guess = "Рух / Привід" if "motor" in cat else "Зчитування даних"
                    connections.append([f"Порт {ports[port_idx]}", Paragraph(item['name'], normal_style), func_guess])
                    port_idx += 1
                    if "motor" in cat: total_power += 1
    
    if connections:
        conn_table = Table([["Порт", "Деталь", "Функція"]] + connections, colWidths=[20*mm, 90*mm, 60*mm])
        conn_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), LEGO_EMERALD),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), font_regular),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('GRID', (0, 0), (-1, -1), 0.5, LEGO_DARK_GRAY),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(conn_table)
    else:
        story.append(Paragraph("Активних електронних компонентів для підключення не знайдено.", normal_style))
    
    story.append(Spacer(1, 10))
    power_warning = "Нормальне навантаження. Хаб працює в безпечних межах."
    if total_power > 3:
        power_warning = "УВАГА: Високе енергоспоживання (>3 моторів). Забезпечте повний заряд батареї Хабу для максимальної продуктивності."
    story.append(Paragraph(f"<b>Перевірка Живлення:</b> {power_warning}", tips_style))
    
    story.append(Spacer(1, 15))

    # 4. Логіка складання
    story.append(Paragraph("4. Логіка Збірки", h1_style))
    
    # Аналіз функцій з запиту (українські ID: їздити, літати, плавати, маніпулювати, сканувати)
    req_functions = req_data.get("functions", [])
    if isinstance(req_functions, str):
        req_functions = [req_functions]
    sub_functions = req_data.get("subFunctions", {})
    sensors = req_data.get("sensors", [])
    size_class = req_data.get("sizeClass", "medium")
    size_ua = {"small": "малий", "medium": "середній", "large": "великий"}.get(size_class, "середній")
    
    has_drive = "їздити" in req_functions
    has_fly = "літати" in req_functions
    has_swim = "плавати" in req_functions
    has_manipulate = "маніпулювати" in req_functions
    has_scan = "сканувати" in req_functions
    
    drive_sub = sub_functions.get("їздити", "")
    fly_sub = sub_functions.get("літати", "")
    swim_sub = sub_functions.get("плавати", "")
    manip_sub = sub_functions.get("маніпулювати", "")
    
    step_num = 1
    steps = [
        f"<b>Етап {step_num}: Базова Структура.</b> Почніть із найбільшої структурної деталі. Розмір робота: {size_ua}. Це забезпечить необхідну жорсткість рами."
    ]
    
    if has_drive:
        step_num += 1
        if drive_sub == "Гусениці":
            steps.append(f"<b>Етап {step_num}: Привід (Гусениці).</b> Встановіть гусеничні стрічки симетрично. Переконайтеся, що натяг стрічки однаковий з обох боків.")
        else:
            steps.append(f"<b>Етап {step_num}: Привід (Колеса).</b> Закріпіть мотори симетрично до рами. Переконайтеся у співвісності осей та надійності кріплення коліс.")
    if has_fly:
        step_num += 1
        if fly_sub == "Квадрокоптер":
            steps.append(f"<b>Етап {step_num}: Льотна система (Квадрокоптер).</b> Розмістіть 4 мотори з пропелерами на рівній відстані від центру. Хаб має бути строго по центру для стабільного центру мас.")
        elif fly_sub == "Вертоліт":
            steps.append(f"<b>Етап {step_num}: Льотна система (Вертоліт).</b> Закріпіть головний ротор зверху та хвостовий стабілізатор. Перевірте баланс лопатей.")
        else:
            steps.append(f"<b>Етап {step_num}: Льотна система (Літак).</b> Встановіть крила симетрично та закріпіть тяговий мотор. Центр мас має бути попереду аеродинамічного центру.")
    if has_swim:
        step_num += 1
        if swim_sub == "Водомет":
            steps.append(f"<b>Етап {step_num}: Водна система (Водомет).</b> Встановіть водометний привід у кормовій частині. Забезпечте герметичність електричних з'єднань.")
        elif swim_sub == "Плавники":
            steps.append(f"<b>Етап {step_num}: Водна система (Плавники).</b> Закріпіть біомеханічні плавники з достатнім ходом сервоприводів.")
        else:
            steps.append(f"<b>Етап {step_num}: Водна система (Гребні гвинти).</b> Встановіть гвинти симетрично. Ізолюйте електроніку від води.")
    if has_manipulate:
        step_num += 1
        if manip_sub == "Біонічна рука":
            steps.append(f"<b>Етап {step_num}: Маніпулятор (Біонічна рука).</b> Зберіть ланки руки послідовно. Відкалібруйте кожен сервопривід окремо.")
        elif manip_sub == "Лінійний актуатор":
            steps.append(f"<b>Етап {step_num}: Маніпулятор (Лінійний актуатор).</b> Закріпіть актуатор жорстко до рами. Перевірте повний хід штоку.")
        else:
            steps.append(f"<b>Етап {step_num}: Маніпулятор (Клішня).</b> Зберіть захват та відкалібруйте нульове положення. Перевірте механічний люфт у шарнірах.")
    if has_scan or sensors:
        step_num += 1
        sensor_list = ", ".join(sensors[:3]) if sensors else "обрані сенсори"
        steps.append(f"<b>Етап {step_num}: Сенсорика.</b> Встановіть {sensor_list}. Підключіть кабелі до вільних портів Хабу.")
    
    step_num += 1
    steps.append(f"<b>Етап {step_num}: Фінальне з'єднання.</b> Встановіть Хаб у центрі конструкції, підключіть усі кабелі та закріпіть вільну проводку.")
    
    for step in steps:
        story.append(Paragraph(step, normal_style))
        
    story.append(Spacer(1, 15))
    
    # 5. Технічні рекомендації
    story.append(Paragraph("5. Технічні Рекомендації", h1_style))
    notes = []
    
    # Перевірка маси
    if total_weight > 700:
        notes.append("<b>Маса конструкції:</b> Виявлено високу вагу (>700г). Рекомендується посилити вертикальні з'єднання та використати додаткові балки.")
    elif total_weight > 400:
        notes.append("<b>Маса конструкції:</b> Середня вага. Конструкція збалансована.")
    else:
        notes.append("<b>Маса конструкції:</b> Легка конструкція. Оптимально для швидкісних завдань.")
    
    # Перевірка живлення
    if total_power > 3:
        notes.append("<b>Живлення:</b> Використано багато моторів. Забезпечте повний заряд батареї Хабу перед запуском.")
    
    # Рекомендації по середовищу
    terrain = req_data.get("terrain", "indoor")
    if terrain == "offroad":
        notes.append("<b>Середовище (Off-road):</b> Для нерівних поверхонь рекомендується збільшити кліренс та використати м'які шини.")
    elif terrain == "water_pool":
        notes.append("<b>Середовище (Водойма):</b> Обов'язково ізолюйте всі електричні з'єднання. Перевірте герметичність корпусу.")
    elif terrain == "outdoor_flat":
        notes.append("<b>Середовище (Вулиця):</b> Захистіть сенсори від пилу та бруду.")
    
    # Рекомендації по функціях
    if has_fly and has_drive:
        notes.append("<b>Комбінована конструкція:</b> Робот поєднує їзду та політ. Переконайтеся, що перехід між режимами не створює механічних конфліктів.")
    if has_swim:
        notes.append("<b>Водний режим:</b> Після кожного використання у воді просушіть конструкцію та перевірте з'єднання на корозію.")
    if has_manipulate and has_drive:
        notes.append("<b>Мобільний маніпулятор:</b> При русі з піднятим маніпулятором центр мас зміщується. Рухайтеся повільно.")
    
    # Складність
    complexity_level = req_data.get("complexityLevel", req_data.get("complexity", 2))
    total_qty = sum(item["qty"] for item in comp_map.values())
    if complexity_level >= 4 or total_qty > 15:
        notes.append("<b>Складність:</b> Високий рівень складності. Ретельно перевірте прокладання кабелів та структурну цілісність.")
    
    # Сенсори
    if sensors:
        notes.append(f"<b>Сенсорика:</b> Обрано {len(sensors)} сенсор(ів). Переконайтеся, що кожен підключений до окремого порту Хабу.")
    
    # Еко-режим
    eco_mode = req_data.get("eco_mode", False)
    if eco_mode:
        notes.append("<b>Еко-режим:</b> Активовано. Система оптимізувала підбір для мінімального енергоспоживання.")
    
    for note in notes:
        story.append(Paragraph(note, tips_style))
        story.append(Spacer(1, 5))

    # 6. Параметри запиту
    story.append(Paragraph("6. Параметри Конфігурації", h1_style))
    
    func_labels = {"їздити": "Їздити", "літати": "Літати", "плавати": "Плавати", "маніпулювати": "Маніпулювати", "сканувати": "Сканувати"}
    func_str = ", ".join([func_labels.get(f, f) for f in req_functions]) if req_functions else "Не вказано"
    
    sub_str_parts = []
    for func_id, sub in sub_functions.items():
        sub_str_parts.append(f"{func_labels.get(func_id, func_id)}: {sub}")
    sub_str = "; ".join(sub_str_parts) if sub_str_parts else "—"
    
    terrain_map = {"indoor": "Приміщення", "outdoor_flat": "Вулиця (рівно)", "offroad": "Off-road", "water_pool": "Водойма"}
    power_map = {"long_runtime": "Тривала робота", "balanced": "Збалансований", "performance": "Максимальна потужність"}
    
    params_data = [
        ["Параметр", "Значення"],
        ["Функції", func_str],
        ["Підтипи", sub_str],
        ["Середовище", terrain_map.get(terrain, terrain)],
        ["Розмір", size_ua.capitalize()],
        ["Бюджет", f"{req_data.get('budget', 'N/A')} грн"],
        ["Макс. вага", f"{req_data.get('weight', 'N/A')} г"],
        ["Профіль живлення", power_map.get(req_data.get("powerProfile", ""), "—")],
        ["Сенсори", ", ".join(sensors) if sensors else "Не обрано"],
    ]
    
    t_params = Table(params_data, colWidths=[60*mm, 110*mm])
    t_params.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), LEGO_EMERALD),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), font_bold),
        ('FONTNAME', (0, 1), (-1, -1), font_regular),
        ('GRID', (0, 0), (-1, -1), 0.5, LEGO_DARK_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LEGO_GRAY]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_params)

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
