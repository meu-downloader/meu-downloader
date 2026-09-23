from flask import Flask, render_template, request, send_file, jsonify
import os
import uuid
import subprocess
import shutil

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)


def encontrar_ytdlp():
    return shutil.which("yt-dlp")


def encontrar_ffmpeg():
    return shutil.which("ffmpeg")


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
    dados = request.get_json()

    if not dados:
        return jsonify({"erro": "Nenhum dado recebido."}), 400

    url = dados.get("url", "").strip()
    tipo = dados.get("tipo", "video")
    qualidade = dados.get("qualidade", "720")

    if not url:
        return jsonify({"erro": "Digite uma URL."}), 400

    if not url.startswith(("http://", "https://")):
        return jsonify({"erro": "URL inválida."}), 400

    ytdlp = encontrar_ytdlp()

    if not ytdlp:
        return jsonify({
            "erro": "yt-dlp não foi encontrado no servidor."
        }), 500

    ffmpeg = encontrar_ffmpeg()

    if not ffmpeg:
        return jsonify({
            "erro": "FFmpeg não foi encontrado no servidor."
        }), 500

    identificador = uuid.uuid4().hex

    if tipo == "mp3":
        caminho_saida = os.path.join(
            TEMP_DIR,
            f"{identificador}.mp3"
        )

        comando = [
            ytdlp,
            "--no-playlist",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--ffmpeg-location", ffmpeg,
            "-o", caminho_saida,
            url
        ]

    elif tipo == "m4a":
        caminho_saida = os.path.join(
            TEMP_DIR,
            f"{identificador}.m4a"
        )

        comando = [
            ytdlp,
            "--no-playlist",
            "-x",
            "--audio-format", "m4a",
            "--audio-quality", "0",
            "--ffmpeg-location", ffmpeg,
            "-o", caminho_saida,
            url
        ]

    else:
        caminho_saida = os.path.join(
            TEMP_DIR,
            f"{identificador}.mp4"
        )

        if qualidade == "best":
            formato = "bv*+ba/b"
        else:
            try:
                limite = int(qualidade)
            except ValueError:
                limite = 720

            formato = (
                f"bv*[height<={limite}]+ba/"
                f"b[height<={limite}]/b"
            )

        comando = [
            ytdlp,
            "--no-playlist",
            "-f", formato,
            "--merge-output-format", "mp4",
            "--ffmpeg-location", ffmpeg,
            "-o", caminho_saida,
            url
        ]

    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if resultado.returncode != 0:
            if os.path.exists(caminho_saida):
                os.remove(caminho_saida)

            return jsonify({
                "erro": "O yt-dlp não conseguiu realizar o download.",
                "detalhes": resultado.stderr[-3000:]
            }), 500

        if not os.path.exists(caminho_saida):
            arquivos = os.listdir(TEMP_DIR)

            encontrados = [
                os.path.join(TEMP_DIR, arquivo)
                for arquivo in arquivos
                if arquivo.startswith(identificador)
            ]

            if encontrados:
                caminho_saida = encontrados[0]
            else:
                return jsonify({
                    "erro": "O download terminou, mas o arquivo não foi encontrado."
                }), 500

        resposta = send_file(
            caminho_saida,
            as_attachment=True,
            download_name=os.path.basename(caminho_saida)
        )

        @resposta.call_on_close
        def apagar_arquivo():
            try:
                if os.path.exists(caminho_saida):
                    os.remove(caminho_saida)
            except Exception as erro:
                print("Erro ao apagar arquivo:", erro)

        return resposta

    except Exception as erro:
        if os.path.exists(caminho_saida):
            try:
                os.remove(caminho_saida)
            except:
                pass

        return jsonify({
            "erro": str(erro)
        }), 500


@app.route("/status")
def status():
    return jsonify({
        "status": "online"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000,
        debug=False
    )
