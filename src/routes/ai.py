# src/routes/ai.py
from flask import Blueprint, jsonify, request, current_app
import json
import os
import re 
import requests # For making HTTP requests
from datetime import datetime
from src.models.models import db, Ingredient 

ai_bp = Blueprint('ai', __name__)

# --- Updated Fallback Model Lists ---
OPENROUTER_MODELS_FALLBACK = [
    {"id": "openai/gpt-4-turbo-preview", "name": "OpenAI: GPT-4 Turbo Preview (Fallback)"},
    {"id": "openai/gpt-4o", "name": "OpenAI: GPT-4o (Fallback)"},
    {"id": "anthropic/claude-3-opus-20240229", "name": "Anthropic: Claude 3 Opus (Fallback)"},
    {"id": "anthropic/claude-3-sonnet-20240229", "name": "Anthropic: Claude 3 Sonnet (Fallback)"},
    {"id": "google/gemini-2.5-flash-preview-05-20", "name": "Google: Gemini 1.5 Pro (Fallback via OR)"}, # OpenRouter ID
    {"id": "meta-llama/llama-3-70b-instruct", "name": "Meta: Llama 3 70B Instruct (Fallback)"}
]
GEMINI_MODELS_FALLBACK = [
    # Direct Google Gemini API model names
    {"id": "gemini-2.5-flash-preview-05-20", "name": "Gemini 2.5 Pro Latest"}, 
    {"id": "gemini-1.5-flash-latest", "name": "Gemini 1.5 Flash Latest"},
    # Adding Gemini 2.5 (Note: Exact API identifiers for "2.5" might vary upon official release for direct API)
    # For now, using hypothetical identifiers. Replace with actual ones when available.
    {"id": "gemini-2.5-pro-latest", "name": "Gemini 2.5 Pro Latest"}, # Placeholder
    {"id": "gemini-2.5-flash-latest", "name": "Gemini 2.5 Flash Latest"}, # Placeholder
    {"id": "gemini-pro", "name": "Gemini Pro (Vision Capable)"} 
]
CLAUDE_MODELS_FALLBACK = [
    {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
    {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"},
    {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"}
]

DEFAULT_PERFUMERY_PROMPTS = { 
    "openrouter": """You are an expert perfumer with decades of experience in scent creation and formulation. 
Your expertise includes knowledge of thousands of aromatic materials, their properties, interactions, and uses in perfumery.
You understand the chemistry of fragrance, the principles of composition, and the artistic aspects of perfume creation.
Help the user create, refine, and troubleshoot perfume formulas with precise, practical advice.
When discussing ingredients, provide information about:
- Odor profile and character
- Typical usage rates
- Common combinations and accords
- Potential substitutions
- Safety considerations and IFRA restrictions
When helping with formulations:
- Suggest balanced compositions
- Identify potential issues in formulas
- Recommend adjustments for specific effects
- Explain the technical reasoning behind your suggestions""",
    
    "gemini": """You are a perfumery assistant with extensive knowledge of fragrance creation.
Your purpose is to help perfumers develop new scents, understand ingredient interactions, and refine their formulas.
Provide detailed, accurate information about perfumery ingredients, techniques, and principles.
When analyzing formulas:
- Evaluate the balance of notes (top, middle, base)
- Identify potential aromatic conflicts
- Suggest modifications to achieve specific olfactory goals
- Consider longevity, projection, and overall harmony
When recommending ingredients:
- Specify appropriate concentration ranges
- Note any special handling requirements
- Mention alternative options when appropriate
- Address any safety or regulatory concerns""",
    
    "claude": """You are Claude, an AI assistant with specialized knowledge in perfumery and scent creation.
You help perfumers analyze ingredients, develop formulas, and understand scent profiles and interactions.
When assisting with perfume creation:
- Provide specific, actionable advice on ingredient selection and proportions
- Explain the olfactory impact of different materials and combinations
- Consider both technical aspects (volatility, solubility) and artistic elements
- Reference established perfumery principles and techniques
- Suggest modifications to achieve desired effects
- Address safety considerations and compliance with industry standards
Your responses should be precise, practical, and grounded in perfumery science and artistry."""
}

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SAVED_PROMPTS_FILE_DIR = os.path.join(PROJECT_ROOT, 'src', 'data')
SAVED_PROMPTS_FILE = os.path.join(SAVED_PROMPTS_FILE_DIR, 'saved_prompts.json')

if not os.path.exists(SAVED_PROMPTS_FILE_DIR):
    try:
        os.makedirs(SAVED_PROMPTS_FILE_DIR, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {SAVED_PROMPTS_FILE_DIR}: {e}")

if not os.path.exists(SAVED_PROMPTS_FILE):
    try:
        with open(SAVED_PROMPTS_FILE, 'w') as f: json.dump([], f)
    except IOError as e:
        print(f"Error creating saved prompts file {SAVED_PROMPTS_FILE}: {e}")

@ai_bp.route('/api/ai/models', methods=['GET'])
def get_ai_models_hardcoded():
    return jsonify({
        'openrouter': OPENROUTER_MODELS_FALLBACK,
        'gemini': GEMINI_MODELS_FALLBACK, # This list is now updated
        'claude': CLAUDE_MODELS_FALLBACK
    })

# --- Helper functions for actual API calls ---
def call_openrouter_api(api_key, model_id, messages, is_json_mode=False):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": current_app.config.get('SITE_URL', 'http://localhost:5000'), 
        "X-Title": current_app.config.get('APP_NAME', 'PerfumeryApp') 
    }
    payload = {"model": model_id, "messages": messages}
    if is_json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        data = response.json()
        if data.get("choices") and len(data["choices"]) > 0:
            content = data["choices"][0].get("message", {}).get("content")
            return content, None
        current_app.logger.warning(f"OpenRouter response missing choices or content: {data}")
        return None, "No content in OpenRouter response choices."
    except requests.exceptions.RequestException as e:
        error_detail = str(e)
        if e.response is not None:
            try: error_detail = e.response.json().get("error", {}).get("message", str(e.response.text))
            except ValueError: error_detail = e.response.text
        current_app.logger.error(f"OpenRouter API request error: {error_detail}")
        return None, f"OpenRouter API error: {error_detail}"
    except Exception as e:
        current_app.logger.error(f"Unexpected error calling OpenRouter: {str(e)}", exc_info=True)
        return None, f"Unexpected error with OpenRouter: {str(e)}"

def call_gemini_api(api_key, model_id, prompt_text, is_json_mode=False):
    # For direct Gemini API, model names are like 'gemini-1.5-pro-latest' or specific versions
    # If model_id comes with a prefix like 'google/', strip it for direct API.
    gemini_model_name = model_id.split('/')[-1] 
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    if is_json_mode:
        # For Gemini, if you need a JSON object specifically, you'd typically add instructions
        # in the prompt and then parse the text response.
        # However, some newer versions/endpoints might support responseMimeType.
        # Let's assume for now the prompt handles JSON output structure.
        # If a specific API version supports it:
        # payload["generationConfig"] = {"responseMimeType": "application/json"}
        pass # JSON mode primarily handled by prompt for Gemini text generation

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        data = response.json()

        # Check for blockReason first
        if data.get("candidates") and data["candidates"][0].get("finishReason") == "SAFETY":
            safety_ratings = data["candidates"][0].get("safetyRatings", [])
            block_reason_detail = "; ".join([f"{rating['category']}: {rating['probability']}" for rating in safety_ratings])
            current_app.logger.warning(f"Gemini content blocked due to safety reasons: {block_reason_detail}")
            return None, f"Content blocked by Gemini due to safety reasons: {block_reason_detail}"
        
        if data.get("candidates") and len(data["candidates"]) > 0:
            part = data["candidates"][0].get("content", {}).get("parts", [{}])[0]
            if "text" in part:
                return part["text"], None
        
        current_app.logger.warning(f"Gemini response missing candidates or text part: {data}")
        return None, "No text content in Gemini API response."
    except requests.exceptions.RequestException as e:
        error_detail = str(e)
        if e.response is not None:
            try: error_detail = e.response.json().get("error", {}).get("message", str(e.response.text))
            except ValueError: error_detail = e.response.text
        current_app.logger.error(f"Gemini API request error: {error_detail}")
        return None, f"Gemini API error: {error_detail}"
    except Exception as e:
        current_app.logger.error(f"Unexpected error calling Gemini: {str(e)}", exc_info=True)
        return None, f"Unexpected error with Gemini: {str(e)}"

def call_claude_api(api_key, model_id, messages, system_prompt=None):
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01", 
        "content-type": "application/json"
    }
    payload = {"model": model_id, "max_tokens": 4096, "messages": messages}
    if system_prompt: payload["system"] = system_prompt
    
    try:
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        data = response.json()
        if data.get("content") and len(data["content"]) > 0:
            text_content = "".join([block.get("text", "") for block in data["content"] if block.get("type") == "text"])
            return text_content, None
        current_app.logger.warning(f"Claude response missing content: {data}")
        return None, "No text content in Claude API response."
    except requests.exceptions.RequestException as e:
        error_detail = str(e)
        if e.response is not None:
            try: 
                err_data = e.response.json().get("error", {})
                error_detail = err_data.get("message", err_data.get("type", str(e.response.text)))
            except ValueError: error_detail = e.response.text
        current_app.logger.error(f"Claude API request error: {error_detail}")
        return None, f"Claude API error: {error_detail}"
    except Exception as e:
        current_app.logger.error(f"Unexpected error calling Claude: {str(e)}", exc_info=True)
        return None, f"Unexpected error with Claude: {str(e)}"

@ai_bp.route('/api/ai/fetch-service-models', methods=['POST'])
def fetch_service_models_endpoint():
    data = request.json
    service_name = data.get('service')
    api_key = data.get('api_key')

    if not service_name or not api_key:
        return jsonify({'error': 'Service name and API key are required.'}), 400

    current_app.logger.info(f"Fetching models for service: {service_name}, API Key Hint: {api_key[:4]}...")

    if service_name == 'openrouter':
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=30)
            response.raise_for_status()
            models_data = response.json().get('data', [])
            formatted_models = [{"id": m.get("id"), "name": m.get("name", m.get("id"))} for m in models_data if m.get("id")]
            return jsonify({'success': True, 'models': formatted_models if formatted_models else OPENROUTER_MODELS_FALLBACK})
        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            if e.response is not None:
                try: error_detail = e.response.json().get("error", {}).get("message", str(e.response.text))
                except ValueError: error_detail = e.response.text
            current_app.logger.error(f"Failed to fetch models from OpenRouter: {error_detail}")
            return jsonify({'error': f"Failed to fetch models from OpenRouter: {error_detail}. Using fallback list.", 'models': OPENROUTER_MODELS_FALLBACK}), 500
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred fetching OpenRouter models: {str(e)}", exc_info=True)
            return jsonify({'error': f"An unexpected error: {str(e)}. Using fallback list.", 'models': OPENROUTER_MODELS_FALLBACK}), 500
    
    elif service_name == 'gemini':
        current_app.logger.info("Returning known/fallback model list for Gemini.")
        return jsonify({'success': True, 'models': GEMINI_MODELS_FALLBACK, 'message': 'Using known model list for Gemini.'})

    elif service_name == 'claude':
        current_app.logger.info("Claude model listing is typically static; returning known/fallback models.")
        return jsonify({'success': True, 'models': CLAUDE_MODELS_FALLBACK, 'message': 'Using known model list for Claude.'})
    
    else:
        return jsonify({'error': f'Fetching models for service "{service_name}" is not supported yet.'}), 400


@ai_bp.route('/api/ai/default-prompts', methods=['GET'])
def get_default_prompts():
    return jsonify(DEFAULT_PERFUMERY_PROMPTS)

# --- Saved Prompts CRUD ---
@ai_bp.route('/api/ai/saved-prompts', methods=['GET'])
def get_saved_prompts():
    try:
        if not os.path.exists(SAVED_PROMPTS_FILE): 
            return jsonify([])
        with open(SAVED_PROMPTS_FILE, 'r') as f:
            saved_prompts = json.load(f)
        return jsonify(saved_prompts)
    except Exception as e:
        current_app.logger.error(f"Error reading saved prompts: {str(e)}")
        return jsonify({'error': f"Could not load saved prompts: {str(e)}"}), 500

@ai_bp.route('/api/ai/saved-prompts', methods=['POST'])
def save_prompt():
    data = request.json
    required_fields = ['name', 'service', 'model', 'system_prompt', 'user_prompt']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Field {field} is required'}), 400
    try:
        saved_prompts = []
        if os.path.exists(SAVED_PROMPTS_FILE):
            with open(SAVED_PROMPTS_FILE, 'r') as f:
                try:
                    saved_prompts = json.load(f)
                    if not isinstance(saved_prompts, list): 
                        saved_prompts = []
                except json.JSONDecodeError:
                    saved_prompts = [] 

        new_id = 1
        if saved_prompts:
            new_id = max(p.get('id', 0) for p in saved_prompts) + 1


        new_prompt = {
            'id': new_id,
            'name': data['name'],
            'service': data['service'],
            'model': data['model'],
            'system_prompt': data['system_prompt'],
            'user_prompt': data['user_prompt'],
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        saved_prompts.append(new_prompt)
        with open(SAVED_PROMPTS_FILE, 'w') as f:
            json.dump(saved_prompts, f, indent=2)
        return jsonify(new_prompt), 201
    except Exception as e:
        current_app.logger.error(f"Error saving prompt: {str(e)}")
        return jsonify({'error': f"Could not save prompt: {str(e)}"}), 500

@ai_bp.route('/api/ai/saved-prompts/<int:id>', methods=['PUT'])
def update_saved_prompt(id):
    data = request.json
    try:
        saved_prompts = []
        if os.path.exists(SAVED_PROMPTS_FILE):
            with open(SAVED_PROMPTS_FILE, 'r') as f:
                try:
                    saved_prompts = json.load(f)
                    if not isinstance(saved_prompts, list):
                         return jsonify({'error': 'Saved prompts data is corrupted.'}), 500
                except json.JSONDecodeError:
                     return jsonify({'error': 'Saved prompts data is corrupted (JSON decode error).'}), 500
        
        prompt_to_update = next((p for p in saved_prompts if p.get('id') == id), None)
        if not prompt_to_update:
            return jsonify({'error': 'Prompt not found'}), 404
        
        prompt_to_update['name'] = data.get('name', prompt_to_update['name'])
        prompt_to_update['service'] = data.get('service', prompt_to_update['service'])
        prompt_to_update['model'] = data.get('model', prompt_to_update['model'])
        prompt_to_update['system_prompt'] = data.get('system_prompt', prompt_to_update['system_prompt'])
        prompt_to_update['user_prompt'] = data.get('user_prompt', prompt_to_update['user_prompt'])
        prompt_to_update['updated_at'] = datetime.utcnow().isoformat()
        
        with open(SAVED_PROMPTS_FILE, 'w') as f:
            json.dump(saved_prompts, f, indent=2)
        return jsonify(prompt_to_update)
    except Exception as e:
        current_app.logger.error(f"Error updating prompt {id}: {str(e)}")
        return jsonify({'error': f"Could not update prompt: {str(e)}"}), 500

@ai_bp.route('/api/ai/saved-prompts/<int:id>', methods=['DELETE'])
def delete_saved_prompt(id):
    try:
        saved_prompts = []
        if os.path.exists(SAVED_PROMPTS_FILE):
            with open(SAVED_PROMPTS_FILE, 'r') as f:
                try:
                    saved_prompts = json.load(f)
                    if not isinstance(saved_prompts, list):
                        return jsonify({'error': 'Saved prompts data is corrupted.'}), 500
                except json.JSONDecodeError:
                    return jsonify({'error': 'Saved prompts data is corrupted (JSON decode error).'}), 500

        original_length = len(saved_prompts)
        saved_prompts = [p for p in saved_prompts if p.get('id') != id]
        if len(saved_prompts) == original_length:
            return jsonify({'error': 'Prompt not found'}), 404
            
        with open(SAVED_PROMPTS_FILE, 'w') as f:
            json.dump(saved_prompts, f, indent=2)
        return jsonify({'message': f'Prompt with id {id} deleted successfully'})
    except Exception as e:
        current_app.logger.error(f"Error deleting prompt {id}: {str(e)}")
        return jsonify({'error': f"Could not delete prompt: {str(e)}"}), 500

# --- General AI Generation Endpoints ---
@ai_bp.route('/api/ai/openrouter/generate', methods=['POST'])
def generate_openrouter_with_key():
    data = request.json
    api_key = data.get('api_key')
    prompt_text = data.get('prompt')
    model_id = data.get('model')
    system_prompt = data.get('system_prompt', DEFAULT_PERFUMERY_PROMPTS.get('openrouter'))

    if not api_key: return jsonify({'error': 'API key is required for OpenRouter.'}), 400
    if not prompt_text: return jsonify({'error': 'Prompt text is required.'}), 400
    if not model_id: return jsonify({'error': 'Model ID is required for OpenRouter.'}), 400
    
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt_text}]
    response_content, error = call_openrouter_api(api_key, model_id, messages)

    if error:
        return jsonify({'error': error}), 500
    return jsonify({'success': True, 'response': response_content, 'model': model_id, 'timestamp': datetime.utcnow().isoformat()})

@ai_bp.route('/api/ai/gemini/generate', methods=['POST'])
def generate_gemini_with_key():
    data = request.json
    api_key = data.get('api_key')
    prompt_text = data.get('prompt')
    model_id = data.get('model')
    system_prompt = data.get('system_prompt', DEFAULT_PERFUMERY_PROMPTS.get('gemini'))
    
    full_prompt = f"{system_prompt}\n\nUser request: {prompt_text}"

    if not api_key: return jsonify({'error': 'API key is required for Gemini.'}), 400
    if not prompt_text: return jsonify({'error': 'Prompt text is required.'}), 400
    if not model_id: return jsonify({'error': 'Model ID is required for Gemini.'}), 400

    response_content, error = call_gemini_api(api_key, model_id, full_prompt)
    if error:
        return jsonify({'error': error}), 500
    return jsonify({'success': True, 'response': response_content, 'model': model_id, 'timestamp': datetime.utcnow().isoformat()})

@ai_bp.route('/api/ai/claude/generate', methods=['POST'])
def generate_claude_with_key():
    data = request.json
    api_key = data.get('api_key')
    prompt_text = data.get('prompt')
    model_id = data.get('model')
    system_prompt = data.get('system_prompt', DEFAULT_PERFUMERY_PROMPTS.get('claude'))

    if not api_key: return jsonify({'error': 'API key is required for Claude.'}), 400
    if not prompt_text: return jsonify({'error': 'Prompt text is required.'}), 400
    if not model_id: return jsonify({'error': 'Model ID is required for Claude.'}), 400

    messages = [{"role": "user", "content": prompt_text}] 
    response_content, error = call_claude_api(api_key, model_id, messages, system_prompt=system_prompt)

    if error:
        return jsonify({'error': error}), 500
    return jsonify({'success': True, 'response': response_content, 'model': model_id, 'timestamp': datetime.utcnow().isoformat()})


# --- AI Formula Generation Endpoint ---
def get_available_ingredients_for_ai():
    ingredients = Ingredient.query.all()
    ai_ingredient_list = []
    for ing in ingredients:
        ai_ingredient_list.append({
            "name": ing.name,
            "odor_profile": ing.odor_profile or ing.description or "N/A", 
            "unit_of_measurement": ing.unit_of_measurement 
        })
    return ai_ingredient_list

def construct_ai_formula_prompt(user_description, available_ingredients, current_formula_context=None, target_total_quantity=None):
    ingredient_list_str = "\n".join([
        f"- Name: \"{ing['name']}\", Odor Profile: \"{ing['odor_profile']}\", Base Unit: \"{ing['unit_of_measurement']}\""
        for ing in available_ingredients
    ])

    context_str = ""
    if current_formula_context and isinstance(current_formula_context, list) and len(current_formula_context) > 0:
        context_items_str = "\n".join([
            f"  - \"{item.get('name', 'Unknown Ingredient')}\": {item.get('quantity', 0)} {item.get('unit', 'g')}" 
            for item in current_formula_context if item.get('name') 
        ])
        if context_items_str.strip():
             context_str = f"\nThe user is currently working with the following formula (you can adjust or build upon this, or create a new one if the request implies it):\n{context_items_str}\n"

    prompt = f"""You are an expert perfumer tasked with creating or adjusting a formula based on a user's request.
The user wants to achieve a scent described as: "{user_description}".
{context_str}
You MUST ONLY use ingredients from the following list of available materials:
{ingredient_list_str}

Instructions for formula generation/adjustment:
1.  The final formula should be a list of ingredients with their quantities and units.
2.  Quantities should primarily be in grams (g) or milliliters (mL). For very potent materials or small adjustments, you may use drops (drops) or microliters (uL).
3.  The total amount of the formula should be reasonable for a small trial batch. {"If the user requests a specific total quantity (e.g., 'adjust to 30mL'), aim for that. Otherwise, " if target_total_quantity else ""} a total of 10g or 10mL is a good target for a new formula if no existing context or target is given. If adjusting an existing formula, try to maintain a similar total quantity unless specified otherwise or if the adjustment (e.g. 'make it 30mL') implies a new total.
4.  Ensure ingredient names in your generated formula EXACTLY match the names from the provided list of available materials. Case sensitivity might matter for some systems, so try to match casing if possible, but prioritize matching the name itself.
5.  Your response MUST be a single valid JSON object containing one key: "formula_ingredients".
    - "formula_ingredients" must be an array of objects.
    - Each object in the array represents one ingredient in the formula and MUST have the following keys:
        - "ingredient_name": (string) The exact name from the available list.
        - "quantity": (number) The amount (must be positive).
        - "unit": (string) The unit for the quantity (e.g., "g", "mL", "drops", "uL").

Example of desired JSON output:
{{
  "formula_ingredients": [
    {{ "ingredient_name": "Bergamot Essential Oil", "quantity": 2.5, "unit": "g" }},
    {{ "ingredient_name": "Linalool", "quantity": 20, "unit": "drops" }},
    {{ "ingredient_name": "Iso E Super", "quantity": 500, "unit": "uL" }}
  ]
}}

Do not include any other text, explanations, apologies, or conversational pleasantries outside of this JSON object in your response.
Your entire response should be only the JSON object.
"""
    return prompt


def parse_ai_formula_response(ai_response_str, available_ingredients_names):
    try:
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response_str, re.DOTALL)
        if json_match:
            ai_response_str_cleaned = json_match.group(1)
        else:
            first_brace = ai_response_str.find('{')
            last_brace = ai_response_str.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                ai_response_str_cleaned = ai_response_str[first_brace : last_brace+1]
            else:
                ai_response_str_cleaned = ai_response_str 
        data = json.loads(ai_response_str_cleaned)
        if "formula_ingredients" not in data or not isinstance(data["formula_ingredients"], list):
            return None, "AI response is missing 'formula_ingredients' array or it's not a list."
        parsed_formula = []
        for item in data["formula_ingredients"]:
            if not isinstance(item, dict):
                 return None, f"AI response item is not a valid object: {item}"
            if not all(k in item for k in ["ingredient_name", "quantity", "unit"]):
                return None, f"AI response item missing required keys (ingredient_name, quantity, unit): {item}"
            
            ingredient_name_from_ai = item["ingredient_name"]
            matched_inventory_name = None
            for inv_name in available_ingredients_names:
                if ingredient_name_from_ai.lower() == inv_name.lower():
                    matched_inventory_name = inv_name
                    break
            
            if not matched_inventory_name:
                return None, f"AI suggested an unavailable or misspelled ingredient: '{ingredient_name_from_ai}'"
            
            try:
                quantity = float(item["quantity"])
                if quantity <= 0: 
                     return None, f"AI suggested a non-positive quantity for '{matched_inventory_name}'"
            except (ValueError, TypeError):
                return None, f"AI suggested an invalid quantity ('{item['quantity']}') for '{matched_inventory_name}'"

            parsed_formula.append({
                "ingredient_name": matched_inventory_name, 
                "quantity": quantity,
                "unit": str(item["unit"]) 
            })
        return parsed_formula, None
    except json.JSONDecodeError:
        current_app.logger.error(f"AI response JSONDecodeError. Raw response: {ai_response_str}")
        return None, "AI response was not valid JSON. Please check the AI's output format."
    except Exception as e:
        current_app.logger.error(f"Error parsing AI response: {str(e)}. Raw response: {ai_response_str}")
        return None, f"Error parsing AI response: {str(e)}"


@ai_bp.route('/api/ai/generate-formula', methods=['POST'])
def ai_generate_formula():
    data = request.json
    user_description = data.get('user_description')
    ai_service = data.get('ai_service', 'gemini') 
    model_id = data.get('model_id') 
    api_key = data.get('api_key')
    current_formula_context = data.get('current_formula_context') 
    target_total_quantity_str = data.get('target_total_quantity')

    target_total_quantity = None
    if target_total_quantity_str:
        try:
            target_total_quantity = float(target_total_quantity_str)
        except ValueError:
            current_app.logger.warning(f"Invalid target_total_quantity received: {target_total_quantity_str}")

    if not user_description: return jsonify({'error': 'User description is required.'}), 400
    if not model_id: return jsonify({'error': 'AI Model ID is required.'}), 400
    if not api_key: return jsonify({'error': f'API key for {ai_service} is required.'}), 400

    try:
        available_ingredients = get_available_ingredients_for_ai()
        if not available_ingredients:
            return jsonify({'error': 'No ingredients available in inventory to generate a formula.'}), 400
        
        available_ingredients_names = [ing["name"] for ing in available_ingredients]
        
        prompt_for_formula_json = construct_ai_formula_prompt(
            user_description, 
            available_ingredients,
            current_formula_context=current_formula_context,
            target_total_quantity=target_total_quantity
        )
        system_prompt_for_service = DEFAULT_PERFUMERY_PROMPTS.get(ai_service, "You are a helpful assistant.")
        
        ai_raw_response_str = None
        error_message = None

        current_app.logger.info(f"Attempting AI formula generation with {ai_service} (model: {model_id}), API Key Hint: {api_key[:4]}...")
        current_app.logger.debug(f"Full prompt for AI: {prompt_for_formula_json}")


        if ai_service == 'gemini':
            ai_raw_response_str, error_message = call_gemini_api(api_key, model_id, prompt_for_formula_json, is_json_mode=True)
        elif ai_service == 'openrouter':
            messages = [{"role": "system", "content": system_prompt_for_service}, {"role": "user", "content": prompt_for_formula_json}]
            ai_raw_response_str, error_message = call_openrouter_api(api_key, model_id, messages, is_json_mode=True)
        elif ai_service == 'claude':
            messages = [{"role": "user", "content": prompt_for_formula_json}]
            ai_raw_response_str, error_message = call_claude_api(api_key, model_id, messages, system_prompt=system_prompt_for_service)
        else:
            return jsonify({'error': f'AI service "{ai_service}" not supported for formula generation.'}), 400

        if error_message:
            current_app.logger.error(f"AI API Call Error ({ai_service}): {error_message}")
            return jsonify({'error': error_message, 'raw_ai_response_for_debug': ai_raw_response_str or "No response received"}), 500
        
        if not ai_raw_response_str:
             current_app.logger.error(f"AI service {ai_service} returned an empty response string.")
             return jsonify({'error': 'AI service failed to generate a response (empty).'}), 500

        parsed_formula, parse_error_msg = parse_ai_formula_response(ai_raw_response_str, available_ingredients_names)

        if parse_error_msg:
            current_app.logger.warning(f"AI Formula Parsing/Validation Error: {parse_error_msg}. Raw AI Response: {ai_raw_response_str}")
            return jsonify({'error': f"Error processing AI response: {parse_error_msg}", 'raw_ai_response_for_debug': ai_raw_response_str}), 500
        
        return jsonify({'success': True, 'generated_formula': parsed_formula })

    except Exception as e:
        current_app.logger.error(f"Error in /api/ai/generate-formula: {str(e)}", exc_info=True)
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

