import getpass
import secrets

from huggingface_hub import HfApi

REPO = "prat20/lumina-api"
api = HfApi(token=getpass.getpass("HF write token (input hidden): "))

# --- non-sensitive variables (safe to hardcode) ---
variables = {
    "TRUSTED_PROXY_HOPS": "1",
    "BUDGET_LOCAL_TOKENS_PER_DAY": "90000",
    "BUDGET_GEMINI_REQUESTS_PER_DAY": "18",
    "GOOGLE_CLIENT_ID": "1042988565966-66pfkc9d04b8chjtqlgnh5ecvjagt95d.apps.googleusercontent.com",
    "OAUTH_REDIRECT_URI": "https://luminarag.vercel.app/auth/callback",
    # the frontend's origin must be allowed or it can't call the API at all:
    "CORS_ORIGINS": "https://luminarag.vercel.app,https://lumina-rag-two.vercel.app",
}
for k, v in variables.items():
    api.add_space_variable(repo_id=REPO, key=k, value=v)
    print("variable set:", k)

# --- secrets (typed locally, never printed) ---
client_secret = getpass.getpass("New Google client secret (input hidden): ")
api.add_space_secret(repo_id=REPO, key="GOOGLE_CLIENT_SECRET", value=client_secret)
print("secret set: GOOGLE_CLIENT_SECRET")

# JWT_SECRET is generated here and set directly — no one ever needs to see it:
api.add_space_secret(repo_id=REPO, key="JWT_SECRET", value=secrets.token_hex(32))
print("secret set: JWT_SECRET (auto-generated)")

print("\nDone. The Space will restart to pick up the changes.")
