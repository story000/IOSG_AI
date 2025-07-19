import yaml

def load_prompt_template(file_path):
    """Load and parse the YAML prompt template"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def format_prompt(template, market, competitors, context="No additional context provided"):
    """Format the prompt template with provided variables"""
    user_prompt = template['prompt']['user']
    system_prompt = template['prompt']['system']
    
    # Replace variables in user prompt
    formatted_user = user_prompt.replace('{{input.market}}', market)
    formatted_user = formatted_user.replace('{{input.competitors}}', competitors)
    formatted_user = formatted_user.replace('{context}', context)
    
    return {
        'system': system_prompt,
        'user': formatted_user,
        'settings': template['settings']
    }

def test_prompt():
    """Test the prompt template with sample data"""
    
    # Load template
    template = load_prompt_template('prompt.yaml')
    print("Template loaded successfully!")
    print(f"Name: {template['name']}")
    print(f"Description: {template['description']}")
    print()
    
    # Test with sample data
    market = "AI infrastructure"
    competitors = "OpenAI, Anthropic, Google DeepMind"
    context = "Focus on enterprise adoption and revenue models"
    
    formatted_prompt = format_prompt(template, market, competitors, context)
    
    print("=== FORMATTED PROMPT ===")
    print("SYSTEM:")
    print(formatted_prompt['system'])
    print("\nUSER:")
    print(formatted_prompt['user'])
    print("\nSETTINGS:")
    print(formatted_prompt['settings'])

if __name__ == "__main__":
    test_prompt()