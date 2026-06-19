from __future__ import annotations

import os

import shortuuid
from flask import (
    Flask,
    Response,
    abort,
    redirect,
    render_template,
    request,
    url_for,
)

from clock import now
from rendering import (
    DARK_CSS,
    LIGHT_CSS,
    get_language_options,
    highlight_code,
    normalize_language,
    render_markdown,
)
from storage import Paste, compute_expires_at, is_valid_id, load_for_view, save_paste

MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB


def create_app(paste_dir: str = "pastes") -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    app.config["PASTE_DIR"] = paste_dir
    os.makedirs(paste_dir, exist_ok=True)

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            content = request.form.get("content", "")
            if not content.strip():
                abort(400)
            render_mode = (
                "markdown"
                if request.form.get("render_mode") == "markdown"
                else "code"
            )
            language = normalize_language(request.form.get("language", "text"))
            paste = Paste(
                id=shortuuid.uuid(),
                content=content,
                language=language,
                render_mode=render_mode,
                created_at=now(),
                expires_at=compute_expires_at(request.form.get("expiry", "never")),
                burn_after_read=request.form.get("burn") == "on",
                views=0,
            )
            save_paste(paste, base_dir=app.config["PASTE_DIR"])
            return redirect(url_for("view_paste", paste_id=paste.id), code=303)
        return render_template("index.html", languages=get_language_options())

    @app.route("/<paste_id>")
    def view_paste(paste_id: str):
        if not is_valid_id(paste_id):
            abort(404)
        paste = load_for_view(paste_id, base_dir=app.config["PASTE_DIR"])
        if paste is None:
            abort(404)
        if paste.render_mode == "markdown":
            body = render_markdown(paste.content)
        else:
            body = highlight_code(paste.content, paste.language)
        return render_template(
            "index.html",
            paste_content=body,
            paste_id=paste_id,
            burned=paste.burn_after_read,
            light_css=LIGHT_CSS,
            dark_css=DARK_CSS,
        )

    def _load_or_404(paste_id: str) -> Paste:
        if not is_valid_id(paste_id):
            abort(404)
        paste = load_for_view(paste_id, base_dir=app.config["PASTE_DIR"])
        if paste is None:
            abort(404)
        return paste

    @app.route("/raw/<paste_id>")
    def raw_paste(paste_id: str):
        paste = _load_or_404(paste_id)
        return Response(paste.content, mimetype="text/plain")

    @app.route("/dl/<paste_id>")
    def download_paste(paste_id: str):
        paste = _load_or_404(paste_id)
        return Response(
            paste.content,
            mimetype="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={paste_id}.txt"
            },
        )

    @app.route("/api/paste", methods=["POST"])
    def api_paste():
        content = request.get_data(as_text=True)
        if not content.strip():
            content = request.form.get("content", "")
        if not content.strip():
            abort(400)
        markdown_flag = request.args.get("markdown") in ("1", "true", "on")
        paste = Paste(
            id=shortuuid.uuid(),
            content=content,
            language=normalize_language(request.args.get("lang", "text")),
            render_mode="markdown" if markdown_flag else "code",
            created_at=now(),
            expires_at=compute_expires_at(request.args.get("expiry", "never")),
            burn_after_read=request.args.get("burn") in ("1", "true", "on"),
            views=0,
        )
        save_paste(paste, base_dir=app.config["PASTE_DIR"])
        url = url_for("view_paste", paste_id=paste.id, _external=True)
        return Response(url + "\n", status=201, mimetype="text/plain")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
