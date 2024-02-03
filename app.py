from flask import Flask, url_for, render_template
import markdown
import locale
import logging
import os

app = Flask(__name__)


locale.setlocale(locale.LC_ALL, "de_DE.UTF8") # Deutsche Namen für Tage und Monate

# Configure the logger
log_file_path = 'hp.log'
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
file_handler = logging.FileHandler(log_file_path, mode='a')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# check if the template is available in the correct language
def files_with_lang(filenames, lang):
    lang = lang.replace("/","")
    print(filenames, lang)
    filenames_with_lang = []
    for filename in filenames:
        loc = lang
        # do nothing if the next if is false in order to reduce errors
        if os.path.exists("templates/de/" + filename) or os.path.exists("templates/en/" + filename):
            if os.path.exists("templates/" + lang + "/" + filename):
                loc = loc
            else:
                if loc == "de":
                    loc = "en"
                else:
                    loc = "de"
            filenames_with_lang.append("/" + loc + "/" + filename)
    return filenames_with_lang

@app.route("/<lang>/")
def showbase(lang):
    filenames = files_with_lang(["quicklinks.html", "news.html"], lang)
    return render_template(f"{lang}/home.html", filenames = filenames, lang=lang)

@app.route("/<lang>/mscdata/")
def showmscdata(lang):
    filenames = ["carousel.html", "news.html"]
    return render_template("home.html", filenames = filenames, lang=lang, site = "showmscdata")

@app.route("/<lang>/allgemeines")
def showallgemeines(lang):
    filenames = files_with_lang(["allgemeines"], lang)
    return render_template(f"{lang}/home.html", filenames = filenames)


if __name__ == 'main__':
    app.run(debug = True)
