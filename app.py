from flask import Flask, render_template, request
import os
app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/create')
def create():
    return  render_template('calculator.html')

@app.route("/calculate", methods=["POST"])
def calculate():

    num1 = float(request.form["num1"])
    num2 = float(request.form["num2"])
    operation = request.form["operation"]

    if operation == "add":
        result = num1 + num2

    elif operation == "sub":
        result = num1 - num2

    elif operation == "mul":
        result = num1 * num2

    elif operation == "div":
        result = num1 / num2

    return render_template('calculator.html',result=result)

if __name__ == '__main__':
    app.run(debug=True,port=int(os.environ.get('PORT', 5000)))


    