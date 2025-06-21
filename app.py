from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import requests
import json
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
    prompt_template = """
قم بإنشاء دليل تعليمي تفاعلي يحتوي على:
1. عنوان للدرس
2. 5-7 خطوات واضحة ومحددة
3. لكل خطوة: عنوان، وصف مفصل، والإجراء المطلوب

اجعل كل خطوة واضحة ومحددة مع تحديد أين يضغط المستخدم بالضبط.

قدم النتيجة بصيغة JSON فقط بهذا التنسيق:
{{
  "title": "عنوان الدرس",
  "steps": [
    {{
      "title": "عنوان الخطوة",
      "description": "وصف مفصل للخطوة",
      "action": "الإجراء المطلوب",
      "element": "العنصر المراد الضغط عليه",
      "tip": "نصيحة إضافية",
      "x": 50,
      "y": 30
    }}
  ]
}}

الرجاء إرجاع JSON فقط بدون أي نص إضافي.
الموضوع: {user_query}
    """
    prompt = prompt_template.format(user_query=user_query)
    webhook_url = "https://call-center-production-334e.up.railway.app/webhook/b003b9fc-23a5-48f4-9094-d8d89bc1c2eb"
    try:
        response = requests.post(
            webhook_url,
            json={"prompt": prompt},
            timeout=20
        )
        print("📥 الرد القادم من الويب هوك:")
        print(response.text)
        response.raise_for_status()
        try:
            result = response.json()
            # إذا كان الرد يحتوي على مفتاح output
            if "output" in result:
                import re
                output_text = result["output"]
                # إزالة ```json و ```
                cleaned = re.sub(r"^```json\s*|```$", "", output_text.strip(), flags=re.MULTILINE)
                tutorial_json = json.loads(cleaned)
                result = tutorial_json
            # تحقق أن الرد يحتوي على title و steps
            if not ("title" in result and "steps" in result):
                return jsonify({"error": "الرد من المزود غير صحيح", "details": result}), 500
        except Exception:
            return jsonify({"error": "الرد من المزود ليس JSON صالح", "details": response.text}), 500
        return jsonify(result), 200
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": "فشل الاتصال بالويب هوك", "details": str(e)}), 500

# ✅ تشغيل الخادم مع إعدادات Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 بدء تشغيل الخادم على المنفذ {port}")
    app.run(host="0.0.0.0", port=port)