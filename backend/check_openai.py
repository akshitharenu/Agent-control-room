import openai
try:
    print(f"OpenAI version: {openai.__version__}")
except:
    print("Could not find version")

try:
    from openai import OpenAI
    print("OpenAI client class exists")
except ImportError:
    print("OpenAI client class does NOT exist")
