from flask import Flask, render_template, request
from camelot.cli import read_pdf

app = Flask(__name__)


@app.route("/")
def home():
    return render_template('home.html')


@app.route('/result', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        file_location = 'tmp/' + f.filename
        f.save(file_location)
        result = read_pdf(file_location, pages='all', **{'line_scale': 25}).to_json()
        return result


if __name__ == "__main__":
    app.run()
