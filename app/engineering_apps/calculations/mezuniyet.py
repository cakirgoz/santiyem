import json
from datetime import datetime, date
import os

def get_price_for_date(date_obj, json_file_path):
    """
    Verilen tarih ve json dosyasına göre, belirtilen tarihin hangi dönemde olduğunu
    ve o döneme ait fiyat bilgisini döndüren fonksiyon.
    """
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for period in data:
        start_date = datetime.strptime(period['baslangic_yayim'], '%d.%m.%Y').date()
        end_date = datetime.strptime(period['bitis_yayim'], '%d.%m.%Y').date()
        if start_date <= date_obj <= end_date:
            return period['yillik_tutar']
    return None

def mezuniyet_guncelle(tarih1, tarih2, mezuniyet_tutar_json_path, has_experience_cert=False):
    """
    Calculate updated graduation amount based on date differences
    """
    yillik_tutar = get_price_for_date(tarih1, mezuniyet_tutar_json_path)
    if yillik_tutar:
        yillar = tarih1.year - tarih2.year
        aylar = tarih1.month - tarih2.month
        gunler = tarih1.day - tarih2.day
        if gunler < 0:
            if tarih1.year % 4 == 0 and tarih1.month - 1 == 2:
                gunler += 29
                aylar -= 1
            elif tarih1.year % 4 != 0 and tarih1.month - 1 == 2:
                gunler += 28
                aylar -= 1
            elif tarih1.month - 1 in [1, 3, 5, 7, 8, 0, 9, 11]:
                gunler += 31
                aylar -= 1
            else:
                gunler += 30
                aylar -= 1
        if aylar < 0:
            aylar += 12
            yillar -= 1
        if not has_experience_cert and yillar >= 15:
            yillar = 15
            aylar = 0
            gunler = 0
        guncel_tutar = (yillik_tutar * yillar) + \
                       (yillik_tutar * aylar / 12) + \
                       (yillik_tutar * gunler / (12 * 30))
        calc_details = {
            'yillar': yillar,
            'aylar': aylar,
            'gunler': gunler,
            'yillik_tutar': yillik_tutar
        }
        return round(guncel_tutar, 2), calc_details
    else:
        return (0, None) 