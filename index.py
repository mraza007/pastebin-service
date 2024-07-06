from flask import Flask, request, render_template, abort
import shortuuid
import os
from pygments import highlight
from pygments.lexers import get_lexer_by_name, get_all_lexers
from pygments.formatters import HtmlFormatter

app = Flask(__name__)

PASTE_DIR = 'pastes'
if not os.path.exists(PASTE_DIR):
    os.makedirs(PASTE_DIR)


def get_language_options():
    return sorted([(lexer[1][0], lexer[0]) for lexer in get_all_lexers() if lexer[1]])


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form['content']
        language = request.form['language']
        paste_id = shortuuid.uuid()
        file_path = os.path.join(PASTE_DIR, paste_id)

        with open(file_path, 'w') as f:
            f.write(f"{language}\n{content}")

        paste_url = request.url_root + paste_id
        return render_template('index.html', paste_url=paste_url, languages=get_language_options())

    return render_template('index.html', languages=get_language_options())


@app.route('/<paste_id>')
def view_paste(paste_id):
    file_path = os.path.join(PASTE_DIR, paste_id)
    if not os.path.exists(file_path):
        abort(404)

    with open(file_path, 'r') as f:
        language = f.readline().strip()
        content = f.read()

    lexer = get_lexer_by_name(language, stripall=True)
    formatter = HtmlFormatter(linenos=True, cssclass="source")
    highlighted_content = highlight(content, lexer, formatter)
    highlight_css = formatter.get_style_defs('.source')

    return render_template('index.html', paste_content=highlighted_content, highlight_css=highlight_css)


if __name__ == '__main__':
    app.run(debug=True)
