from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import ElementClickInterceptedException
import time
import pandas as pd
from datetime import timedelta
from io import StringIO
from rich.console import Console

from .setup_webdriver import setup_webdriver
from .utils import (
    FUND_TYPE_CODES,
    TAB_CODES,
    get_localized_message,
    parse_and_validate_dates,
    print_rich_panel,
    fix_date
)

def fetch_tefas_data(
    fund_type_code: int,
    tab_code: int,
    start_date: str,
    end_date: str,
    fund_codes: list = None,
    fund_title_contains: list = None,
    lang: str = "tr",
    save_to_excel: bool = False,
    wait_seconds: int = 3
) -> pd.DataFrame:
    console = Console()

    if fund_type_code not in FUND_TYPE_CODES:
        raise ValueError(get_localized_message("invalid_fund_type", lang, fund_type_code, list(FUND_TYPE_CODES.keys())))
    if tab_code not in TAB_CODES:
        raise ValueError(get_localized_message("invalid_tab_type", lang, tab_code, list(TAB_CODES.keys())))

    fund_type_label = FUND_TYPE_CODES[fund_type_code]
    tab_label = TAB_CODES[tab_code]

    start_date_dt, end_date_dt = parse_and_validate_dates(start_date, end_date, lang)
    start_date_filename = start_date_dt.strftime("%Y%m%d")
    end_date_filename = end_date_dt.strftime("%Y%m%d")
    excel_filename = f"tefas_{fund_type_label}_{tab_label}_{start_date_filename}_{end_date_filename}.xlsx"

    driver = setup_webdriver(lang)
    driver.maximize_window()
    driver.get("https://www.tefas.gov.tr/TarihselVeriler.aspx")
    time.sleep(wait_seconds)
    driver.minimize_window()
    print_rich_panel(console, get_localized_message("browser_minimized", lang), lang)
    time.sleep(wait_seconds)

    tab_dropdown_table_map = {
        "general_information": {
            "tab_button_id": "ui-id-1",
            "table_id": "table_general_info",
            "next_button_id": "table_general_info_next",
            "dropdown_name": "table_general_info_length"
        },
        "portfolio_breakdown": {
            "tab_button_id": "ui-id-2",
            "table_id": "table_allocation",
            "next_button_id": "table_allocation_next",
            "dropdown_name": "table_allocation_length"
        }
    }
    tab_params = tab_dropdown_table_map[tab_label]

    tab_button = driver.find_element(By.ID, tab_params["tab_button_id"])
    tab_button.click()
    time.sleep(wait_seconds)

    all_rows = []
    columns = None
    current_date = start_date_dt

    while current_date <= end_date_dt:
        date_str = current_date.strftime("%d.%m.%Y")

        print_rich_panel(
            console,
            get_localized_message("processing_date", lang, date_str),
            lang,
            style="bold yellow"
        )

        start_date_input = driver.find_element(By.ID, "TextBoxStartDate")
        start_date_input.clear()
        start_date_input.send_keys(date_str)
        end_date_input = driver.find_element(By.ID, "TextBoxEndDate")
        end_date_input.clear()
        end_date_input.send_keys(date_str)
        view_button = driver.find_element(By.ID, "ButtonSearchDates")
        view_button.click()
        time.sleep(wait_seconds)

        table_element = driver.find_element(By.ID, tab_params["table_id"])
        table_html = table_element.get_attribute("outerHTML")
        if ("dataTables_empty" in table_html) or ("Tabloda herhangi bir veri mevcut değil" in table_html):
            print_rich_panel(
                console,
                get_localized_message("date_skipped", lang, date_str),
                lang,
                style="magenta"
            )
            current_date += timedelta(days=1)
            continue

        try:
            select_element = driver.find_element(By.NAME, tab_params["dropdown_name"])
            select_box = Select(select_element)
            max_option = max(int(option.text) for option in select_box.options if option.text.isdigit())
            select_box.select_by_visible_text(str(max_option))
            time.sleep(wait_seconds)
        except Exception as e:
            print(get_localized_message("dropdown_error", lang, e))

        while True:
            table_element = driver.find_element(By.ID, tab_params["table_id"])
            table_html = table_element.get_attribute("outerHTML")
            page_df = pd.read_html(StringIO(table_html), decimal=',', thousands='.')[0]

            if "Tarih" in page_df.columns:
                page_df["Tarih"] = page_df["Tarih"].apply(fix_date)

            if columns is None:
                columns = page_df.columns.tolist()

            all_rows.extend(page_df.values.tolist())

            try:
                next_button = driver.find_element(By.ID, tab_params["next_button_id"])
            except Exception:
                break

            if "disabled" in next_button.get_attribute("class"):
                break
            if not (next_button.is_displayed() and next_button.is_enabled()):
                break

            try:
                next_button.click()
                time.sleep(wait_seconds)
            except ElementClickInterceptedException:
                break

        print_rich_panel(
            console,
            get_localized_message("date_done", lang, date_str),
            lang,
            style="green"
        )
        current_date += timedelta(days=1)

    if not all_rows or columns is None:
        final_df = pd.DataFrame()
    else:
        final_df = pd.DataFrame(all_rows, columns=columns)

    if fund_codes and not final_df.empty:
        possible_cols = [c for c in final_df.columns if ("fon kodu" in c.lower())]
        if possible_cols:
            fund_col = possible_cols[0]
            final_df = final_df[final_df[fund_col].isin(fund_codes)]

    if fund_title_contains and not final_df.empty:
        possible_title_cols = [c for c in final_df.columns if ("fon adı" in c.lower()) or ("fon adi" in c.lower())]
        if possible_title_cols:
            title_col = possible_title_cols[0]
            mask = pd.Series(False, index=final_df.index)
            for term in fund_title_contains:
                term = (str(term) if term is not None else "").strip()
                if term:
                    mask |= final_df[title_col].astype(str).str.contains(term, case=False, regex=False, na=False)
            final_df = final_df[mask]

    print_rich_panel(console, get_localized_message("rows_fetched", lang, final_df.shape[0]), lang, style="green")

    if save_to_excel and not final_df.empty:
        final_df.to_excel(excel_filename, index=False)
        print_rich_panel(console, get_localized_message("saved_excel", lang, excel_filename), lang, style="bold cyan")

    print_rich_panel(console, get_localized_message("all_done", lang), lang, style="bold green")
    driver.quit()
    return final_df