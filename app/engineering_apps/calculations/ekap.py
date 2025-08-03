import json
from datetime import datetime
import os
from .yapi_kullanma import get_previous_month_info, get_ufe_data_and_ratio, get_unit_prices_for_building_classes, calculate_document_update_ratio, calculate_son_5_15_yil

def build_ekap_input_dict(form):
    """
    EKAP İş Deneyim Belgesi Ekle sekmesi için kullanıcıdan alınan verileri dictionary olarak döndürür.
    """
    params = {}
    # Kat/Arsa Karşılığı
    kat_arsa_karsiligi = "kat_arsa_karsiligi" in form
    params["kat_karsiligi"] = "Evet" if kat_arsa_karsiligi else "Hayır"
    if kat_arsa_karsiligi:
        params["building_class"] = form.get("building_class")
        params["building_class_application_date"] = form.get("building_class_application_date")
        kat_arsa_opsiyon = form.get("kat_arsa_teblig_sinir_tarih_opsiyonu")
        if kat_arsa_opsiyon:
            if kat_arsa_opsiyon == "gecerlilik":
                params["teblig_sinir_tarih_opsiyonu"] = "Tebliğde belirtilen geçerlilik süresi esas alınsın."
            elif kat_arsa_opsiyon == "yayim":
                params["teblig_sinir_tarih_opsiyonu"] = "Tebliğ yayımlanma tarihi esas alınsın."
            params["tarih_opsiyonu_gercerlilik"] = kat_arsa_opsiyon
    # Checkboxlar ve faktörler
    take_85_percent = "take_85_percent" in form
    params["take_85_percent"] = "Evet" if take_85_percent else "Hayır"
    green_building = "green_building" in form
    params["green_building"] = "Evet" if green_building else "Hayır"
    green_building_factor = 1.05 if green_building else 1.0
    params["green_building_factor"] = green_building_factor
    joint_venture = "joint_venture" in form
    params["joint_venture"] = "Evet" if joint_venture else "Hayır"
    if joint_venture:
        venture_ratio = form.get("venture_ratio")
        params["venture_ratio"] = venture_ratio
    # Sanayi yapısı
    params["is_industrial"] = form.get("ekap_is_industrial")
    if params["is_industrial"] == "Evet":
        params["industrial_type"] = form.get("ekap_industrial_type")
        params["year_category"] = form.get("ekap_year_category")
        if params["year_category"] == "2019 Öncesi":
            params["percentage_selected"] = "Evet" if "ekap_percentage_selected" in form else "Hayır"
        elif params["year_category"] == "2019 Sonrası":
            params["approval_date"] = form.get("ekap_approval_date")
            params["authority_group"] = form.get("ekap_authority_group")
            params["teblig_sinir_tarih_opsiyonu"] = form.get("ekap_teblig_sinir_tarih_opsiyonu")
    # Temel alanlar
    params["application_date"] = form.get("application_date")
    params["contract_date"] = form.get("contract_date")
    params["acceptance_date"] = form.get("acceptance_date")
    params["initial_amount"] = form.get("initial_amount")
    params["document_amount"] = form.get("document_amount")
    return params

def format_currency(amount):
    try:
        return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " TL"
    except Exception:
        return str(amount)

def calculate_ekap_amount(params):
    """
    EKAP İş Deneyim Belgesi için güncel belge tutarını ve açıklama listesini döndürür.
    """
    try:
        belge_tutari = float(params["document_amount"])
    except Exception:
        raise ValueError("Belge tutarı sayısal olmalıdır.")
    take_85_percent = params["take_85_percent"] == "Evet"
    green_building_factor = float(params.get("green_building_factor", 1.0))
    joint_venture = params["joint_venture"] == "Evet"
    if joint_venture:
        try:
            venture_ratio_val = float(params.get("venture_ratio", 100)) / 100.0
        except Exception:
            venture_ratio_val = 1.0
    else:
        venture_ratio_val = 1.0
    esas_belge_tutari = belge_tutari * (0.85 if take_85_percent else 1.0) * green_building_factor * venture_ratio_val

    contract_date_str = params.get("contract_date")
    application_date_str = params.get("application_date")
    acceptance_date_str = params.get("acceptance_date")
    building_class_contract = params.get("building_class")
    building_class_application = params.get("building_class_application_date")
    tarih_opsiyonu = params.get("tarih_opsiyonu_gercerlilik")

    contract_date = None
    application_date = None
    acceptance_date = None
    try:
        contract_date = datetime.strptime(contract_date_str, "%Y-%m-%d").date()
        application_date = datetime.strptime(application_date_str, "%Y-%m-%d").date()
        acceptance_date = datetime.strptime(acceptance_date_str, "%Y-%m-%d").date() if acceptance_date_str else None
    except Exception:
        pass

    contract_previous_month = None
    application_previous_month = None
    ufe_data = None
    unit_prices = None
    birim_fiyat_orani = None
    belge_guncelleme_orani = None
    guncel_belge_tutari = None
    son_5_15_yil = ''
    kat_karsiligi = params.get("kat_karsiligi") == "Evet"
    try:
        if contract_date and application_date:
            contract_previous_month = get_previous_month_info(contract_date)
            application_previous_month = get_previous_month_info(application_date)
            ufe_data = get_ufe_data_and_ratio(contract_previous_month, application_previous_month)
            if acceptance_date:
                try:
                    son_5_15_yil = calculate_son_5_15_yil({
                        "application_date": application_date_str,
                        "acceptance_date": acceptance_date_str
                    })
                except Exception:
                    son_5_15_yil = ''
            if kat_karsiligi and building_class_contract and building_class_application and tarih_opsiyonu:
                unit_prices = get_unit_prices_for_building_classes(
                    contract_date=contract_date,
                    application_date=application_date,
                    building_class_contract=building_class_contract,
                    building_class_application=building_class_application,
                    tarih_opsiyonu=tarih_opsiyonu
                )
                birim_fiyat_orani = unit_prices["unit_price_application"] / unit_prices["unit_price_contract"]
                belge_guncelleme_orani = calculate_document_update_ratio({
                    "unit_price_ratio": unit_prices["unit_price_ratio"],
                    "ufe_update_ratio": ufe_data["ufe_update_ratio"]
                })
            elif ufe_data:
                belge_guncelleme_orani = ufe_data["ufe_update_ratio"]
            if belge_guncelleme_orani is not None:
                guncel_belge_tutari = esas_belge_tutari * belge_guncelleme_orani
    except Exception:
        pass

    aciklama_list = []
    aciklama_list.append(f"Güncellenmemiş Belge Tutarı: {format_currency(belge_tutari)}")
    aciklama_list.append(f"Güncellemeye Esas Belge Tutarı: {format_currency(esas_belge_tutari)}")
    if guncel_belge_tutari is not None:
        aciklama_list.append(f"Güncel Belge Tutarı: {format_currency(guncel_belge_tutari)}")
    if son_5_15_yil:
        aciklama_list.append(f"Son 5 yıl/Son 15 Yıl: {son_5_15_yil.replace('_', ' ').replace('yil', 'Yıl').capitalize()}")
    if contract_previous_month:
        aciklama_list.append(f"Sözleşme Tarihi Önceki Ay: {contract_previous_month['year']}-{contract_previous_month['month']:02d}")
    if ufe_data:
        aciklama_list.append(f"Sözleşme Dönemi ÜFE Endeksi: {ufe_data['ufe_contract']}")
    if application_previous_month:
        aciklama_list.append(f"Başvuru Tarihi Önceki Ay: {application_previous_month['year']}-{application_previous_month['month']:02d}")
    if ufe_data:
        aciklama_list.append(f"Başvuru Dönemi ÜFE Endeksi: {ufe_data['ufe_application']}")
        aciklama_list.append(f"ÜFE Güncelleme Oranı: {ufe_data['ufe_update_ratio']:.4f}")
    if kat_karsiligi and unit_prices:
        aciklama_list.append(f"Sözleşme Tarihi Birim Fiyatı: {format_currency(unit_prices['unit_price_contract'])}")
        aciklama_list.append(f"Başvuru Tarihi Birim Fiyatı: {format_currency(unit_prices['unit_price_application'])}")
        if birim_fiyat_orani is not None:
            aciklama_list.append(f"Birim Fiyat Oranı: {birim_fiyat_orani:.4f}")
    if belge_guncelleme_orani is not None:
        aciklama_list.append(f"Belge Güncelleme Oranı: {belge_guncelleme_orani:.4f}")

    # Dictionary'ye ekle
    params["guncellenmemis_belge_tutari"] = belge_tutari
    params["guncellemeye_esas_belge_tutari"] = esas_belge_tutari
    if contract_previous_month:
        params["contract_previous_month"] = contract_previous_month
    if application_previous_month:
        params["application_previous_month"] = application_previous_month
    if ufe_data:
        params["ufe_contract"] = ufe_data["ufe_contract"]
        params["ufe_application"] = ufe_data["ufe_application"]
        params["ufe_update_ratio"] = ufe_data["ufe_update_ratio"]
    if kat_karsiligi and unit_prices:
        params["unit_price_contract"] = unit_prices["unit_price_contract"]
        params["unit_price_application"] = unit_prices["unit_price_application"]
        params["unit_price_ratio"] = unit_prices["unit_price_ratio"]
    if kat_karsiligi and birim_fiyat_orani is not None:
        params["birim_fiyat_orani"] = birim_fiyat_orani
    if belge_guncelleme_orani is not None:
        params["belge_guncelleme_orani"] = belge_guncelleme_orani
    if guncel_belge_tutari is not None:
        params["guncel_belge_tutari"] = guncel_belge_tutari
    if son_5_15_yil:
        params["son_5_15_yil"] = son_5_15_yil

    return guncel_belge_tutari, aciklama_list, format_currency(guncel_belge_tutari) 