from dotenv import load_dotenv
from app import create_app

# .env (optional) laden
load_dotenv()

app = create_app()

if __name__ == "__main__":
    # Port kannst du via ENV PORT überschreiben
    app.run(host="0.0.0.0", port=5151, debug=True)
