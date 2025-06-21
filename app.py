from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import google.generativeai as genai
import json
from dotenv import load_dotenv
import traceback
import google.api_core.exceptions

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

# ✅ تفعيل API Key مع التحقق من صحته
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ خطأ: مفتاح Gemini API غير موجود في ملف .env")
genai.configure(api_key=api_key)

# ✅ مسار توليد الدروس التعليمية
@app.route("/generate-tutorial", methods=["POST"])
def generate_tutorial():
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "استعلام المستخدم مطلوب"}), 400

    user_query = data["query"]
    print(f"🔵 بدأ توليد درس لـ: {user_query}")

    model = genai.GenerativeModel("gemini-1.5-pro")

    prompt = f"""
قم بإنشاء دليل تعليمي تفاعلي باللغة العربية يحتوي على:
1. عنوان للدرس
2. 5 خطوات واضحة ومحددة
3. لكل خطوة: عنوان، وصف مفصل، والإجراء المطلوب

الرجاء إرجاع النتيجة بتنسيق JSON فقط بدون أي نص إضافي.

### تنسيق JSON المطلوب:
{{
  "title": "عنوان الدرس",
  "steps": [
    {{
      "title": "عنوان الخطوة",
      "description": "وصف مفصل للخطوة",
      "action": "الإجراء المطلوب",
      "element": "العنصر المراد التفاعل معه",
      "tip": "نصيحة إضافية",
      "x": 50,
      "y": 50
    }}
  ]
}}

### الموضوع المطلوب:
{user_query}
    """

    try:
        response = model.generate_content(
            prompt,
            request_options={"timeout": 15}
        )
        
        # التحقق من وجود استجابة صالحة
        if not response or not response.text:
            raise ValueError("استجابة فارغة من Gemini API")
            
        # معالجة الاستجابة بشكل آمن
        response_text = response.text.strip()
        
        # محاولة تحليل JSON مباشرة
        try:
            json_data = json.loads(response_text)
            return jsonify(json_data)
        except json.JSONDecodeError:
            # إذا فشل التحليل، حاول استخراج JSON من النص
            try:
                json_start = response_text.index('{')
                json_end = response_text.rindex('}') + 1
                json_str = response_text[json_start:json_end]
                json_data = json.loads(json_str)
                return jsonify(json_data)
            except Exception as e:
                return jsonify({
                    "error": "فشل في تحليل الاستجابة",
                    "message": str(e),
                    "response": response_text[:500] + "..." if len(response_text) > 500 else response_text
                }), 500
                
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"❌ خطأ عام في توليد الدرس:\n{error_trace}")
        return jsonify({
            "error": "فشل في توليد الدرس التعليمي",
            "message": str(e)
        }), 500

# ✅ تشغيل الخادم مع إعدادات Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 بدء تشغيل الخادم على المنفذ {port}")
    app.run(host="0.0.0.0", port=port)