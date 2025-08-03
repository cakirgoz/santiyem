from datetime import datetime
import os
import json

def build_yapi_kullanma_input_dict(
    application_date,
    contract_date,
    acceptance_date,
    building_class,
    building_class_application_date,
    building_area,
    completion_percentage,
    teblig_sinir_tarih_opsiyonu,
    is_industrial,
    year_category=None,
    percentage_selected=None,
    approval_date=None,
    authority_group=None,
    green_building=False,
    industrial_type=None,
    tarih_opsiyonu=None
):
    """
    Yapı Kullanma İzin Belgesi Ekle sekmesi için kullanıcıdan alınan verileri dictionary olarak döndürür.
    """
    # teblig_sinir_tarih_opsiyonu için Türkçe metin belirleme
    teblig_text = ""
    tarih_opsiyonu_gercerlilik = ""
    
    if teblig_sinir_tarih_opsiyonu == "yayim":
        teblig_text = "Tebliğ yayımlanma tarihi esas alınsın."
        tarih_opsiyonu_gercerlilik = "yayim"
    elif teblig_sinir_tarih_opsiyonu == "gecerlilik":
        teblig_text = "Tebliğde belirtilen geçerlilik süresi esas alınsın."
        tarih_opsiyonu_gercerlilik = "gecerlilik"
    
    return {
        "application_date": application_date,
        "contract_date": contract_date,
        "acceptance_date": acceptance_date,
        "building_class": building_class,
        "building_class_application_date": building_class_application_date,
        "building_area": building_area,
        "completion_percentage": completion_percentage,
        "teblig_sinir_tarih_opsiyonu": teblig_text,
        "is_industrial": is_industrial,
        "year_category": year_category if is_industrial == "Evet" else None,
        "percentage_selected": percentage_selected if is_industrial == "Evet" and year_category == "2019 Öncesi" else None,
        "approval_date": approval_date if is_industrial == "Evet" and year_category == "2019 Sonrası" else None,
        "authority_group": authority_group if is_industrial == "Evet" and year_category == "2019 Sonrası" else None,
        "green_building": green_building,
        "industrial_type": industrial_type if is_industrial == "Evet" else None,
        "tarih_opsiyonu": tarih_opsiyonu,
        "tarih_opsiyonu_gercerlilik": tarih_opsiyonu_gercerlilik,
    }

def validate_building_permit_inputs(params):
    """
    Yapı Kullanma İzin Belgesi için giriş verilerini doğrular.
    """
    errors = []

    if not params.get("contract_date"):
        errors.append("Sözleşme tarihi eksik.")
    if not params.get("acceptance_date"):
        errors.append("Geçici kabul/iskân tarihi eksik.")
    if not params.get("building_area") or float(params["building_area"]) == 0.0:
        errors.append("Yapı alanı sıfır olamaz.")
    if not params.get("building_class"):
        errors.append("Sözleşme tarihindeki yapı sınıfı seçilmelidir.")
    if not params.get("building_class_application_date"):
        errors.append("Başvuru tarihindeki yapı sınıfı seçilmelidir.")
    if not params.get("completion_percentage") or float(params["completion_percentage"]) == 0.0:
        errors.append("Tamamlanma yüzdesi boş veya sıfır olamaz.")

    if params.get("is_industrial") == "Evet":
        if params.get("industrial_type") == "İş deneyimine tabi olmayan sanayi yapısı":
            errors.append("İş deneyimine tabi olmayan sanayi yapıları müteahhitlik başvurularında kullanılamaz.")

        if params.get("year_category") == "2019 Sonrası":
            if not params.get("approval_date"):
                errors.append("Sanayi yapısı (2019 sonrası) için ruhsat onay tarihi eksik.")
            if not params.get("authority_group"):
                errors.append("Sanayi yapısı (2019 sonrası) için yetki belge grubu eksik.")

    return errors

def get_unit_prices_for_building_classes(contract_date, application_date, building_class_contract,
                                         building_class_application, tarih_opsiyonu,
                                         json_path='app/engineering_apps/data/birim_fiyatlar.json'):

    def date_in_range(date_obj, start_str, end_str):
        start = datetime.strptime(start_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_str, "%Y-%m-%d").date()
        return start <= date_obj <= end

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if tarih_opsiyonu == "yayim":
        field_start = "yayim_tarihi"
        field_end = "yayim_sonu"
    else:
        field_start = "gecerlilik_tarihi"
        field_end = "gecerlilik_sonu"

    contract_unit_price = None
    application_unit_price = None

    for record in data:
        # Sözleşme tarihi dönemi
        if contract_unit_price is None and date_in_range(contract_date, record[field_start], record[field_end]):
            price = record["data"].get(building_class_contract)
            if price is None:
                raise ValueError(f"Seçilen tarih için seçmiş olduğunuz {building_class_contract} yapı sınıfı bulunamamıştır, girdiğiniz tarihi veya yapı sınıfını kontrol ediniz.")
            contract_unit_price = price

        # Başvuru tarihi dönemi
        if application_unit_price is None and date_in_range(application_date, record[field_start], record[field_end]):
            price = record["data"].get(building_class_application)
            if price is None:
                raise ValueError(f"Seçilen tarih için seçmiş olduğunuz {building_class_application} yapı sınıfı bulunamamıştır, girdiğiniz tarihi veya yapı sınıfını kontrol ediniz.")
            application_unit_price = price

        # Erken çıkmak için
        if contract_unit_price is not None and application_unit_price is not None:
            break

    if contract_unit_price is None:
        raise ValueError(f"Seçilen tarih için seçmiş olduğunuz {building_class_contract} yapı sınıfı bulunamamıştır, girdiğiniz tarihi veya yapı sınıfını kontrol ediniz.")
    if application_unit_price is None:
        raise ValueError(f"Seçilen tarih için seçmiş olduğunuz {building_class_application} yapı sınıfı bulunamamıştır, girdiğiniz tarihi veya yapı sınıfını kontrol ediniz.")

    unit_price_ratio = application_unit_price / contract_unit_price

    return {
        "unit_price_contract": contract_unit_price,
        "unit_price_application": application_unit_price,
        "unit_price_ratio": unit_price_ratio
    }

def get_unit_prices_for_building_classes_tutara_esas(contract_date, building_class_contract,
                                         tarih_opsiyonu='gecerlilik',
                                         json_path='app/engineering_apps/data/birim_fiyatlar.json'):

    def date_in_range(date_obj, start_str, end_str):
        start = datetime.strptime(start_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_str, "%Y-%m-%d").date()
        return start <= date_obj <= end

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if tarih_opsiyonu == "yayim":
        field_start = "yayim_tarihi"
        field_end = "yayim_sonu"
    else:
        field_start = "gecerlilik_tarihi"
        field_end = "gecerlilik_sonu"

    contract_unit_price = None

    for record in data:
        # Sözleşme tarihi dönemi
        if contract_unit_price is None and date_in_range(contract_date, record[field_start], record[field_end]):
            price = record["data"].get(building_class_contract)
            if price is None:
                raise ValueError(f"Seçilen tarih için seçmiş olduğunuz {building_class_contract} yapı sınıfı bulunamamıştır, girdiğiniz tarihi veya yapı sınıfını kontrol ediniz.")
            contract_unit_price = price

        # Erken çıkmak için
        if contract_unit_price is not None:
            break

    if contract_unit_price is None:
        raise ValueError(f"Seçilen tarih için seçmiş olduğunuz {building_class_contract} yapı sınıfı bulunamamıştır, girdiğiniz tarihi veya yapı sınıfını kontrol ediniz.")

    return {
        "unit_price_contract_ruhsata_esas": contract_unit_price
    }

def get_max_industrial_amount(authority_group, json_path='app/engineering_apps/data/max_is_tutari.json'):
    """
    Sanayi yapısı için maksimum tutarı JSON dosyasından alır.
    Kullanıcının seçtiği authority_group'e göre tutarı döndürür.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # JSON dosyası bir liste içinde dönem objeleri şeklinde
        # En güncel dönemi al (ilk eleman)
        if not data or not isinstance(data, list):
            raise ValueError("JSON dosyası geçerli bir liste formatında değil.")
        
        # En güncel dönemi al (ilk eleman)
        current_period = data[0]
        tutarlar = current_period.get("tutarlar", {})
        
        if not tutarlar:
            raise ValueError("Güncel dönemde tutarlar bulunamadı.")
        
        # Kullanıcının seçtiği authority_group'e göre tutarı al
        if authority_group not in tutarlar:
            raise ValueError(f"Seçilen belge grubu '{authority_group}' için tutar bulunamadı.")
        
        max_amount = tutarlar[authority_group]
        
        return {
            "max_industrial_amount": max_amount
        }
    except Exception as e:
        raise ValueError(f"Maksimum sanayi tutarı alınırken hata oluştu: {str(e)}")

def get_previous_month_info(date_obj):
    """
    Verilen tarihin bir önceki ayının bilgilerini döndürür.
    """
    year = date_obj.year
    month = date_obj.month

    if month == 1:
        return {"year": year - 1, "month": 12}
    else:
        return {"year": year, "month": month - 1}

def get_ufe_data_and_ratio(contract_month_info, application_month_info, json_path='app/engineering_apps/data/yi_ufe_data.json'):
    """
    Sözleşme ve başvuru tarihlerinin önceki aylarına ait ÜFE endeksleri ve oranlarını alır.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    year_contract = str(contract_month_info["year"])
    month_contract = str(contract_month_info["month"])
    year_application = str(application_month_info["year"])
    month_application = str(application_month_info["month"])

    try:
        ufe_contract = data[year_contract][month_contract]
    except KeyError:
        raise ValueError(f"ÜFE verisi bulunamadı: {year_contract}/{month_contract}")

    try:
        ufe_application = data[year_application][month_application]
    except KeyError:
        raise ValueError(f"ÜFE verisi bulunamadı: {year_application}/{month_application}")

    try:
        ufe_update_ratio = ufe_application / ufe_contract
    except ZeroDivisionError:
        raise ValueError("Sözleşme dönemine ait ÜFE verisi sıfır, oran hesaplanamıyor.")

    return {
        "ufe_contract": ufe_contract,
        "ufe_application": ufe_application,
        "ufe_update_ratio": ufe_update_ratio
    }

def calculate_document_update_ratio(params):
    """
    Belge tutarının güncelleme oranını hesaplar.
    """
    upr = params.get("unit_price_ratio")
    ufe = params.get("ufe_update_ratio")

    if upr is None or ufe is None:
        raise ValueError("Güncelleme oranı hesaplanamıyor. unit_price_ratio ve ufe_update_ratio gereklidir.")

    min_allowed = 0.9 * upr
    max_allowed = 1.3 * upr

    if ufe < min_allowed:
        return min_allowed
    elif ufe > max_allowed:
        return max_allowed
    else:
        return ufe

def get_green_building_factor(green_building_selected):
    """
    Yeşil bina seçimine göre faktör değerini döndürür.
    """
    return 1.05 if green_building_selected else 1.0

def calculate_base_amount(params):
    """
    Temel tutarı hesaplar.
    """
    area = params.get("building_area")
    unit_price = params.get("unit_price_contract_ruhsata_esas")
    completion = params.get("completion_percentage")

    if area is None or unit_price is None or completion is None:
        raise ValueError("Base amount hesaplamak için building_area, unit_price_contract ve completion_percentage gereklidir.")

    # String değerleri float'a çevir
    try:
        area = float(area)
        unit_price = float(unit_price)
        completion = float(completion)
    except (ValueError, TypeError):
        raise ValueError("building_area, unit_price_contract_ruhsata_esas ve completion_percentage sayısal değerler olmalıdır.")

    return area * unit_price * (completion / 100)

def calculate_contractor_base_amount(params):
    """
    Müteahhitlik belge tutarını hesaplar.
    """
    base_amount = params.get("base_amount")
    green_factor = params.get("green_building_factor", 1.0)
    is_industrial = params.get("is_industrial")
    year_category = params.get("year_category")

    if base_amount is None:
        raise ValueError("Base amount gereklidir.")

    # Sanayi yapısı değilse
    if is_industrial != "Evet":
        return 0.85 * base_amount * green_factor

    # Sanayi yapısı ve 2019 öncesi
    if year_category == "2019 Öncesi":
        return 0.20 * base_amount

    # Sanayi yapısı ve 2019 sonrası
    if year_category == "2019 Sonrası":
        max_amount = params.get("max_industrial_amount")
        if max_amount is None:
            raise ValueError("max_industrial_amount değeri gerekli.")
        return min(base_amount, max_amount)

    # Diğer tüm durumlar
    raise ValueError("Müteahhitlik belge tutarı hesaplaması için gerekli bilgiler eksik.")

def calculate_updated_contractor_amount(params):
    """
    Güncel belge tutarını hesaplar.
    """
    contractor_base_amount = params.get("contractor_base_amount")
    document_update_ratio = params.get("document_update_ratio")

    if contractor_base_amount is None:
        raise ValueError("contractor_base_amount gereklidir.")
    
    if document_update_ratio is None:
        raise ValueError("document_update_ratio gereklidir.")

    return contractor_base_amount * document_update_ratio

def calculate_son_5_15_yil(params):
    """
    Başvuru tarihine göre geçici kabul/iskan tarihinin son 5 yıl veya 15 yıl içinde olup olmadığını kontrol eder.
    """
    application_date_str = params.get("application_date")
    acceptance_date_str = params.get("acceptance_date")
    
    if application_date_str is None:
        raise ValueError("application_date gereklidir.")
    
    if acceptance_date_str is None:
        raise ValueError("acceptance_date gereklidir.")
    
    # Tarih string'lerini datetime objelerine çevir
    try:
        application_date = datetime.strptime(application_date_str, "%Y-%m-%d").date()
        acceptance_date = datetime.strptime(acceptance_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Tarih formatları hatalı. YYYY-MM-DD formatında olmalıdır.")
    
    # Başvuru tarihinden geriye dönük 5 yıl ve 15 yıl hesapla
    five_years_ago = application_date.replace(year=application_date.year - 5)
    fifteen_years_ago = application_date.replace(year=application_date.year - 15)
    
    # Geçici kabul/iskan tarihi başvuru tarihinden sonra olamaz
    if acceptance_date > application_date:
        raise ValueError("Geçici kabul/iskan tarihi başvuru tarihinden sonra olamaz.")
    
    # Son 5 yıl içinde mi kontrol et
    if acceptance_date >= five_years_ago:
        return "5_yil"
    
    # Son 15 yıl içinde mi kontrol et
    if acceptance_date >= fifteen_years_ago:
        return "15_yil"
    
    # 15 yıldan daha eski ise hata ver
    raise ValueError("Geçici kabul/iskan tarihi son 15 yıl içinde değil. Bu belge kullanılamaz.")

def calculate_building_permit(params):
    """
    Yapı Kullanma İzin Belgesi hesaplaması yapar.
    """
    try:
        # Tarih string'lerini datetime objelerine çevir
        contract_date = datetime.strptime(params.get("contract_date"), "%Y-%m-%d").date()
        application_date = datetime.strptime(params.get("application_date"), "%Y-%m-%d").date()
        
        # Son 5/15 yıl kontrolü yap
        son_5_15_yil = calculate_son_5_15_yil(params)
        params.update({"son_5_15_yil": son_5_15_yil})
        
        # Bir önceki ay bilgilerini al
        contract_previous_month = get_previous_month_info(contract_date)
        application_previous_month = get_previous_month_info(application_date)
        
        # ÜFE verilerini al
        ufe_data = get_ufe_data_and_ratio(contract_previous_month, application_previous_month)
        
        # Birim fiyatları al
        unit_prices = get_unit_prices_for_building_classes(
            contract_date=contract_date,
            application_date=application_date,
            building_class_contract=params.get("building_class"),
            building_class_application=params.get("building_class_application_date"),
            tarih_opsiyonu=params.get("tarih_opsiyonu_gercerlilik")
        )
        
        # Ruhsata esas birim fiyatı al
        ruhsata_esas_prices = get_unit_prices_for_building_classes_tutara_esas(
            contract_date=contract_date,
            building_class_contract=params.get("building_class"),
            tarih_opsiyonu=params.get("tarih_opsiyonu_gercerlilik")
        )
        
        # Yeşil bina faktörünü al
        green_building_factor = get_green_building_factor(params.get("green_building", False))
        
        # Hesaplama parametrelerini güncelle
        params.update(unit_prices)
        params.update(ruhsata_esas_prices)
        params.update({
            "contract_previous_month": contract_previous_month,
            "application_previous_month": application_previous_month,
            "green_building_factor": green_building_factor
        })
        params.update(ufe_data)
        
        # Belge güncelleme oranını hesapla
        document_update_ratio = calculate_document_update_ratio(params)
        params.update({"document_update_ratio": document_update_ratio})
        
        # Sanayi yapısı ve 2019 sonrası koşulları kontrol et
        if params.get("is_industrial") == "Evet" and params.get("year_category") == "2019 Sonrası":
            max_industrial = get_max_industrial_amount(params.get("authority_group"))
            params.update(max_industrial)
        
        # Temel tutarı hesapla
        base_amount = calculate_base_amount(params)
        params.update({"base_amount": base_amount})
        
        # Müteahhitlik belge tutarını hesapla
        contractor_base_amount = calculate_contractor_base_amount(params)
        params.update({"contractor_base_amount": contractor_base_amount})
        
        # Güncel belge tutarını hesapla
        updated_contractor_amount = calculate_updated_contractor_amount(params)
        params.update({"updated_contractor_amount": updated_contractor_amount})
        
        # Dummy hesaplama - gerçek algoritma daha sonra eklenecek
        building_area = float(params.get("building_area", 0))
        completion_percentage = float(params.get("completion_percentage", 100))
        
        # Final hesaplama
        final_amount = updated_contractor_amount
        
        # Sonuç detaylarını hazırla
        details = {
            "building_area": building_area,
            "completion_percentage": completion_percentage,
            "base_amount": base_amount,
            "contractor_base_amount": contractor_base_amount,
            "updated_contractor_amount": updated_contractor_amount,
            "adjusted_amount": final_amount,
            "son_5_15_yil": son_5_15_yil,
            "unit_price_contract": unit_prices["unit_price_contract"],
            "unit_price_application": unit_prices["unit_price_application"],
            "unit_price_ratio": unit_prices["unit_price_ratio"],
            "unit_price_contract_ruhsata_esas": ruhsata_esas_prices["unit_price_contract_ruhsata_esas"],
            "contract_previous_month": contract_previous_month,
            "application_previous_month": application_previous_month,
            "ufe_contract": ufe_data["ufe_contract"],
            "ufe_application": ufe_data["ufe_application"],
            "ufe_update_ratio": ufe_data["ufe_update_ratio"],
            "document_update_ratio": document_update_ratio,
            "green_building_factor": green_building_factor
        }
        
        # Sanayi yapısı maksimum tutarını ekle (varsa)
        if params.get("is_industrial") == "Evet" and params.get("year_category") == "2019 Sonrası":
            details["max_industrial_amount"] = params.get("max_industrial_amount", 0)
        
        return {
            "success": True,
            "amount": final_amount,
            "formatted_amount": f"{final_amount:,.2f} TL",
            "details": details
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Hesaplama hatası: {str(e)}"
        } 