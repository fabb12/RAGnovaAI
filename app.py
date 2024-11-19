from flask import Flask, render_template, redirect, url_for
import subprocess
import os

app = Flask(__name__)

# Configura il percorso dello script Streamlit
STREAMLIT_SCRIPT = "main.py"

@app.route("/")
def home():
    """
    Home page che redirige alla dashboard Streamlit.
    """
    return redirect(url_for("streamlit_dashboard"))


@app.route("/streamlit")
def streamlit_dashboard():
    """
    Serve la dashboard Streamlit come iframe.
    """
    # Avvia Streamlit come sottoprocesso
    streamlit_host = "http://localhost:8501"
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Finance Q&A</title>
    </head>
    <body style="margin:0">
        <iframe src="{streamlit_host}" style="width:100%; height:100%; border:none;"></iframe>
    </body>
    </html>
    """


def start_streamlit():
    """
    Avvia Streamlit come sottoprocesso.
    """
    streamlit_command = ["streamlit", "run", STREAMLIT_SCRIPT]
    subprocess.Popen(streamlit_command, env=os.environ, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


if __name__ == "__main__":
    # Avvia Streamlit in parallelo
    start_streamlit()

    # Esegui l'app Flask
    app.run(host="0.0.0.0", port=5000, debug=True)
