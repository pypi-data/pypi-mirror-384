# tefasfon v0.3.0

## Türkçe tercih edenler için:

***Those who prefer English can scroll down the page.***

## Açıklama

`tefasfon`, Türkiye Elektronik Fon Alım Satım Platformu'nun (TEFAS) resmi web sitesinde yayımlanan yatırım fonu ve emeklilik fonu verilerini programatik olarak çekmenizi sağlayan bir Python kütüphanesidir. Kütüphane, fon türü ve tarih aralığı seçimiyle esnek veri çekimi sunar. Mesajlar ve hata bildirimleri Türkçe/İngilizce desteklidir; çıktı doğrudan kullanıma hazır pandas DataFrame olarak döner ve isteğe bağlı olarak Excel dosyasına kaydedilebilir.

## Özellikler

* İstenilen tarih aralığında ve fon türüne göre TEFAS verilerini hızlıca çekebilirsiniz.
* Fon bilgisi veya portföy dağılımı (iki farklı sekme) için veri alabilirsiniz.
* Mesajlar ve hata uyarıları Türkçe/İngilizce gösterilir.
* Kolay kullanım, çıktı olarak doğrudan `pandas.DataFrame` döner.
* Çekilen verileri opsiyonel olarak Excel dosyasına kaydedebilirsiniz.
* Selenium ile gerçek tarayıcı üzerinden veriler alınır, böylece web arayüzündeki tüm güncel verilere ulaşabilirsiniz.

## Kurulum

Kütüphaneyi yüklemek için şu adımları izleyin:

1. Python'ı yükleyin: https://www.python.org/downloads/
2. Terminal veya komut istemcisinde aşağıdaki komutu çalıştırın:

```bash
pip install tefasfon
```

Belirli bir versiyonu yüklemek için:

```bash
pip install tefasfon==0.3.0
```

Yüklü versiyonu görüntülemek için:

```bash
pip show tefasfon
```

## Fonksiyonlar

### `fetch_tefas_data`

TEFAS web sitesinden fon veya portföy verisi çeker.

Parametreler:

* `fund_type_code` (int): Fon tipi kodu
  * 0: Menkul Kıymet Yatırım Fonları
  * 1: Emeklilik Fonları
  * 2: Borsa Yatırım Fonları
  * 3: Gayrimenkul Yatırım Fonları
  * 4: Girişim Sermayesi Yatırım Fonları
* `tab_code` (int): Sekme kodu
  * 0: Genel Bilgiler
  * 1: Portföy Dağılımı
* `start_date` (str): Başlangıç tarihi, 'gg.aa.yyyy' formatında (örn. '17.07.2025')
* `end_date` (str): Bitiş tarihi, 'gg.aa.yyyy' formatında (örn. '18.07.2025')
* `fund_codes` (list | None): "Fon Kodu" sütununda tam eşleşme için kod listesi (opsiyonel)
* `fund_title_contains` (list | None): "Fon Adı" sütununda kısmi arama için terim listesi (opsiyonel)
* `lang` (str): "tr" veya "en" (varsayılan "tr")
* `save_to_excel` (bool): True verilirse, Excel dosyasına kaydeder (varsayılan: False)
* `wait_seconds` (int): Web işlemleri arası bekleme süresi (varsayılan: 3)

Dönüş:

* `pandas.DataFrame` (veya veri yoksa boş DataFrame)

## Örnek Kullanım

```python
from tefasfon import fetch_tefas_data

df = fetch_tefas_data(
    fund_type_code=0,
    tab_code=0,
    start_date="17.08.2025",
    end_date="18.07.2025",
    lang="tr",
    save_to_excel=True
)

df_codes = fetch_tefas_data(
    fund_type_code=0,
    tab_code=0,
    start_date="17.07.2025",
    end_date="18.07.2025",
    fund_codes=["ABC", "XYZ"], # Fon kodu değerleri
    lang="tr",
    save_to_excel=False
)

df_title = fetch_tefas_data(
    fund_type_code=0,
    tab_code=0,
    start_date="17.07.2025",
    end_date="18.07.2025",
    fund_title_contains=["Altın", "Teknoloji"], # Ünvan içinde geçen terimler
    lang="tr",
    save_to_excel=False
)
```

## Notlar

* Kütüphane, TEFAS'ın web sitesindeki verilere bağımlıdır. Herhangi bir değişiklikte veya bakımda, veri çekilemeyebilir. Lütfen [TEFAS](https://www.tefas.gov.tr/TarihselVeriler.aspx) adresinden veri durumu ve güncelliğini kontrol edin.
* Selenium ve ChromeDriver kullanılır. Bilgisayarınızda Google Chrome kurulu olmalı ve güncel olmalıdır.
* Kütüphanenin geliştirilmesi ve iyileştirilmesi için geri bildirimlerinizi bekliyorum. GitHub reposuna katkıda bulunun: [GitHub Repo](https://github.com/urazakgul/tefasfon)
* Herhangi bir sorun veya öneride lütfen GitHub reposundaki "Issue" bölümünden yeni bir konu açarak bildirim sağlayın: [GitHub Issues](https://github.com/urazakgul/tefasfon/issues)

## Sürüm Notları

### v0.3.0 - 15/10/2025

* `fund_codes` parametresi ile "Fon Kodu" üzerinden tam eşleşme filtresi eklendi.
* `fund_title_contains` parametresi ile "Fon Adı" içinde kısmi arama filtresi eklendi.

### v0.2.0 - 05/09/2025

* Veri bulunmadığında güvenli dönüş sağlandı.
* WebDriver/TFLite logları kaldırıldı.
* Gün bazında ilerleme panelleri eklendi.
* Açılır menü hata mesajı yerelleştirildi.

### v0.1.0 - 20/07/2025

* İlk sürüm yayınlandı.

## Lisans

Bu proje MIT Lisansı altında lisanslanmıştır.

## For those who prefer English:

## Description

`tefasfon` is a Python package that enables you to programmatically fetch investment fund and pension fund data published on the official TEFAS website. The library offers flexible data fetching by fund type and date range. All messages and errors are displayed in Turkish or English. The output is delivered as a ready-to-use pandas DataFrame and can optionally be saved as an Excel file.

## Features

* Easily fetch TEFAS data for any desired date range and fund type.
* Fetch either general fund information or portfolio breakdown (two separate tabs).
* Errors and status messages are shown in Turkish or English.
* Simple usage; output is directly returned as a `pandas.DataFrame`.
* Optionally save the fetched data as an Excel file.
* Uses Selenium for browser automation, ensuring access to up-to-date data from the web interface.

## Installation

To use the package, follow these steps:

1. Install Python: https://www.python.org/downloads/
2. Open your terminal or command prompt and run:

```bash
pip install tefasfon
```

To install a specific version:

```bash
pip install tefasfon==0.3.0
```

To check the installed version:

```bash
pip show tefasfon
```

## Functions

### `fetch_tefas_data`

Fetches fund or portfolio data from the TEFAS website.

Parameters:

* `fund_type_code` (int): Fund type code
  * 0: Securities Mutual Funds
  * 1: Pension Funds
  * 2: Exchange Traded Funds
  * 3: Real Estate Investment Funds
  * 4: Venture Capital Investment Funds
* `tab_code` (int): Tab code
  * 0: General Information
  * 1: Portfolio Breakdown
* `start_date` (str): Start date, in 'dd.mm.yyyy' format (e.g. '17.07.2025')
* `end_date` (str): End date, in 'dd.mm.yyyy' format (e.g. '18.07.2025')
* `fund_codes` (list | None): List of codes for exact matching in the "Fund Code" column (optional)
* `fund_title_contains` (list | None): List of terms for substring matching in the "Fund Title" column (optional)
* `lang` (str): "tr" or "en" (default "tr")
* `save_to_excel` (bool): If True, saves the result to an Excel file (default: False)
* `wait_seconds` (int): Wait time between web actions (default: 3)

Returns:

* `pandas.DataFrame` (or an empty DataFrame if no data)

## Example

```python
from tefasfon import fetch_tefas_data

df = fetch_tefas_data(
    fund_type_code=0,
    tab_code=0,
    start_date="17.08.2025",
    end_date="18.07.2025",
    lang="en",
    save_to_excel=True
)

df_codes = fetch_tefas_data(
    fund_type_code=0,
    tab_code=0,
    start_date="17.07.2025",
    end_date="18.07.2025",
    fund_codes=["ABC", "XYZ"], # Fund code values
    lang="en",
    save_to_excel=False
)

df_title = fetch_tefas_data(
    fund_type_code=0,
    tab_code=0,
    start_date="17.07.2025",
    end_date="18.07.2025",
    fund_title_contains=["Gold", "Technology"], # Terms contained in the fund title
    lang="en",
    save_to_excel=False
)
```

## Notes

* The library depends on data from the [TEFAS](https://www.tefas.gov.tr/TarihselVeriler.aspx) official website. In case of any changes or maintenance, data fetching may not be possible. Please check the data status and availability on TEFAS.
* Selenium and ChromeDriver are used. Google Chrome must be installed and up-to-date on your system.
* I welcome your feedback to improve and develop the library. You can contribute to the GitHub repository: [GitHub Repo](https://github.com/urazakgul/tefasfon)
* For any issues or suggestions, please open a new topic in the "Issue" section of the GitHub repository: [GitHub Issues](https://github.com/urazakgul/tefasfon/issues)

## Release Notes

### v0.3.0 - 15/10/2025

* Added exact-match filtering on "Fund Code" via the `fund_codes` parameter.
* Added substring filtering on "Fund Title" via the `fund_title_contains` parameter.

### v0.2.0 - 05/09/2025

* Safe return when no data.
* Suppressed WebDriver/TFLite logs.
* Added per-date progress panels.
* Localized dropdown error message.

### v0.1.0 - 20/07/2025

* First release published.

## License

This project is licensed under the MIT License.