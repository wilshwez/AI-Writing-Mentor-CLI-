import os
import sys
from dotenv import load_dotenv


def load_api_key() -> str:
    """
    Load the Groq API key from the .env file (or environment).

    Returns:
        str: A valid-looking Groq API key.

    Exits the program with a helpful message if the key is missing.
    """
    # Load variables from a .env file into the environment.
    # If .env doesn't exist, this simply does nothing (no crash).
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key or api_key.strip() == "" or api_key == "your_api_key_here":
        print("=" * 50)
        print(" ERROR: Missing or invalid GROQ_API_KEY")
        print("=" * 50)
        print(
            "Please create a '.env' file in this folder with a line like:\n"
            "    GROQ_API_KEY=your_real_key_here\n"
            "You can get a free API key at: https://console.groq.com/keys"
        )
        sys.exit(1)

    return api_key.strip()



# llama-3.3-70b-versatile is a strong general-purpose choice.
DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Default sampling settings - tweak these to change Arthur's "creativity".
DEFAULT_TEMPERATURE = 0.8
DEFAULT_MAX_TOKENS = 2048
