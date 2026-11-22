import os
from flask import Flask, jsonify, render_template_string, request
from openai import OpenAI

app = Flask(__name__)

# Render के Environment Variables से OPENAI_API_KEY पढ़ना
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

PAGE = """<!DOCTYPE html>
<html lang="hi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>NEXA A2A</title>
  <style>
    * { box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; }
    body { margin: 0; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; min-height: 100vh; }
    .app { width: 100%; max-width: 720px; display: flex; flex-direction: column; padding: 16px; gap: 12px; }
    header { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 12px 16px; border-radius: 12px; }
    header h1 { margin: 0; font-size: 1.15rem; }
    .status { font-size: 0.85rem; color: #94a3b8; }
    .chat-box { flex: 1; background: #1e293b; border-radius: 12px; padding: 14px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; min-height: 360px; max-height: 65vh; }
    .msg { padding: 10px 14px; border-radius: 12px; max-width: 85%; line-height: 1.5; white-space: pre-wrap; word-wrap: break-word; }
    .user { align-self: flex-end; background: #2563eb; color: #fff; }
    .bot { align-self: flex-start; background: #334155; color: #f1f5f9; }
    .controls { display: flex; gap: 8px; }
    input { flex: 1; padding: 12px 14px; border-radius: 10px; border: 1px solid #475569; background: #0f172a; color: #fff; font-size: 1rem; }
    button { padding: 12px 16px; border-radius: 10px; border: none; background: #22c55e; color: #052e16; font-weight: 600; cursor: pointer; }
    button.mic { background: #f59e0b; color: #1c1917; }
    button:disabled { opacity: 0.6; cursor: not-allowed; }
  </style>
</head>
<body>
  <div class="app">
    <header>
      <h1>NEXA A2A</h1>
      <div id="statusText" class="status">तैयार</div>
    </header>

    <div id="chatBox" class="chat-box">
      <div class="msg bot">नमस्ते! मैं NEXA A2A हूँ। आप लिखकर या माइक से बोलकर सवाल पूछ सकते हैं।</div>
    </div>

    <div class="controls">
      <input id="userInput" type="text" placeholder="यहाँ अपना सवाल लिखें..." autocomplete="off" />
      <button id="micBtn" class="mic" type="button" title="बोलें">माइक</button>
      <button id="sendBtn" type="button">भेजें</button>
    </div>
  </div>

  <script>
    const chatBox = document.getElementById("chatBox");
    const input = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const micBtn = document.getElementById("micBtn");
    const statusText = document.getElementById("statusText");

    function addMessage(text, sender = "bot") {
      const div = document.createElement("div");
      div.className = `msg ${sender}`;
      div.textContent = text;
      chatBox.appendChild(div);
      chatBox.scrollTop = chatBox.scrollHeight;
    }

    function speakText(text) {
      if (!("speechSynthesis" in window)) return;
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = "hi-IN";
      window.speechSynthesis.speak(utter);
    }

    async function sendMessage() {
      const text = input.value.trim();
      if (!text) return;

      addMessage(text, "user");
      input.value = "";
      sendBtn.disabled = true;
      statusText.textContent = "सोच रहा हूँ...";

      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();

        if (!res.ok) {
          addMessage(data.error || "सर्वर से सही जवाब नहीं मिला।", "bot");
          statusText.textContent = "त्रुटि";
        } else {
          const reply = data.reply || "कोई उत्तर प्राप्त नहीं हुआ।";
          addMessage(reply, "bot");
          speakText(reply);
          statusText.textContent = "तैयार";
        }
      } catch (err) {
        addMessage("नेटवर्क या सर्वर से जुड़ने में समस्या आई।", "bot");
        statusText.textContent = "ऑफ़लाइन / त्रुटि";
      } finally {
        sendBtn.disabled = false;
        input.focus();
      }
    }

    sendBtn.addEventListener("click", sendMessage);
    input.addEventListener("keydown", function(e) {
      if (e.key === "Enter") sendMessage();
    });

    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    micBtn.addEventListener("click", function() {
      if (!Speech) {
        addMessage("आपके ब्राउज़र में Voice Recognition समर्थित नहीं है।", "bot");
        return;
      }

      const recognition = new Speech();
      recognition.lang = "hi-IN";
      recognition.interimResults = false;

      recognition.onstart = function() {
        statusText.textContent = "सुन रहा हूँ (बोलें)...";
      };

      recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        input.value = transcript;
        statusText.textContent = "तैयार";
        sendMessage();
      };

      recognition.onerror = function() {
        statusText.textContent = "माइक्रोफ़ोन की अनुमति या त्रुटि";
      };

      recognition.onend = function() {
        if (statusText.textContent === "सुन रहा हूँ (बोलें)...") {
          statusText.textContent = "तैयार";
        }
      };

      recognition.start();
    });
  </script>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(PAGE)


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "app": "NEXA A2A",
        "ai_configured": client is not None
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    if client is None:
        return jsonify({"error": "OPENAI_API_KEY Required"}), 503

    data = request.get_json(silent=True) or {}
    user_message = str(data.get("message", "")).strip()

    if not user_message:
        return jsonify({"error": "कृपया कोई संदेश या प्रश्न भेजें।"}), 400

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "system",
                    "content": "आप एक मददगार और स्पष्ट हिंदी सहायक हैं। सरल और सटीक उत्तर दें।"
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )
        reply_text = (response.output_text or "").strip()
        if not reply_text:
            reply_text = "मुझे उत्तर तैयार करने में समस्या आई, कृपया दोबारा प्रयास करें।"

        return jsonify({"reply": reply_text})

    except Exception as exc:
        return jsonify({"error": f"AI अनुरोध में त्रुटि: {str(exc)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

