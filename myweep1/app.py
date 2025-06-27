from flask import Flask, request, jsonify
from flask_cors import CORS
import whois
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

app = Flask(__name__)
# Barcha manbalardan CORSga ruxsat berish
CORS(app)

@app.route('/')
def home():
    return "Backend is running! Use /analyze endpoint for website analysis."

@app.route('/analyze', methods=['POST'])
def analyze_website():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL not provided"}), 400

    try:
        # URLni tozalash va domen nomini ajratib olish
        parsed_url = urlparse(url)
        domain = parsed_url.hostname
        if not domain:
            return jsonify({"error": "Invalid URL format"}), 400

        # WHOIS ma'lumotlarini olish
        whois_info = {}
        try:
            # whois.whois() ni to'g'ri chaqirish
            w = whois.whois(domain)
            whois_info = {
                "domain_name": w.domain_name,
                "registrar": w.registrar,
                "creation_date": w.creation_date,
                "expiration_date": w.expiration_date,
                "updated_date": w.updated_date,
                "name_servers": w.name_servers,
                "status": w.status,
                "emails": w.emails,
                "org": w.org,
                "country": w.country
            }
            # Listlarni stringga aylantirish (JSONga moslashish uchun)
            for key, value in whois_info.items():
                if isinstance(value, list):
                    whois_info[key] = ", ".join(map(str, value))
                elif isinstance(value, (type(None),)): # None bo'lsa bo'sh string
                    whois_info[key] = "N/A"

        except whois.parser.PywhoisError as e:
            whois_info = {"error": f"WHOIS error for {domain}: {e}"}
            print(f"WHOIS parser error: {e}")
        except Exception as e:
            whois_info = {"error": f"An unexpected WHOIS error occurred for {domain}: {e}"}
            print(f"General WHOIS error: {e}")

        # Sayt sarlavhasini olish (oddiy veb-skreping misoli)
        title = "N/A"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status() # HTTP xatolar uchun
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
        except requests.exceptions.RequestException as e:
            title = f"Could not fetch title: {e}"
        except Exception as e:
            title = f"Error parsing title: {e}"

        return jsonify({
            "status": "success",
            "requested_url": url,
            "domain": domain,
            "whois_data": whois_info,
            "page_title": title,
            # Qo'shimcha ma'lumotlar bu yerga qo'shilishi mumkin
        })

    except Exception as e:
        print(f"Analysis error: {e}")
        return jsonify({"error": f"An error occurred during analysis: {e}"}), 500

if __name__ == '__main__':
    # Debug rejimida ishga tushirish (faqat rivojlanish uchun)
    app.run(debug=True, port=5000)
    # Debugni o'chirib, hostni belgilash (deployment uchun)
    # app.run(host='0.0.0.0', port=5000, debug=False)