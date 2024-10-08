import json
import logging
from flask import Flask, request, jsonify
import requests

# Configuração do Logger (mesma lógica)
class AzureJsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'category': 'WebhookLogs',  # Update with your log category
            'operationName': 'WebhookRequest',  # Update with your operation name
            'resourceId': '/subscriptions/<subscription_id>/resourceGroups/<resource_group>/providers/Microsoft.Web/sites/<site_name>',  # Update with your resource ID
            'level': record.levelname,
            'message': record.getMessage()
        }
        return json.dumps(data)

formatter = AzureJsonFormatter(datefmt='%Y-%m-%dT%H:%M:%S.%fZ')

logging.basicConfig(
    filename='webhook_logs.txt',  # Nome do arquivo de log (na mesma pasta do .py)
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'  # Formato da mensagem de log
)

app = Flask(__name__)

# URL base de destino
BASE_TARGET_URL = "https://devi-sandbox.azurewebsites.net/api/webhooks/incoming/omie/"

@app.route('/api/webhooks/incoming/omie/<path:webhook_id>', methods=['POST'])
def handle_webhook(webhook_id):
    app.logger.handlers[0].setFormatter(formatter)
    app.logger.info(json.dumps({'message': f"Requisição recebida em {request.url} com webhook_id: {webhook_id}"}))

    try:
        data = request.get_json()
    except json.JSONDecodeError as e:
        app.logger.error(json.dumps({'message': f"Erro ao decodificar JSON: {e}"}))
        return jsonify({"error": "Invalid JSON data"}), 400

    app.logger.info(json.dumps({'message': f"Dados recebidos: {data}"}))

    # Define um valor padrão para 'topic'
    topic = "Tópico não informado"  

    try:
        data = request.get_json()
        # Agora você pode sobrescrever o valor padrão de 'topic' se ele existir no JSON
        topic = data.get("topic", topic)  
    except json.JSONDecodeError as e:
        app.logger.error(json.dumps({'message': f"Erro ao decodificar JSON: {e}"}))
        return jsonify({"error": "Invalid JSON data"}), 400

    # Construção da URL de destino com o webhook_id
    target_url = BASE_TARGET_URL + webhook_id

    try:
        response = requests.post(target_url, json=data, timeout=600)  # Timeout de 600 segundos (10 minutos)
        app.logger.debug(f"Resposta da requisição: {response.status_code} - {response.text}")
    except requests.Timeout:
        app.logger.error("Tempo limite excedido na requisição.")
        return jsonify({"error": "Request timeout"}), 504
    except requests.RequestException as e:
        app.logger.error(f"Erro ao enviar requisição: {e}")
        return jsonify({"error": "Internal server error"}), 500

    # Retorna o endereço reenviado e o tópico
    return jsonify({"reenviado_para": target_url, "topico": topic}), 200 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)