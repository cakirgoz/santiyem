import json
import re
from datetime import datetime
import os

def format_currency(amount):
    """Para formatını düzenler"""
    try:
        return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"
    except Exception:
        return str(amount)

def parse_currency(currency_str):
    """Para string'ini sayıya çevirir"""
    try:
        if not currency_str or currency_str == '':
            return 0
        # "1.234,56 TL" veya "1,234,567.89 TL" formatından sayıya çevir
        clean_str = currency_str.replace(' TL', '').replace(' ', '')
        
        # Eğer hem virgül hem nokta varsa
        if ',' in clean_str and '.' in clean_str:
            # Türk formatı: 1.234,56 (nokta binlik, virgül ondalık)
            if clean_str.count('.') > 1:  # Birden fazla nokta varsa Türk formatı
                clean_str = clean_str.replace('.', '').replace(',', '.')
            # İngiliz formatı: 1,234,567.89 (virgül binlik, nokta ondalık)
            else:
                clean_str = clean_str.replace(',', '')
        # Eğer sadece virgül varsa (Türk formatı: 1.234,56)
        elif ',' in clean_str and '.' not in clean_str:
            # Nokta binlik ayırıcı, virgül ondalık ayırıcı
            clean_str = clean_str.replace('.', '').replace(',', '.')
        # Eğer sadece nokta varsa (basit format: 1234567.89)
        elif '.' in clean_str and ',' not in clean_str:
            # Nokta ondalık ayırıcı
            pass
        
        return float(clean_str)
    except Exception as e:
        print(f"DEBUG: parse_currency error for '{currency_str}': {e}")
        return 0

def calculate_mezuniyet_tutari(belgeler):
    """Güncellenmiş Mezuniyet Belgesi tutarını hesaplar"""
    print(f"DEBUG: calculate_mezuniyet_tutari called with {len(belgeler)} belgeler")
    for belge in belgeler:
        deneyim_tipi = belge.get('deneyim_tipi', '')
        print(f"DEBUG: Checking belge with deneyim_tipi: '{deneyim_tipi}'")
        if deneyim_tipi in ['Mezuniyet belgesi', 'Mezuniyet Belgesi']:
            guncel_tutar = belge.get('guncel_tutar', '')
            print(f"DEBUG: Found mezuniyet belgesi with guncel_tutar: '{guncel_tutar}'")
            return parse_currency(guncel_tutar)
    print("DEBUG: No mezuniyet belgesi found")
    return None

def calculate_en_buyuk_is_deneyimi(belgeler):
    """Mezuniyet hariç en büyük iş deneyimini hesaplar"""
    max_tutar = 0
    for belge in belgeler:
        deneyim_tipi = belge.get('deneyim_tipi', '')
        if deneyim_tipi not in ['Mezuniyet belgesi', 'Mezuniyet Belgesi']:
            tutar = parse_currency(belge.get('guncel_tutar', ''))
            if tutar > max_tutar:
                max_tutar = tutar
    return max_tutar if max_tutar > 0 else None

def calculate_en_buyuk_2_kat(belgeler):
    """Mezuniyet hariç en büyük iş deneyiminin 2 katını hesaplar"""
    max_tutar = calculate_en_buyuk_is_deneyimi(belgeler)
    return max_tutar * 2 if max_tutar is not None else None

def calculate_en_buyuk_3_kat(belgeler):
    """Mezuniyet hariç en büyük iş deneyiminin 3 katını hesaplar"""
    max_tutar = calculate_en_buyuk_is_deneyimi(belgeler)
    return max_tutar * 3 if max_tutar is not None else None

def calculate_son_5_yil_toplam(belgeler):
    """Son 5 yıldaki iş deneyimlerinin toplamını hesaplar (3 kat limitli)"""
    son_5_yil_toplam = 0
    max_tutar = calculate_en_buyuk_is_deneyimi(belgeler)
    
    # Son 5 yıldaki toplamı hesapla
    for belge in belgeler:
        deneyim_tipi = belge.get('deneyim_tipi', '')
        if deneyim_tipi not in ['Mezuniyet belgesi', 'Mezuniyet Belgesi'] and belge.get('son_yil') == '5 Yıl':
            tutar = parse_currency(belge.get('guncel_tutar', ''))
            son_5_yil_toplam += tutar
    
    # 3 kat limitini uygula
    if max_tutar and max_tutar > 0:
        limit = max_tutar * 3
        return min(son_5_yil_toplam, limit)
    return son_5_yil_toplam if son_5_yil_toplam > 0 else None

def get_period_for_date(application_date, tarih_opsiyonu):
    """Başvuru tarihine göre dönemi bulur"""
    try:
        app_date = datetime.strptime(application_date, "%Y-%m-%d").date()
        
        with open('app/engineering_apps/data/grup_sinir_tutarlari.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for period in data:
            if tarih_opsiyonu == "yayim":
                start_date = datetime.strptime(period["yayim_tarihi"], "%Y-%m-%d").date()
                end_date = datetime.strptime(period["yayim_sonu"], "%Y-%m-%d").date()
            else:  # gecerlilik
                start_date = datetime.strptime(period["gecerlilik_tarihi"], "%Y-%m-%d").date()
                end_date = datetime.strptime(period["gecerlilik_sonu"], "%Y-%m-%d").date()
            
            if start_date <= app_date <= end_date:
                return period
        
        return None
    except Exception as e:
        print(f"Periyot bulma hatası: {e}")
        return None

def determine_document_class(calculated_amount, period_data):
    """Hesaplanan tutara göre belge sınıfını belirler"""
    if not period_data or calculated_amount <= 0:
        return None
    
    tutarlar = period_data["tutarlar"]
    # Sınıfları büyükten küçüğe sırala
    sorted_classes = sorted(tutarlar.items(), key=lambda x: x[1], reverse=True)
    
    for sinif, sinir_tutar in sorted_classes:
        if calculated_amount >= sinir_tutar:
            return sinif
    
    return None

def calculate_is_deneyimi_degerlendirme(belgeler, application_date, tarih_opsiyonu):
    """
    İş deneyimi değerlendirmesi yapar
    """
    print(f"DEBUG: calculate_is_deneyimi_degerlendirme called with {len(belgeler)} belgeler")
    print(f"DEBUG: application_date: {application_date}, tarih_opsiyonu: {tarih_opsiyonu}")
    
    # 3 yöntemi hesapla
    mezuniyet_tutari = calculate_mezuniyet_tutari(belgeler)
    print(f"DEBUG: mezuniyet_tutari: {mezuniyet_tutari}")
    
    en_buyuk_is_deneyimi = calculate_en_buyuk_is_deneyimi(belgeler)
    print(f"DEBUG: en_buyuk_is_deneyimi: {en_buyuk_is_deneyimi}")
    
    en_buyuk_2_kat = calculate_en_buyuk_2_kat(belgeler)
    print(f"DEBUG: en_buyuk_2_kat: {en_buyuk_2_kat}")
    
    en_buyuk_3_kat = calculate_en_buyuk_3_kat(belgeler)
    print(f"DEBUG: en_buyuk_3_kat: {en_buyuk_3_kat}")
    
    son_5_yil_toplam = calculate_son_5_yil_toplam(belgeler)
    print(f"DEBUG: son_5_yil_toplam: {son_5_yil_toplam}")
    
    # En büyük değeri bul
    hesaplanan_degerler = []
    if mezuniyet_tutari is not None:
        hesaplanan_degerler.append(mezuniyet_tutari)
    if en_buyuk_2_kat is not None:
        hesaplanan_degerler.append(en_buyuk_2_kat)
    if son_5_yil_toplam is not None:
        hesaplanan_degerler.append(son_5_yil_toplam)
    
    print(f"DEBUG: hesaplanan_degerler: {hesaplanan_degerler}")
    
    if not hesaplanan_degerler:
        print("DEBUG: No hesaplanan_degerler found")
        return {
            "success": False,
            "error": "Hesaplanabilir değer bulunamadı."
        }
    
    esas_belge_tutari = max(hesaplanan_degerler)
    print(f"DEBUG: esas_belge_tutari: {esas_belge_tutari}")
    
    # Dönemi bul
    period_data = get_period_for_date(application_date, tarih_opsiyonu)
    print(f"DEBUG: period_data found: {period_data is not None}")
    
    if not period_data:
        print("DEBUG: No period_data found")
        return {
            "success": False,
            "error": "Başvuru tarihi için uygun dönem bulunamadı."
        }
    
    # Belge sınıfını belirle
    belge_sinifi = determine_document_class(esas_belge_tutari, period_data)
    print(f"DEBUG: belge_sinifi: {belge_sinifi}")
    
    # Sonuçları hazırla
    result = {
        "success": True,
        "mezuniyet_tutari": mezuniyet_tutari,
        "en_buyuk_is_deneyimi": en_buyuk_is_deneyimi,
        "en_buyuk_2_kat": en_buyuk_2_kat,
        "en_buyuk_3_kat": en_buyuk_3_kat,
        "son_5_yil_toplam": son_5_yil_toplam,
        "esas_belge_tutari": esas_belge_tutari,
        "belge_sinifi": belge_sinifi,
        "period_data": period_data,
        "application_date": application_date,
        "tarih_opsiyonu": tarih_opsiyonu
    }
    
    print(f"DEBUG: Returning result with success: {result['success']}")
    return result 