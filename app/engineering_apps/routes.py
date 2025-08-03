from flask import render_template, request, render_template_string, jsonify
from . import engineering_apps
from datetime import datetime
import os
from .calculations.mezuniyet import mezuniyet_guncelle
from .calculations.yapi_kullanma import build_yapi_kullanma_input_dict, validate_building_permit_inputs, calculate_building_permit
from .calculations.ekap import build_ekap_input_dict, calculate_ekap_amount
from .calculations.is_deneyimi_degerlendirme import calculate_is_deneyimi_degerlendirme
import json

def is_htmx_request():
    return 'HX-Request' in request.headers

@engineering_apps.route('/category1')
def category1():
    template = 'engineering_apps/category1.html' if is_htmx_request() else 'engineering_apps/pages/category1.html'
    # Bugünün tarihi YYYY-MM-DD formatında
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template(template, current_date=current_date)

@engineering_apps.route('/category2')
def category2():
    template = 'engineering_apps/category2.html' if is_htmx_request() else 'engineering_apps/pages/category2.html'
    return render_template(template)

@engineering_apps.route('/category3')
def category3():
    template = 'engineering_apps/category3.html' if is_htmx_request() else 'engineering_apps/pages/category3.html'
    return render_template(template)

@engineering_apps.route('/category4')
def category4():
    template = 'engineering_apps/category4.html' if is_htmx_request() else 'engineering_apps/pages/category4.html'
    return render_template(template)

@engineering_apps.route('/calculate-graduation', methods=['POST'])
def calculate_graduation():
    app_date_str = request.form.get('application_date')
    grad_date_str = request.form.get('graduation_date')
    grad_dept = request.form.get('graduation_department')
    has_experience_cert = request.form.get('has_experience_certificate') == 'on'
    mezuniyet_tutar_json_path = os.path.join(os.path.dirname(__file__), 'data', 'mezuniyet_tutar.json')

    # Boş alan kontrolü
    missing_fields = []
    if not app_date_str:
        missing_fields.append('Başvuru tarihi')
    if not grad_date_str:
        missing_fields.append('Mezuniyet tarihi')
    if not grad_dept:
        missing_fields.append('Mezun olunan bölüm')
    if missing_fields:
        return render_template_string('<div class="alert alert-danger">Lütfen tüm alanları doldurun: ' + ', '.join(missing_fields) + '</div>')

    # Diğer Bölümler kontrolü
    if grad_dept == 'Diğer Bölümler':
        return render_template_string('<div class="alert alert-danger">Yönetmeliğin 13/2/a hükmü uyarınca: Mezuniyet belgeleri bakımından inşaat mühendisliği ve mimarlık bölümleri benzer iş grubuna denk sayılır. İnşaat mühendisliği ve mimarlık bölümleri haricinde mezuniyet belgesi iş deneyimi olarak dikkate alınmaz.</div>')

    # Tarih formatı kontrolü
    try:
        # Başvuru tarihi: YYYY-MM-DD formatı bekleniyor (type=date input)
        app_date = datetime.strptime(app_date_str, '%Y-%m-%d').date()
    except Exception:
        return render_template_string('<div class="alert alert-danger">Başvuru tarihi formatı hatalı!</div>')
    try:
        grad_date = datetime.strptime(grad_date_str, '%Y-%m-%d').date()
    except Exception:
        return render_template_string('<div class="alert alert-danger">Mezuniyet tarihi formatı hatalı!</div>')

    # Başvuru tarihi mezuniyet tarihinden büyük olmalı
    if app_date <= grad_date:
        return render_template_string('<div class="alert alert-danger">Başvuru tarihi mezuniyet tarihinden büyük olmalıdır.</div>')

    # 03.10.2020 öncesi başvurular için hata
    if app_date < datetime.strptime('03.10.2020', '%d.%m.%Y').date():
        return render_template_string('<div class="alert alert-danger">Mezuniyet Belgesi ile İş Deneyim Tutarı Hesabı 03.10.2020 ve sonrası başvurular için yapılmaktadır.</div>')

    # Hesaplama
    tutar, detay = mezuniyet_guncelle(app_date, grad_date, mezuniyet_tutar_json_path, has_experience_cert)
    if not detay:
        return render_template_string('<div class="alert alert-danger">Başvuru tarihi için yıllık tutar bulunamadı!</div>')

    detay_html = f"""
    <ul class='mb-0'>
        <li>Yıllar: <b>{detay['yillar']}</b></li>
        <li>Aylar: <b>{detay['aylar']}</b></li>
        <li>Günler: <b>{detay['gunler']}</b></li>
        <li>Yıllık Tutar: <b>{detay['yillik_tutar']:,} TL</b></li>
    </ul>
    """
    return render_template_string(f'''
        <div class="alert alert-success">Hesaplanan Tutar: <b>{tutar:,} TL</b></div>
        <div class="card card-body mt-2"><b>Hesaplama Detayları:</b>{detay_html}</div>
    ''')

@engineering_apps.route('/calculate-building-permit', methods=['POST'])
def calculate_building_permit_route():
    """
    Yapı Kullanma İzin Belgesi hesaplama endpoint'i
    """
    # Form verilerini al
    application_date = request.form.get('application_date')
    contract_date = request.form.get('contract_date')
    acceptance_date = request.form.get('acceptance_date')
    building_class = request.form.get('building_class')
    building_class_application_date = request.form.get('building_class_application_date')
    building_area = request.form.get('building_area')
    completion_percentage = request.form.get('completion_percentage')
    teblig_sinir_tarih_opsiyonu = request.form.get('teblig_sinir_tarih_opsiyonu')
    is_industrial = request.form.get('is_industrial')
    year_category = request.form.get('year_category')
    percentage_selected = request.form.get('percentage_selected') == 'on'
    approval_date = request.form.get('approval_date')
    authority_group = request.form.get('authority_group')
    green_building = request.form.get('green_building') == 'on'
    industrial_type = request.form.get('industrial_type')
    tarih_opsiyonu = request.form.get('tarih_opsiyonu')

    # Parametreleri dictionary olarak oluştur
    params = build_yapi_kullanma_input_dict(
        application_date=application_date,
        contract_date=contract_date,
        acceptance_date=acceptance_date,
        building_class=building_class,
        building_class_application_date=building_class_application_date,
        building_area=building_area,
        completion_percentage=completion_percentage,
        teblig_sinir_tarih_opsiyonu=teblig_sinir_tarih_opsiyonu,
        is_industrial=is_industrial,
        year_category=year_category,
        percentage_selected=percentage_selected,
        approval_date=approval_date,
        authority_group=authority_group,
        green_building=green_building,
        industrial_type=industrial_type,
        tarih_opsiyonu=tarih_opsiyonu
    )

    # Doğrulama yap
    errors = validate_building_permit_inputs(params)
    if errors:
        return render_template_string('''
            <div class="alert alert-danger">
                <b>Lütfen aşağıdaki hataları düzeltin:</b>
                <ul class="mb-0">
                {% for err in errors %}<li>{{ err }}</li>{% endfor %}
                </ul>
            </div>
        ''', errors=errors)

    # Hesaplama yap
    try:
        result = calculate_building_permit(params)
        if result['success']:
            params_pretty = json.dumps(params, indent=4, ensure_ascii=False, default=str)
            print(f"DEBUG: son_5_15_yil = {result['details']['son_5_15_yil']}")
            return render_template_string('''
                <div class="alert alert-success">Güncel Belge Tutarı: <b>{{ result['formatted_amount'] }}</b></div>
                <div class="card card-body mt-2">
                    <b>Hesaplama Detayları:</b>
                    <ul class="mb-0">
                        <li>Yapı Alanı: <b>{{ result['details']['building_area'] }} m²</b></li>
                        <li>Tamamlanma Yüzdesi: <b>{{ result['details']['completion_percentage'] }}%</b></li>
                        <li>Güncellenmemiş Belge Tutarı: <b>{{ "{:,.2f}".format(result['details']['base_amount']).replace(',', 'X').replace('.', ',').replace('X', '.') }} TL</b></li>
                        <li>Güncellemeye Esas Belge Tutarı: <b>{{ "{:,.2f}".format(result['details']['contractor_base_amount']).replace(',', 'X').replace('.', ',').replace('X', '.') }} TL</b></li>
                        <li>Güncel Belge Tutarı: <b>{{ "{:,.2f}".format(result['details']['updated_contractor_amount']).replace(',', 'X').replace('.', ',').replace('X', '.') }} TL</b></li>
                        <li>Sözleşme Tarihi Birim Fiyatı: <b>{{ "{:,.2f}".format(result['details']['unit_price_contract']).replace(',', 'X').replace('.', ',').replace('X', '.') }} TL/m²</b></li>
                        <li>Başvuru Tarihi Birim Fiyatı: <b>{{ "{:,.2f}".format(result['details']['unit_price_application']).replace(',', 'X').replace('.', ',').replace('X', '.') }} TL/m²</b></li>
                        <li>Birim Fiyat Oranı: <b>{{ "%.4f"|format(result['details']['unit_price_ratio']) }}</b></li>
                        <li>Ruhsata Esas Birim Fiyatı: <b>{{ "{:,.2f}".format(result['details']['unit_price_contract_ruhsata_esas']).replace(',', 'X').replace('.', ',').replace('X', '.') }} TL/m²</b></li>
                        <li>Sözleşme Tarihi Önceki Ay: <b>{{ result['details']['contract_previous_month']['year'] }}-{{ "%02d"|format(result['details']['contract_previous_month']['month']) }}</b></li>
                        <li>Başvuru Tarihi Önceki Ay: <b>{{ result['details']['application_previous_month']['year'] }}-{{ "%02d"|format(result['details']['application_previous_month']['month']) }}</b></li>
                        <li>Sözleşme Dönemi ÜFE Endeksi: <b>{{ "%.2f"|format(result['details']['ufe_contract']) }}</b></li>
                        <li>Başvuru Dönemi ÜFE Endeksi: <b>{{ "%.2f"|format(result['details']['ufe_application']) }}</b></li>
                        <li>ÜFE Güncelleme Oranı: <b>{{ "%.4f"|format(result['details']['ufe_update_ratio']) }}</b></li>
                        <li>Belge Güncelleme Oranı: <b>{{ "%.4f"|format(result['details']['document_update_ratio']) }}</b></li>
                        <li>Yeşil Bina Katsayısı: <b>{{ "%.2f"|format(result['details']['green_building_factor']) }}</b></li>
                        <li>Son 5 yıl/Son 15 Yıl: <b>{{ result['details']['son_5_15_yil'] }}</b></li>
                        {% if result['details'].get('max_industrial_amount') %}
                        <li>Maksimum Sanayi Tutarı: <b>{{ "{:,.2f}".format(result['details']['max_industrial_amount']).replace(',', 'X').replace('.', ',').replace('X', '.') }} TL</b></li>
                        {% endif %}
                    </ul>
                </div>
                <div class="mt-3">
                    <button class="btn btn-outline-secondary btn-sm" type="button" data-toggle="collapse" data-target="#paramsCollapse" aria-expanded="false" aria-controls="paramsCollapse">
                        🧮 Hesaplama Parametrelerini Göster
                    </button>
                    <div class="collapse mt-2" id="paramsCollapse">
                        <div class="card card-body p-2 bg-light border">
                            <b>📄 Hesap Parametreleri</b>
                            <pre class="mb-0"><code class="json">{{ params_pretty }}</code></pre>
                        </div>
                    </div>
                </div>
            ''', result=result, params_pretty=params_pretty)
        else:
            return render_template_string('<div class="alert alert-danger">{{ result["error"] }}</div>', result=result)
    except Exception as e:
        return render_template_string(f'<div class="alert alert-danger">Hesaplama hatası: {str(e)}</div>')

@engineering_apps.route('/calculate-ekap-experience', methods=['POST'])
def calculate_ekap_experience():
    """
    EKAP İş Deneyim Belgesi hesaplama endpoint'i (gelişmiş)
    """
    # Dictionary oluştur
    params = build_ekap_input_dict(request.form)
    # Hesaplama
    try:
        guncel_belge_tutari, aciklama_list, formatted_guncel_belge_tutari = calculate_ekap_amount(params)
    except Exception as e:
        return render_template_string(f'<div class="alert alert-danger">{str(e)}</div>')
    params_pretty = json.dumps(params, indent=4, ensure_ascii=False, default=str)
    return render_template_string('''
        <div class="alert alert-success">Güncel Belge Tutarı: <b>{{ formatted_guncel_belge_tutari }}</b></div>
        <div class="card card-body mt-2">
            <b>Hesaplama Detayları:</b>
            <ul class="mb-0">
            {% for aciklama in aciklama_list %}
                <li>{{ aciklama }}</li>
            {% endfor %}
            </ul>
        </div>
        <div class="mt-3">
            <button class="btn btn-outline-secondary btn-sm" type="button" data-toggle="collapse" data-target="#ekapParamsCollapse" aria-expanded="false" aria-controls="ekapParamsCollapse">
                🧮 Hesaplama Parametrelerini Göster
            </button>
            <div class="collapse mt-2" id="ekapParamsCollapse">
                <div class="card card-body p-2 bg-light border">
                    <b>📄 Hesap Parametreleri</b>
                    <pre class="mb-0"><code class="json">{{ params_pretty }}</code></pre>
                </div>
            </div>
        </div>
        <div class="mt-3">
            <button type="button" class="btn btn-success" id="ekap-tabloya-ekle-btn">Tabloya Ekle</button>
        </div>
    ''', formatted_guncel_belge_tutari=formatted_guncel_belge_tutari, aciklama_list=aciklama_list, params=params, params_pretty=params_pretty)

@engineering_apps.route('/calculate-is-deneyimi-degerlendirme', methods=['POST'])
def calculate_is_deneyimi_degerlendirme_route():
    """
    İş Deneyimi Değerlendirme hesaplama endpoint'i
    """
    print("DEBUG: calculate_is_deneyimi_degerlendirme_route called")
    
    # Form verilerini al
    application_date = request.form.get('application_date')
    tarih_opsiyonu = request.form.get('is_deneyimi_teblig_sinir_tarih_opsiyonu')
    
    # localStorage'dan tablo verilerini al (frontend'den gönderilecek)
    belgeler_json = request.form.get('belgeler', '[]')
    try:
        belgeler = json.loads(belgeler_json)
    except Exception:
        belgeler = []
    
    print(f"DEBUG: application_date: {application_date}")
    print(f"DEBUG: tarih_opsiyonu: {tarih_opsiyonu}")
    print(f"DEBUG: belgeler count: {len(belgeler)}")
    
    if not belgeler:
        return render_template_string('<div class="alert alert-danger">Tabloda iş deneyim belgesi bulunamadı.</div>')
    
    # Hesaplama yap
    try:
        result = calculate_is_deneyimi_degerlendirme(belgeler, application_date, tarih_opsiyonu)
        print(f"DEBUG: calculation result success: {result.get('success')}")
        
        if result['success']:
            # Dictionary oluştur
            params = {
                "application_date": application_date,
                "tarih_opsiyonu": tarih_opsiyonu,
                "mezuniyet_tutari": result.get("mezuniyet_tutari"),
                "en_buyuk_is_deneyimi": result.get("en_buyuk_is_deneyimi"),
                "en_buyuk_2_kat": result.get("en_buyuk_2_kat"),
                "en_buyuk_3_kat": result.get("en_buyuk_3_kat"),
                "son_5_yil_toplam": result.get("son_5_yil_toplam"),
                "esas_belge_tutari": result.get("esas_belge_tutari"),
                "belge_sinifi": result.get("belge_sinifi"),
                "period_data": result.get("period_data")
            }
            params_pretty = json.dumps(params, indent=4, ensure_ascii=False, default=str)
            
            print("DEBUG: Returning HTML response")
            return render_template_string('''
                <div class="alert alert-info">
                    <h5>Hesaplama Sonuçları</h5>
                    <div class="row">
                        <div class="col-md-6">
                            <strong>Mezuniyet Belgesi Tutarı:</strong><br>
                            {% if params.mezuniyet_tutari %}
                                {{ "{:,.2f}".format(params.mezuniyet_tutari).replace(",", "X").replace(".", ",").replace("X", ".") }} TL
                            {% else %}
                                N/A
                            {% endif %}
                        </div>
                        <div class="col-md-6">
                            <strong>Son 5/15 Yıldaki En Büyük İş Deneyimi:</strong><br>
                            {% if params.en_buyuk_is_deneyimi %}
                                {{ "{:,.2f}".format(params.en_buyuk_is_deneyimi).replace(",", "X").replace(".", ",").replace("X", ".") }} TL
                            {% else %}
                                N/A
                            {% endif %}
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-md-6">
                            <strong>Son 5/15 Yıldaki En Büyük İş Deneyiminin İki Katı:</strong><br>
                            {% if params.en_buyuk_2_kat %}
                                {{ "{:,.2f}".format(params.en_buyuk_2_kat).replace(",", "X").replace(".", ",").replace("X", ".") }} TL
                            {% else %}
                                N/A
                            {% endif %}
                        </div>
                        <div class="col-md-6">
                            <strong>Son 5/15 Yıldaki En Büyük İş Deneyiminin Üç Katı:</strong><br>
                            {% if params.en_buyuk_3_kat %}
                                {{ "{:,.2f}".format(params.en_buyuk_3_kat).replace(",", "X").replace(".", ",").replace("X", ".") }} TL
                            {% else %}
                                N/A
                            {% endif %}
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-md-6">
                            <strong>Son Beş Yıldaki İş Deneyimlerinin Toplamı:</strong><br>
                            {% if params.son_5_yil_toplam %}
                                {{ "{:,.2f}".format(params.son_5_yil_toplam).replace(",", "X").replace(".", ",").replace("X", ".") }} TL
                            {% else %}
                                N/A
                            {% endif %}
                        </div>
                        <div class="col-md-6">
                            <strong>İş Deneyiminin Belirlenmesine Esas Belge Tutarı:</strong><br>
                            {{ "{:,.2f}".format(params.esas_belge_tutari).replace(",", "X").replace(".", ",").replace("X", ".") }} TL
                        </div>
                    </div>
                </div>
                <div class="alert alert-success text-center" style="font-size: 1.5em; font-weight: bold;">
                    <h4>Belge Sınıfı: {{ params.belge_sinifi }}</h4>
                </div>
                <div class="mt-3">
                    <button class="btn btn-outline-secondary btn-sm" type="button" data-toggle="collapse" data-target="#isDeneyimiParamsCollapse" aria-expanded="false" aria-controls="isDeneyimiParamsCollapse">
                        🧮 Hesaplama Parametrelerini Göster
                    </button>
                    <div class="collapse mt-2" id="isDeneyimiParamsCollapse">
                        <div class="card card-body p-2 bg-light border">
                            <b>📄 Hesap Parametreleri</b>
                            <pre class="mb-0"><code class="json">{{ params_pretty }}</code></pre>
                        </div>
                    </div>
                </div>
            ''', params=params, params_pretty=params_pretty)
        else:
            return render_template_string('<div class="alert alert-danger">{{ result["error"] }}</div>', result=result)
    except Exception as e:
        print(f"DEBUG: Exception in calculation: {e}")
        return render_template_string(f'<div class="alert alert-danger">Hesaplama hatası: {str(e)}</div>')
