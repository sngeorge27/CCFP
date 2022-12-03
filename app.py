from flask import Flask, render_template, redirect, url_for, request
app = Flask(__name__)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        return redirect(url_for('dashboard'))
    return render_template('login.html', error=error)

if __name__ == '__main__':
    app.run(debug=True)
