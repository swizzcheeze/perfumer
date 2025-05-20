from flask import Blueprint, jsonify, request
import json
import os
from datetime import datetime

ai_bp = Blueprint('ai', __name__)

# Models for AI playground
OPENROUTER_MODELS = [
    {"id": "openai/gpt-4-turbo", "name": "GPT-4 Turbo"},
    {"id": "anthropic/claude-3-opus", "name": "Claude 3 Opus"},
    {"id": "anthropic/claude-3-sonnet", "name": "Claude 3 Sonnet"},
    {"id": "meta-llama/llama-3-70b-instruct", "name": "Llama 3 70B"}
]

GEMINI_MODELS = [
    {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro"},
    {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"}
]

CLAUDE_MODELS = [
    {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
    {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"},
    {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"}
]

# Default system prompts for perfumery
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

# Saved prompts storage (would be in database in production)
SAVED_PROMPTS_FILE = '/home/ubuntu/perfumery_app/src/data/saved_prompts.json'

# Ensure the data directory exists
os.makedirs(os.path.dirname(SAVED_PROMPTS_FILE), exist_ok=True)

# Initialize saved prompts file if it doesn't exist
if not os.path.exists(SAVED_PROMPTS_FILE):
    with open(SAVED_PROMPTS_FILE, 'w') as f:
        json.dump([], f)

@ai_bp.route('/api/ai/models', methods=['GET'])
def get_ai_models():
    """Get available AI models for each service"""
    return jsonify({
        'openrouter': OPENROUTER_MODELS,
        'gemini': GEMINI_MODELS,
        'claude': CLAUDE_MODELS
    })

@ai_bp.route('/api/ai/default-prompts', methods=['GET'])
def get_default_prompts():
    """Get default system prompts for perfumery"""
    return jsonify(DEFAULT_PERFUMERY_PROMPTS)

@ai_bp.route('/api/ai/saved-prompts', methods=['GET'])
def get_saved_prompts():
    """Get all saved prompts"""
    try:
        with open(SAVED_PROMPTS_FILE, 'r') as f:
            saved_prompts = json.load(f)
        return jsonify(saved_prompts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/api/ai/saved-prompts', methods=['POST'])
def save_prompt():
    """Save a new prompt"""
    data = request.json
    
    # Validate required fields
    required_fields = ['name', 'service', 'model', 'system_prompt', 'user_prompt']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Field {field} is required'}), 400
    
    try:
        with open(SAVED_PROMPTS_FILE, 'r') as f:
            saved_prompts = json.load(f)
        
        # Create new prompt with ID and timestamp
        new_prompt = {
            'id': len(saved_prompts) + 1,
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
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/api/ai/saved-prompts/<int:id>', methods=['PUT'])
def update_saved_prompt(id):
    """Update a saved prompt"""
    data = request.json
    
    try:
        with open(SAVED_PROMPTS_FILE, 'r') as f:
            saved_prompts = json.load(f)
        
        # Find prompt by ID
        prompt_index = None
        for i, prompt in enumerate(saved_prompts):
            if prompt['id'] == id:
                prompt_index = i
                break
        
        if prompt_index is None:
            return jsonify({'error': 'Prompt not found'}), 404
        
        # Update fields
        if 'name' in data:
            saved_prompts[prompt_index]['name'] = data['name']
        if 'service' in data:
            saved_prompts[prompt_index]['service'] = data['service']
        if 'model' in data:
            saved_prompts[prompt_index]['model'] = data['model']
        if 'system_prompt' in data:
            saved_prompts[prompt_index]['system_prompt'] = data['system_prompt']
        if 'user_prompt' in data:
            saved_prompts[prompt_index]['user_prompt'] = data['user_prompt']
        
        saved_prompts[prompt_index]['updated_at'] = datetime.utcnow().isoformat()
        
        with open(SAVED_PROMPTS_FILE, 'w') as f:
            json.dump(saved_prompts, f, indent=2)
        
        return jsonify(saved_prompts[prompt_index])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/api/ai/saved-prompts/<int:id>', methods=['DELETE'])
def delete_saved_prompt(id):
    """Delete a saved prompt"""
    try:
        with open(SAVED_PROMPTS_FILE, 'r') as f:
            saved_prompts = json.load(f)
        
        # Find prompt by ID
        prompt_index = None
        for i, prompt in enumerate(saved_prompts):
            if prompt['id'] == id:
                prompt_index = i
                break
        
        if prompt_index is None:
            return jsonify({'error': 'Prompt not found'}), 404
        
        # Remove prompt
        deleted_prompt = saved_prompts.pop(prompt_index)
        
        with open(SAVED_PROMPTS_FILE, 'w') as f:
            json.dump(saved_prompts, f, indent=2)
        
        return jsonify({
            'message': f'Prompt "{deleted_prompt["name"]}" deleted successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/api/ai/openrouter/generate', methods=['POST'])
def generate_openrouter():
    """Generate text using OpenRouter API"""
    data = request.json
    
    # In a real implementation, this would make an actual API call
    # For now, we'll return a mock response
    return jsonify({
        'success': True,
        'response': 'This is a mock response from OpenRouter. In the actual implementation, this would be the AI-generated text based on your prompt about perfumery.',
        'model': data.get('model', 'openai/gpt-4-turbo'),
        'timestamp': datetime.utcnow().isoformat()
    })

@ai_bp.route('/api/ai/gemini/generate', methods=['POST'])
def generate_gemini():
    """Generate text using Gemini API"""
    data = request.json
    
    # In a real implementation, this would make an actual API call
    # For now, we'll return a mock response
    return jsonify({
        'success': True,
        'response': 'This is a mock response from Gemini. In the actual implementation, this would be the AI-generated text based on your prompt about perfumery.',
        'model': data.get('model', 'gemini-1.5-pro'),
        'timestamp': datetime.utcnow().isoformat()
    })

@ai_bp.route('/api/ai/claude/generate', methods=['POST'])
def generate_claude():
    """Generate text using Claude API"""
    data = request.json
    
    # In a real implementation, this would make an actual API call
    # For now, we'll return a mock response
    return jsonify({
        'success': True,
        'response': 'This is a mock response from Claude. In the actual implementation, this would be the AI-generated text based on your prompt about perfumery.',
        'model': data.get('model', 'claude-3-opus-20240229'),
        'timestamp': datetime.utcnow().isoformat()
    })
