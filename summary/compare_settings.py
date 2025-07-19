import yaml
import json
import os
import asyncio
import aiohttp
from datetime import datetime
import time

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
        'user': formatted_user
    }

def generate_settings_combinations():
    """Generate different combinations of model settings"""
    
    # Define parameter ranges to test
    models = [
        # "gemini-2.5-pro", 
        # "gemini-2.5-flash",
        # "claude-3.5-sonnet",
        # "claude-3-opus",
        # "gpt-4o",
        # "gpt-4o-mini",
        # "deepseek-chat",
        # "deepseek-reasoner",
        "grok-4"
        # "GPT-4.1",
        # "GPT-4.1 mini",
        # "o3",
        # "o4 mini"
        #"GPT-deepresearch"
    ]
    
    # Define specific parameter combinations
    parameter_sets = [
        # {"temperature": 0.2, "top_p": 0.95, "top_k": 30},
        # {"temperature": 0.9, "top_p": 0.99, "top_k": 40},
        {"temperature": 0.1, "top_p": 0.9, "top_k": 20},
        # {"temperature": 0, "top_p": 0.95, "top_k": 40}  # Added default top_p and top_k for T=0
    ]
    
    combinations = []
    
    # Generate combinations: each model with each parameter set
    for model in models:
        for params in parameter_sets:
            combinations.append({
                "model": model,
                "temperature": params["temperature"],
                "top_k": params["top_k"],
                "top_p": params["top_p"]
            })
    
    return combinations

def load_test_context(file_path):
    """Load test context from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return None

def create_test_scenarios():
    """Create different test scenarios with various market data"""
    # Try to load from test_context.json first
    test_context = load_test_context('test_context.json')
    
    scenarios = []
    
    # Add scenario from test_context.json if available
    if test_context:
        scenarios.append({
            "name": test_context.get("name", "Custom Test Scenario"),
            "market": test_context.get("market", "Unknown market"),
            "competitors": test_context.get("competitors", "Unknown competitors"),
            "context": test_context.get("context", "No additional context provided")
        })
    
    return scenarios

class APIClient:
    def __init__(self):
        self.api_keys = self.load_api_keys()
    
    def load_api_keys(self):
        """Load API keys from environment variables or config file"""
        import os
        
        api_keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"), 
            "google": os.getenv("GOOGLE_API_KEY"),
            "xai": os.getenv("XAI_API_KEY"),
            "deepseek": os.getenv("DEEPSEEK_API_KEY")
        }
        
        # Try to load from config file if env vars not found
        try:
            with open('api_keys.json', 'r') as f:
                file_keys = json.load(f)
                for key, value in file_keys.items():
                    if not api_keys.get(key):
                        api_keys[key] = value
        except FileNotFoundError:
            print("Warning: api_keys.json not found. Please set API keys via environment variables or create api_keys.json")
        
        return api_keys
    
    def get_api_config(self, model_name):
        """Get API configuration for different models"""
        model_configs = {
            # OpenAI models
            "o3": {
                "provider": "openai",
                "url": "https://api.openai.com/v1/chat/completions",
                "model": "o3-mini"
            },
            "GPT-4o": {
                "provider": "openai", 
                "url": "https://api.openai.com/v1/chat/completions",
                "model": "gpt-4o"
            },
            "GPT-4.1": {
                "provider": "openai",
                "url": "https://api.openai.com/v1/chat/completions", 
                "model": "gpt-4.1"
            },
            "GPT-4.1 mini": {
                "provider": "openai",
                "url": "https://api.openai.com/v1/chat/completions",
                "model": "gpt-4.1-mini"
            },
            "o4 mini": {
                "provider": "openai",
                "url": "https://api.openai.com/v1/chat/completions",
                "model": "o4-mini"
            },
            "GPT-deepresearch": {
                "provider": "openai",
                "url": "https://api.openai.com/v1/chat/completions",
                "model": "o3-deep-research-2025-06-26"
            },

            # Anthropic models
            "claude-3.5-sonnet": {
                "provider": "anthropic",
                "url": "https://api.anthropic.com/v1/messages",
                "model": "claude-3-5-sonnet-20241022"
            },
            "claude-3-opus": {
                "provider": "anthropic",
                "url": "https://api.anthropic.com/v1/messages", 
                "model": "claude-3-opus-20240229"
            },
            
            # Google models
            "gemini-2.5-flash": {
                "provider": "google",
                "model": "gemini-2.5-flash"
            },
            "gemini-2.5-pro": {
                "provider": "google", 
                "model": "gemini-2.5-pro"
            },
            
            # xAI models
            "grok-4": {
                "provider": "xai",
                "model": "grok-4"
            },
            
            # DeepSeek models
            "deepseek-chat": {
                "provider": "deepseek",
                "url": "https://api.deepseek.com/v1/chat/completions",
                "model": "deepseek-chat"
            },
            "deepseek-reasoner": {
                "provider": "deepseek",
                "url": "https://api.deepseek.com/v1/chat/completions",
                "model": "deepseek-reasoner"
            }
        }
        
        return model_configs.get(model_name)
    
    async def call_api(self, session, model_name, system_prompt, user_prompt, settings):
        """Make API call to the specified model"""
        config = self.get_api_config(model_name)
        if not config:
            return {"error": f"Model {model_name} not supported"}
        
        provider = config["provider"]
        api_key = self.api_keys.get(provider)
        
        if not api_key:
            return {"error": f"API key not found for {provider}"}
        
        try:
            if provider == "openai" or provider == "deepseek":
                return await self._call_openai_style_api(session, config, api_key, system_prompt, user_prompt, settings)
            elif provider == "xai":
                return await self._call_xai_sdk_api(config, api_key, system_prompt, user_prompt, settings)
            elif provider == "anthropic":
                return await self._call_anthropic_api(session, config, api_key, system_prompt, user_prompt, settings)
            elif provider == "google":
                return await self._call_google_genai_api(config, api_key, system_prompt, user_prompt, settings)
        except Exception as e:
            return {"error": str(e)}
    
    def is_reasoning_model(self, model_name):
        """Check if model is a reasoning model that doesn't support temperature"""
        reasoning_models = ["o3-mini", "o1", "o1-preview", "o1-mini"]
        return model_name in reasoning_models
    
    def is_limited_reasoning_model(self, model_name):
        """Check if model only supports temperature=1"""
        limited_models = ["o4-mini"]
        return model_name in limited_models
    
    async def _call_openai_style_api(self, session, config, api_key, system_prompt, user_prompt, settings):
        """Call OpenAI-style APIs (OpenAI, xAI, DeepSeek)"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        
        # Handle reasoning models that don't support temperature
        if self.is_reasoning_model(config["model"]):
            # Don't add temperature for o3, o1 models
            pass
        elif self.is_limited_reasoning_model(config["model"]):
            # Only add temperature=1 for o4-mini
            payload["temperature"] = 1
        else:
            # Normal models support temperature
            payload["temperature"] = settings["temperature"]
            
            # Add top_p and top_k if supported
            if settings.get("top_p") is not None:
                payload["top_p"] = settings["top_p"]
    
        
        async with session.post(config["url"], headers=headers, json=payload) as response:
            result = await response.json()
            
            if response.status == 200:
                return {
                    "response": result["choices"][0]["message"]["content"],
                    "usage": result.get("usage", {}),
                    "model": config["model"],
                    "actual_settings": {
                        "temperature": payload.get("temperature", "not_supported"),
                        "top_p": payload.get("top_p", "not_set")
                    }
                }
            else:
                return {"error": f"API Error: {result}"}
    
    async def _call_xai_sdk_api(self, config, api_key, system_prompt, user_prompt, settings):
        """Call xAI API using the xai_sdk"""
        try:
            # Import xai_sdk dynamically
            import asyncio
            from xai_sdk.search import SearchParameters
            
            def call_xai_sync():
                try:
                    from xai_sdk import Client
                    from xai_sdk.chat import user, system
                    
                    client = Client(api_key=api_key)
                    
                    chat = client.chat.create(model=config["model"],search_parameters=SearchParameters(mode="on"))
                    chat.append(system(system_prompt))
                    chat.append(user(user_prompt))
                    
                    response = chat.sample()
                    
                    return {
                        "response": response.content,
                        "usage": {"total_tokens": len(response.content.split())},  # Rough estimate
                        "model": config["model"],
                        "actual_settings": {
                            "temperature": "xai_default",
                            "top_p": "xai_default",
                            "max_tokens": "xai_default"
                        }
                    }
                except ImportError:
                    return {"error": "xai_sdk not installed. Please install: pip install xai_sdk"}
                except Exception as e:
                    return {"error": f"xAI SDK Error: {str(e)}"}
            
            # Run the synchronous xAI call in a thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, call_xai_sync)
            return result
            
        except Exception as e:
            return {"error": f"xAI Integration Error: {str(e)}"}
    
    async def _call_anthropic_api(self, session, config, api_key, system_prompt, user_prompt, settings):
        """Call Anthropic API"""
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": config["model"],
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": settings["temperature"]
        }
        
        if settings.get("top_p") is not None:
            payload["top_p"] = settings["top_p"]
        if settings.get("top_k") is not None:
            payload["top_k"] = settings["top_k"]
        
        async with session.post(config["url"], headers=headers, json=payload) as response:
            result = await response.json()
            
            if response.status == 200:
                return {
                    "response": result["content"][0]["text"],
                    "usage": result.get("usage", {}),
                    "model": config["model"]
                }
            else:
                return {"error": f"API Error: {result}"}
    
    async def _call_google_api(self, session, config, api_key, system_prompt, user_prompt, settings):
        """Call Google API"""
        url = f"{config['url']}?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
            }],
            "generationConfig": {
                "temperature": settings["temperature"]
            }
        }
        
        if settings.get("top_p") is not None:
            payload["generationConfig"]["topP"] = settings["top_p"]
        if settings.get("top_k") is not None:
            payload["generationConfig"]["topK"] = settings["top_k"]
        
        async with session.post(url, json=payload) as response:
            result = await response.json()
            
            if response.status == 200:
                return {
                    "response": result["candidates"][0]["content"]["parts"][0]["text"],
                    "usage": result.get("usageMetadata", {}),
                    "model": config["model"]
                }
            else:
                return {"error": f"API Error: {result}"}

    async def _call_google_genai_api(self, config, api_key, system_prompt, user_prompt, settings):
        """Call Google API using the new genai SDK"""
        try:
            import asyncio
            
            def call_google_sync():
                try:
                    from google import genai
                    from google.genai import types
                    
                    # Configure the client with API key
                    client = genai.Client(api_key=api_key)
                    
                    # Combine system and user prompts
                    combined_prompt = f"{system_prompt}\n\n{user_prompt}"
                    
                    # Create generation config
                    generation_config = types.GenerateContentConfig(
                        temperature=settings.get("temperature", 0.7)
                    )
                    
                    # Add thinking config for thinking models
                    if "thinking" in config["model"].lower():
                        generation_config.thinking_config = types.ThinkingConfig(thinking_budget=1000)
                    
                    # Add top_p if specified
                    if settings.get("top_p"):
                        generation_config.top_p = settings["top_p"]
                    
                    # Add top_k if specified  
                    if settings.get("top_k"):
                        generation_config.top_k = settings["top_k"]
                    
                    response = client.models.generate_content(
                        model=config["model"],
                        contents=combined_prompt,
                        config=generation_config
                    )
                    # Check if response has text
                    if hasattr(response, 'text') and response.text:
                        response_text = response.text
                        token_count = len(response_text.split())
                    elif hasattr(response, 'candidates') and response.candidates:
                        # Try to get text from candidates
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                response_text = candidate.content.parts[0].text
                                token_count = len(response_text.split())
                            else:
                                response_text = str(candidate.content)
                                token_count = len(response_text.split())
                        else:
                            return {"error": f"No content in response candidate: {candidate}"}
                    else:
                        return {"error": f"No valid response from Google API. Response: {response}"}
                    
                    return {
                        "response": response_text,
                        "usage": {"total_tokens": token_count},
                        "model": config["model"],
                        "actual_settings": {
                            "temperature": settings.get("temperature", 0.7),
                            "top_p": settings.get("top_p", "not_set"),
                            "top_k": settings.get("top_k", "not_set"),
                            "max_tokens": settings.get("max_tokens", 2000)
                        }
                    }
                except ImportError:
                    return {"error": "google-genai not installed. Please install: pip install google-genai"}
                except Exception as e:
                    return {"error": f"Google GenAI SDK Error: {str(e)}"}
            
            # Run the synchronous Google call in a thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, call_google_sync)
            return result
            
        except Exception as e:
            return {"error": f"Google GenAI Integration Error: {str(e)}"}

def save_test_result(scenario_name, settings, formatted_prompt, api_response, output_dir):
    """Save test configuration, prompt, and API response to file"""
    
    # Create filename with timestamp and settings info
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
    filename = f"{scenario_name}_{settings['model']}_{settings['temperature']}_{settings['top_k']}_{settings['top_p']}_{timestamp}.json"
    filename = filename.replace(" ", "_").replace("(", "").replace(")", "").replace(".", "_")
    
    result = {
        "scenario": scenario_name,
        "settings": settings,
        "prompt": formatted_prompt,
        "api_response": api_response,
        "timestamp": timestamp,
        "status": "completed" if "error" not in api_response else "failed"
    }
    
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    return filepath

async def run_comparison_test_with_api():
    """Run comprehensive comparison test with actual API calls"""
    
    # Create output directory
    output_dir = "prompt_test_results2"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load template
    template = load_prompt_template('prompt.yaml')
    print(f"Loaded template: {template['name']}")
    
    # Get test scenarios and settings combinations
    scenarios = create_test_scenarios()
    settings_combinations = generate_settings_combinations()
    
    print(f"Testing {len(scenarios)} scenarios with {len(settings_combinations)} settings combinations")
    print(f"Total tests: {len(scenarios) * len(settings_combinations)}")
    
    # Initialize API client
    api_client = APIClient()
    
    # Create summary file
    summary = {
        "test_run_info": {
            "timestamp": datetime.now().isoformat(),
            "total_scenarios": len(scenarios),
            "total_settings_combinations": len(settings_combinations),
            "total_tests": len(scenarios) * len(settings_combinations)
        },
        "scenarios": scenarios,
        "settings_combinations": settings_combinations,
        "completed_tests": [],
        "failed_tests": []
    }
    
    # Run tests with API calls
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
        for scenario in scenarios:
            print(f"\nTesting scenario: {scenario['name']}")
            
            for i, settings in enumerate(settings_combinations):
                print(f"  Settings {i+1}/{len(settings_combinations)}: {settings['model']} T={settings['temperature']} K={settings['top_k']} P={settings['top_p']}")
                
                # Format prompt with current scenario
                formatted_prompt = format_prompt(
                    template, 
                    scenario['market'], 
                    scenario['competitors'], 
                    scenario['context']
                )
                
                # Make API call
                print(f"    Making API call to {settings['model']}...")
                start_time = time.time()
                
                api_response = await api_client.call_api(
                    session,
                    settings['model'],
                    formatted_prompt['system'],
                    formatted_prompt['user'],
                    settings
                )
                
                end_time = time.time()
                api_response['response_time'] = end_time - start_time
                
                # Save test result with API response
                filepath = save_test_result(scenario['name'], settings, formatted_prompt, api_response, output_dir)
                
                if "error" not in api_response:
                    summary['completed_tests'].append(os.path.basename(filepath))
                    print(f"    ✅ Success - Response time: {api_response['response_time']:.2f}s")
                else:
                    summary['failed_tests'].append({
                        "file": os.path.basename(filepath),
                        "error": api_response["error"]
                    })
                    print(f"    ❌ Failed: {api_response}")
                
                # Add small delay to respect rate limits
                await asyncio.sleep(1)
    
    # Save summary
    summary_path = os.path.join(output_dir, f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Test execution complete!")
    print(f"📁 Results saved to: {output_dir}")
    print(f"📊 Summary file: {summary_path}")
    print(f"🎯 Completed: {len(summary['completed_tests'])} tests")
    print(f"❌ Failed: {len(summary['failed_tests'])} tests")
    
    return output_dir, summary_path

def run_comparison_test():
    """Run comprehensive comparison test across different settings"""
    return asyncio.run(run_comparison_test_with_api())

def analyze_specific_combination(model="claude-3-sonnet", temperature=0.7, top_k=40, top_p=0.9):
    """Analyze a specific settings combination in detail"""
    
    template = load_prompt_template('prompt.yaml')
    scenarios = create_test_scenarios()
    
    settings = {
        "model": model,
        "temperature": temperature,
        "top_k": top_k,
        "top_p": top_p
    }
    
    print(f"=== ANALYZING SPECIFIC COMBINATION ===")
    print(f"Settings: {settings}")
    print()
    
    for scenario in scenarios:
        print(f"--- SCENARIO: {scenario['name']} ---")
        formatted_prompt = format_prompt(
            template, 
            scenario['market'], 
            scenario['competitors'], 
            scenario['context']
        )
        
        print("SYSTEM PROMPT:")
        print(formatted_prompt['system'])
        print("\nUSER PROMPT:")
        print(formatted_prompt['user'])
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    print("🚀 Starting prompt settings comparison test...")
    
    # Choice menu
    print("Choose test mode:")
    print("1. Run full comparison test (generates all combinations)")
    print("2. Analyze specific settings combination")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        run_comparison_test()
    elif choice == "2":
        analyze_specific_combination()
    else:
        print("Invalid choice. Running full comparison test...")
        run_comparison_test()