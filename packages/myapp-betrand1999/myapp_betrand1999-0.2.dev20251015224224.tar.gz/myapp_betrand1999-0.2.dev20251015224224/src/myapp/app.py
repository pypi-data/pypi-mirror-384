from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def main():
    app.run(debug=True, host='0.0.0.0', port=8000)

if __name__ == '__main__':
    main()
