import os

# Set a dummy key so llama-index's OpenAI client can be imported and
# instantiated without raising a missing-key error. Real API calls are
# never made during the test suite (they're mocked).
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-do-not-use")
