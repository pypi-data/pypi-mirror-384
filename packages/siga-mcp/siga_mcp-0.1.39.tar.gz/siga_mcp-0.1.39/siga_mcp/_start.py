from dotenv import load_dotenv
import os

load_dotenv(override=True)

os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-ef37e766-6587-4afb-bad0-bbc4a3f563c1"
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-17ed825f-2b3b-44c9-9f0e-16349e74c2e7"
os.environ["LANGFUSE_HOST"] = "https://langfuse.uniube.br"
os.environ["AVA_API_KEY"] = "92a61a8a-395e-40f9-abe1-7d172ce79df4"
