from flask import Flask, render_template, request
import os
import calendar
from datetime import date, datetime
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/create')
def create():
    return  render_template('calculator.html')


@app.route('/bmi', methods=["GET", "POST"])
def bmi_calculator():
    if request.method == "POST":
        weight = request.form.get("weight", "").strip()
        height = request.form.get("height", "").strip()

        if weight == "" or height == "":
            return render_template("bmi.html", result_message="Please input weight and height")

        try:
            weight = float(weight)
            height = float(height)
        except ValueError:
            return render_template("bmi.html", result_message="Please enter valid numbers")

        if weight <= 0 or height <= 0:
            return render_template("bmi.html", result_message="Weight and height must be greater than zero")

        height_in_meters = height / 100
        bmi = weight / (height_in_meters * height_in_meters)

        if bmi < 18.5:
            category = "Underweight"
        elif bmi < 25:
            category = "Normal weight"
        elif bmi < 30:
            category = "Overweight"
        else:
            category = "Obesity"

        return render_template("bmi.html", bmi_result=round(bmi, 2), bmi_category=category)

    return render_template("bmi.html")


@app.route('/unit-converter', methods=["GET", "POST"])
def unit_converter():
    units_by_category = {
        "length": [
            ("mm", "Millimeter (mm)"),
            ("cm", "Centimeter (cm)"),
            ("m", "Meter (m)"),
            ("km", "Kilometer (km)"),
            ("in", "Inch (in)"),
            ("ft", "Foot (ft)"),
            ("yd", "Yard (yd)"),
            ("mi", "Mile (mi)")
        ],
        "weight": [
            ("mg", "Milligram (mg)"),
            ("g", "Gram (g)"),
            ("kg", "Kilogram (kg)"),
            ("lb", "Pound (lb)"),
            ("oz", "Ounce (oz)")
        ],
        "temperature": [
            ("c", "Celsius (C)"),
            ("f", "Fahrenheit (F)"),
            ("k", "Kelvin (K)")
        ],
        "pressure": [
            ("pa", "Pascal (Pa)"),
            ("kpa", "Kilopascal (kPa)"),
            ("bar", "Bar"),
            ("atm", "Atmosphere (atm)"),
            ("psi", "PSI")
        ]
    }

    selected_category = "length"
    selected_from = "m"
    selected_to = "cm"
    input_value = ""

    if request.method == "POST":
        selected_category = request.form.get("category", "length").strip()
        selected_from = request.form.get("from_unit", "").strip()
        selected_to = request.form.get("to_unit", "").strip()
        input_value = request.form.get("value", "").strip()

        if selected_category not in units_by_category:
            return render_template(
                "unit_converter.html",
                error_message="Please select a valid unit category",
                units_by_category=units_by_category,
                selected_category=selected_category,
                selected_from=selected_from,
                selected_to=selected_to,
                input_value=input_value
            )

        allowed_units = [u[0] for u in units_by_category[selected_category]]
        if selected_from not in allowed_units or selected_to not in allowed_units:
            return render_template(
                "unit_converter.html",
                error_message="Please select valid units for the selected category",
                units_by_category=units_by_category,
                selected_category=selected_category,
                selected_from=selected_from,
                selected_to=selected_to,
                input_value=input_value
            )

        if input_value == "":
            return render_template(
                "unit_converter.html",
                error_message="Please enter a value to convert",
                units_by_category=units_by_category,
                selected_category=selected_category,
                selected_from=selected_from,
                selected_to=selected_to,
                input_value=input_value
            )

        try:
            value = float(input_value)
        except ValueError:
            return render_template(
                "unit_converter.html",
                error_message="Please enter a valid number",
                units_by_category=units_by_category,
                selected_category=selected_category,
                selected_from=selected_from,
                selected_to=selected_to,
                input_value=input_value
            )

        if selected_category == "temperature":
            if selected_from == "c":
                celsius = value
            elif selected_from == "f":
                celsius = (value - 32) * 5 / 9
            else:
                celsius = value - 273.15

            if selected_to == "c":
                converted_value = celsius
            elif selected_to == "f":
                converted_value = (celsius * 9 / 5) + 32
            else:
                converted_value = celsius + 273.15
        else:
            factors = {
                "length": {
                    "mm": 0.001, "cm": 0.01, "m": 1, "km": 1000,
                    "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mi": 1609.344
                },
                "weight": {
                    "mg": 0.000001, "g": 0.001, "kg": 1, "lb": 0.45359237, "oz": 0.028349523125
                },
                "pressure": {
                    "pa": 1, "kpa": 1000, "bar": 100000, "atm": 101325, "psi": 6894.757293168
                }
            }
            from_factor = factors[selected_category][selected_from]
            to_factor = factors[selected_category][selected_to]
            converted_value = value * from_factor / to_factor

        return render_template(
            "unit_converter.html",
            units_by_category=units_by_category,
            selected_category=selected_category,
            selected_from=selected_from,
            selected_to=selected_to,
            input_value=input_value,
            converted_value=round(converted_value, 6)
        )

    return render_template(
        "unit_converter.html",
        units_by_category=units_by_category,
        selected_category=selected_category,
        selected_from=selected_from,
        selected_to=selected_to,
        input_value=input_value
    )


def _birthday_for_year(birthdate, year):
    if birthdate.month == 2 and birthdate.day == 29 and not calendar.isleap(year):
        return date(year, 2, 28)
    return date(year, birthdate.month, birthdate.day)


@app.route('/age', methods=["GET", "POST"])
def age_calculator():
    if request.method == "POST":
        dob_str = request.form.get("dob", "").strip()

        if dob_str == "":
            return render_template("age.html", result_message="Please select your birth date")

        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except ValueError:
            return render_template("age.html", result_message="Invalid date format", dob_value=dob_str)

        today = date.today()
        if dob > today:
            return render_template("age.html", result_message="Birth date cannot be in the future", dob_value=dob_str)

        years = today.year - dob.year
        months = today.month - dob.month
        days = today.day - dob.day

        if days < 0:
            prev_month = today.month - 1
            prev_year = today.year
            if prev_month == 0:
                prev_month = 12
                prev_year -= 1
            days += calendar.monthrange(prev_year, prev_month)[1]
            months -= 1

        if months < 0:
            months += 12
            years -= 1

        total_days = (today - dob).days
        total_weeks = total_days // 7
        total_months = years * 12 + months
        day_of_birth = dob.strftime("%A")

        next_birthday = _birthday_for_year(dob, today.year)
        if next_birthday < today:
            next_birthday = _birthday_for_year(dob, today.year + 1)

        days_until_birthday = (next_birthday - today).days
        age_on_next_birthday = years + 1

        return render_template(
            "age.html",
            dob_value=dob_str,
            age_years=years,
            age_months=months,
            age_days=days,
            total_months=total_months,
            total_weeks=total_weeks,
            total_days=total_days,
            day_of_birth=day_of_birth,
            next_birthday=next_birthday.strftime("%d %b %Y"),
            days_until_birthday=days_until_birthday,
            age_on_next_birthday=age_on_next_birthday
        )

    return render_template("age.html")


@app.route("/calculate", methods=["POST"])
def calculate():
    num1 = request.form.get("num1", "").strip()
    num2 = request.form.get("num2", "").strip()
    operation = request.form.get("operation", "")

    if num1 == "" or num2 == "":
        return render_template("calculator.html", result="Please input the numbers")

    try:
        num1 = float(num1)
        num2 = float(num2)
    except ValueError:
        return render_template("calculator.html", result="Please enter valid numbers")

    if operation == "add":
        result = num1 + num2
    elif operation == "sub":
        result = num1 - num2
    elif operation == "mul":
        result = num1 * num2
    elif operation == "div":
        if num2 == 0:
            return render_template("calculator.html", result="Cannot divide by zero")
        result = num1 / num2
    else:
        result = "Invalid operation"

    return render_template("calculator.html", result=result)

if __name__ == '__main__':
    app.run(debug=True,port=int(os.environ.get('PORT', 5000)))


    
