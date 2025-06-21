from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import requests
from dotenv import load_dotenv
import traceback

# تحميل المتغيرات البيئية
load_dotenv()
print("ENV path:", os.path.abspath(".env"))
app = Flask(__name__)
CORS(app)

# ✅ عرض ملف index.html عند زيارة الجذر
@app.route("/")
def serve_index():
    return send_from_directory(".", "index.html")

# ✅ نقطة نهاية لـ favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# ✅ مسار توليد الدروس التعليمية
@app.route("/generate-tutorial", methods=["POST"])
def generate_tutorial():
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "استعلام المستخدم مطلوب"}), 400

    user_query = data["query"]
    print(f"🔵 إرسال الطلب إلى الويب هوك لـ: {user_query}")

    webhook_url = "https://call-center-production-334e.up.railway.app/webhook/b003b9fc-23a5-48f4-9094-d8d89bc1c2eb"
    payload = {"query": user_query}

    try:
        response = requests.post(webhook_url, json=payload, timeout=20)
        if response.status_code != 200:
            return jsonify({
                "error": "فشل في الاتصال بالويب هوك",
                "status_code": response.status_code,
                "response": response.text
            }), 500

        # محاولة تحليل JSON من الاستجابة
        try:
            json_data = response.json()
            return jsonify(json_data)
        except Exception as e:
            return jsonify({
                "error": "فشل في تحليل استجابة الويب هوك",
                "message": str(e),
                "response": response.text
            }), 500

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"❌ خطأ في إرسال الطلب للويب هوك:\n{error_trace}")
        return jsonify({
            "error": "فشل في إرسال الطلب للويب هوك",
            "message": str(e)
        }), 500

# ✅ تشغيل الخادم مع إعدادات Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 بدء تشغيل الخادم على المنفذ {port}")
    app.run(host="0.0.0.0", port=port)