import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from google import genai
from google.genai import types
from dotenv import load_dotenv

from config import CONSELHOS_SCHEMA, SYSTEM_INSTRUCTION

load_dotenv()

app = Flask(__name__)
CORS(app)

def generate_bad_advice(situacao):
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY não foi configurada.")
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    conteudo_prompt = f"Me dê um conselho terrível para a seguinte situação: {situacao}"
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=conteudo_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=CONSELHOS_SCHEMA,
        )
    )
    return response.text

@app.route("/")
def root():
    return jsonify({
        "status": "success",
        "message": "API Aconselhador do Caos funcionando!",
        "version": "1.0"
    }), 200

@app.route("/generate", methods=["POST", "OPTIONS"])
def generate():
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json()
    
    if not data or "situacao" not in data:
        return jsonify({
            "status": "error",
            "message": "Por favor, informe qual a sua 'situacao' para receber um conselho."
        }), 400
        
    situacao = data.get("situacao")
    
    if not len(str(situacao)) > 5:
        return jsonify({
            "status": "error",
            "message": "Sua situação é muito curta. Explique melhor o seu problema."
        }), 400
    
    try:
        conselho_json_string = generate_bad_advice(situacao)
        
        conselho_estruturado = json.loads(conselho_json_string)
        
        return jsonify({
            "status": "success",
            "ingredientes_enviados": situacao,
            "dados_receita": conselho_estruturado
        }), 200
        
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return jsonify({
                "status": "error",
                "message": "Limite de requisições atingido."
            }), 429
            
        return jsonify({
            "status": "error",
            "message": f"Erro: {error_msg}"
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
