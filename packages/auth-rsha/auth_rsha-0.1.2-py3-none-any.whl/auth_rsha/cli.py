# src/auth_rsha/cli.py
import secrets, sys
def gen_secret():
    print(secrets.token_urlsafe(64))
if __name__ == "__main__":
    if sys.argv[1:] == ["gen-secret"]:
        gen_secret()
