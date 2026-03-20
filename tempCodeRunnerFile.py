@app.route('/calculator', methods=[  'POST'])
def create():
    return  render_template('calculator.html')