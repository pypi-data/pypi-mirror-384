import re
import pandas as pd
from datetime import datetime
from rich.panel import Panel
from rich.text import Text

LANGUAGES = {
    "tr": {
        "browser_minimized": "Tarayıcı küçültüldü! Lütfen kapatmayın. İşlem arka planda devam edecek. Bittiğinde bildirim alacaksınız.",
        "info": "BİLGİ",
        "rows_fetched": "{} satır çekildi.",
        "saved_excel": "Excel dosyasına kaydedildi: {}",
        "all_done": "Tüm işlemler başarıyla tamamlandı.",
        "invalid_fund_type": "Geçersiz fon tipi kodu: '{}'. Geçerli kodlar: {}",
        "invalid_tab_type": "Geçersiz sekme kodu: '{}'. Geçerli kodlar: {}",
        "invalid_date_format": "Geçersiz {} formatı! Doğru format: 'gg.aa.yyyy'",
        "start_date_gt_end": "Başlangıç tarihi, bitiş tarihinden sonra olamaz!",
        "webdriver_version_mismatch": "WebDriver sürüm uyumsuzluğu: {}. Lütfen Chrome veya WebDriver'ı güncellemeyi deneyin.",
        "webdriver_setup_failed": "WebDriver kurulumu başarısız oldu: {}. Lütfen Google Chrome'un kurulu ve WebDriver sürümünüzle uyumlu olduğundan emin olun.",
        "dropdown_error": "Dropdown seçim hatası: {}",
        "processing_date": "{} tarihi işleniyor...",
        "date_skipped": "{} için veri yok, atlandı.",
        "date_done": "{} tamamlandı.",
    },
    "en": {
        "browser_minimized": "Browser minimized! Please do not close it. The process will continue in the background. You will get a notification when it finishes.",
        "info": "INFO",
        "rows_fetched": "{} rows fetched.",
        "saved_excel": "Saved to Excel file: {}",
        "all_done": "All operations completed successfully.",
        "invalid_fund_type": "Invalid fund type code: '{}'. Valid codes: {}",
        "invalid_tab_type": "Invalid tab code: '{}'. Valid codes: {}",
        "invalid_date_format": "Invalid {} format! Correct format: 'dd.mm.yyyy'",
        "start_date_gt_end": "Start date cannot be after end date!",
        "webdriver_version_mismatch": "WebDriver version mismatch: {}. Please try updating Chrome or WebDriver.",
        "webdriver_setup_failed": "WebDriver setup failed: {}. Please ensure Google Chrome is installed and compatible with the WebDriver version.",
        "dropdown_error": "Dropdown selection error: {}",
        "processing_date": "Processing date {}...",
        "date_skipped": "No data for {}, skipped.",
        "date_done": "{} completed.",
    }
}

FUND_TYPE_CODES = {
    0: "securities_mutuals",
    1: "pension",
    2: "exchange_traded",
    3: "real_estate_investment",
    4: "venture_capital_investment"
}
FUND_TYPE_LABELS = {v: k for k, v in FUND_TYPE_CODES.items()}

TAB_CODES = {
    0: "general_information",
    1: "portfolio_breakdown"
}
TAB_LABELS = {v: k for k, v in TAB_CODES.items()}

def get_localized_message(key, lang, *args):
    template = LANGUAGES.get(lang, LANGUAGES["en"]).get(key, key)
    return template.format(*args) if args else template

def parse_and_validate_dates(start_date_str, end_date_str, lang):
    try:
        start_date = datetime.strptime(start_date_str, "%d.%m.%Y")
    except Exception:
        raise ValueError(get_localized_message("invalid_date_format", lang, "start date"))
    try:
        end_date = datetime.strptime(end_date_str, "%d.%m.%Y")
    except Exception:
        raise ValueError(get_localized_message("invalid_date_format", lang, "end date"))
    if start_date > end_date:
        raise ValueError(get_localized_message("start_date_gt_end", lang))
    return start_date, end_date

def print_rich_panel(console, message, lang, style="bold yellow", title_key="info", border_style="bright_magenta"):
    panel = Panel(
        Text(message, style=style, justify="center"),
        title=f"[cyan]{get_localized_message(title_key, lang)}",
        border_style=border_style
    )
    console.print(panel)

def fix_date(val):
    s = str(val).strip()

    if s == "" or s.lower() in {"nan", "none"}:
        return pd.NaT

    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", s):
        return s

    m = re.fullmatch(r"(\d{1,2})[./](\d{1,2})[./](\d{2,4})", s)
    if m:
        d, mo, y = m.groups()
        d, mo = int(d), int(mo)
        y = int(y) if len(y) == 4 else int(f"20{int(y):02d}")
        return f"{d:02d}.{mo:02d}.{y:04d}"

    if s.isdigit() and 5 <= len(s) <= 8:
        s = s.zfill(8)
        return f"{s[:2]}.{s[2:4]}.{s[4:]}"

    try:
        n = int(float(s))
        s = str(n).zfill(8)
        if len(s) == 8:
            return f"{s[:2]}.{s[2:4]}.{s[4:]}"
    except Exception:
        pass

    return s