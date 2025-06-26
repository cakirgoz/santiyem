from flask import Flask, render_template, request, session, , send_from_directory
from datetime import date
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'


# Session başlatma yardımcı fonksiyonu
def init_session():
    if 'data' not in session:
        session['data'] = []
    if 'calculated_amount' not in session:
        session['calculated_amount'] = None
    if 'counter' not in session:
        session['counter'] = 0
    if 'document_amount' not in session:
        session['document_amount'] = ''
    if 'experience_type' not in session:
        session['experience_type'] = 'EKAP İş Deneyim Belgesi Ekle'
    # Yapı izin belgesi için ek session değişkenleri
    if 'is_industrial' not in session:
        session['is_industrial'] = 'Hayır'
    if 'year_category' not in session:
        session['year_category'] = '2019 Öncesi'


@app.route('/')
def index():
    init_session()
    return render_template(
        'index.html',
        today=date.today().strftime("%Y-%m-%d"),
        experience_type=session['experience_type']
    )


# Form gönderimi için endpoint
@app.route('/submit', methods=['POST'])
def submit_form():
    # Form verilerini al
    experience_type = request.form.get('experience_type')
    application_date = request.form.get('application_date')
    graduation_date = request.form.get('graduation_date')
    graduation_department = request.form.get('graduation_department')
    has_experience_certificate = request.form.get('has_experience_certificate') == 'on'

    # Burada verileri işle (örneğin session'a kaydet)
    # ...

    # Basit bir yanıt döndür
    return f"<div class='p-4 bg-green-100 text-green-700 rounded'>Form başarıyla gönderildi! Deneyim Türü: {experience_type}</div>"


# @app.route('/graduation-fields', methods=['GET'])
# def graduation_fields():
#     try:
#         experience_type = request.args.get('experience_type')
#         if experience_type:
#             session['experience_type'] = experience_type
#             if experience_type == "Mezuniyet Belgesi Ekle":
#                 return render_template('graduation_fields.html')
#             elif experience_type == "Yapı Kullanma İzin Belgesi Ekle":
#                 return render_template('building_permit_fields.html')
#         return ""
#     except Exception as e:
#         return f"Hata: {str(e)}", 500


# Yapı izin belgesi için sanayi tipi seçimi endpoint'i
@app.route('/industrial-type-fields', methods=['GET'])
def industrial_type_fields():
    is_industrial = request.args.get('is_industrial')
    year_category = request.args.get('year_category', '2019 Öncesi')
    return render_template('industrial_type_fields.html',
                           is_industrial=is_industrial,
                           year_category=year_category)


# Yapı izin belgesi hesaplama endpoint'i
@app.route('/calculate-building-permit', methods=['POST'])
def calculate_building_permit():
    # Form verilerini al
    data = request.form

    # Burada hesaplama mantığınızı uygulayın
    # Örnek olarak basit bir mesaj döndürüyoruz
    result = f"Yapı Alanı: {data['building_area']} m² için hesaplama yapıldı"

    return f"<div class='p-4 bg-green-100 text-green-700 rounded'>{result}</div>"


@app.route('/graduation-fields', methods=['GET'])
def graduation_fields():
    try:
        experience_type = request.args.get('experience_type')
        if experience_type:
            session['experience_type'] = experience_type
            if experience_type == "Mezuniyet Belgesi Ekle":
                return render_template('graduation_fields.html')
            elif experience_type == "Yapı Kullanma İzin Belgesi Ekle":
                return render_template('building_permit_fields.html')
            elif experience_type == "EKAP İş Deneyim Belgesi Ekle":
                return render_template('ekap_fields.html')  # Yeni template
        return ""
    except Exception as e:
        return f"Hata: {str(e)}", 500

# EKAP için sanayi tipi seçimi endpoint'i
@app.route('/industrial-type-fields-ekap', methods=['GET'])
def industrial_type_fields_ekap():
    return render_template('industrial_type_fields_ekap.html')

# EKAP için detay alanları endpoint'i
@app.route('/industrial-type-fields-ekap-details', methods=['GET'])
def industrial_type_fields_ekap_details():
    year_category = request.args.get('year_category')
    return render_template(
        'industrial_type_fields_ekap_details.html',
        year_category=year_category
    )

@app.route('/ads.txt')
def ads():
    return send_from_directory('.', 'ads.txt')

if __name__ == '__main__':
    app.run(debug=True)
