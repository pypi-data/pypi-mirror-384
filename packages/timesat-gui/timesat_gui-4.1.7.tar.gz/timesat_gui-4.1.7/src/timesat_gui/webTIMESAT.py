from flask import Flask, jsonify, render_template, session, request, send_from_directory
import os  # Import os to use for the favicon route
import psutil
import tempfile

app = Flask(__name__)



app.secret_key = 'supersecretkey'
app.config['MAX_CONTENT_LENGTH'] = 4096 * 1024 * 1024  # 4GB

# file_list_input 的 Blueprint
from file_list_input import file_list_input_bp
app.register_blueprint(file_list_input_bp)
from tab_settings import tab_settings_bp
app.register_blueprint(tab_settings_bp)
from tab_output import tab_output_bp
app.register_blueprint(tab_output_bp)
from tab_save_load import tab_save_load_bp
app.register_blueprint(tab_save_load_bp)
from tab_run import tab_run_bp
app.register_blueprint(tab_run_bp)

@app.route('/')
def home():
    info = {
        'version': '4.1.7',
        'release_date': 'Jan 2025',
        'logos': {
            'malmo': 'malmo-university-vector-logo.png',
            'lund': 'LundUniversity_C2line_RGB.png',
            'timesat': 'Slide_flat.jpg',
            'sidebar': 'Slide2.jpg'
        },
        'contacts': [
            {'name': 'Zhanzhang Cai, Lund University, Sweden', 'email': 'zhanzhang.cai@nateko.lu.se'},
            {'name': 'Lars Eklundh, Lund University, Sweden', 'email': 'lars.eklundh@nateko.lu.se'},
            {'name': 'Per Jonsson, Malmö University, Sweden', 'email': 'per.jonsson@mah.se'}
        ],
        'website_url': 'https://github.com/TIMESAT'
    }

    # Additional information: number of CPU cores and available memory
    number_of_cores = os.cpu_count()
    total_memory = psutil.virtual_memory().total / (1024 ** 3)  # Convert bytes to GB
    default_temp_dir = tempfile.gettempdir()
    session['ray_dir'] = default_temp_dir

    return render_template('mainapp.html', **info, runcores=number_of_cores, runmemory=total_memory, tempfolder=default_temp_dir)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/quitapp", methods=["POST"])
def quit_app():
    return "Thank you for using TIMESAT!"

if __name__ == '__main__':
    import webbrowser
    import threading

    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000/")

    # open the browser after the server starts
    threading.Timer(1.0, open_browser).start()

    app.run(threaded=True)
