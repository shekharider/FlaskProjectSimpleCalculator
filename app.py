from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import calendar
import os

app = Flask(__name__)

# --- Database config ---
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///history.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# --- Model ---
class CalculationHistory(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    tool        = db.Column(db.String(50), nullable=False)   # "calculator", "bmi", "unit_converter", "age"
    input_data  = db.Column(db.String(500), nullable=False)  # human-readable summary of inputs
    result      = db.Column(db.String(200), nullable=False)  # result as a string
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<History {self.tool} | {self.input_data} = {self.result}>"


# Create all tables on first run
with app.app_context():
    db.create_all()


# --- Helper ---
def save_history(tool, input_data, result):
    """Save a calculation to the database. Silently skips on error."""
    try:
        record = CalculationHistory(
            tool=tool,
            input_data=input_data,
            result=str(result)
        )
        db.session.add(record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[history] Failed to save: {e}")


# --- Routes ---

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/create")
def create():
    return render_template("calculator.html")


# --- History page ---
@app.route("/history")
def history():
    tool_filter = request.args.get("tool", "all")
    if tool_filter == "all":
        records = CalculationHistory.query.order_by(
            CalculationHistory.created_at.desc()
        ).limit(100).all()
    else:
        records = CalculationHistory.query.filter_by(tool=tool_filter).order_by(
            CalculationHistory.created_at.desc()
        ).limit(100).all()

    return render_template("history.html", records=records, tool_filter=tool_filter)


@app.route("/history/clear", methods=["POST"])
def clear_history():
    CalculationHistory.query.delete()
    db.session.commit()
    return render_template("history.html", records=[], tool_filter="all",
                           success_message="History cleared.")


# --- Calculator ---
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

    op_symbols = {"add": "+", "sub": "-", "mul": "×", "div": "÷"}

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
        return render_template("calculator.html", result="Invalid operation")

    symbol = op_symbols.get(operation, "?")
    save_history(
        tool="calculator",
        input_data=f"{num1} {symbol} {num2}",
        result=round(result, 6)
    )
    return render_template("calculator.html", result=result)


# --- BMI calculator ---
@app.route("/bmi", methods=["GET", "POST"])
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
            return render_template("bmi.html",
                                   result_message="Weight and height must be greater than zero")

        height_in_meters = height / 100
        bmi = weight / (height_in_meters ** 2)

        if bmi < 18.5:
            category = "Underweight"
        elif bmi < 25:
            category = "Normal weight"
        elif bmi < 30:
            category = "Overweight"
        else:
            category = "Obesity"

        save_history(
            tool="bmi",
            input_data=f"weight={weight}kg height={height}cm",
            result=f"{round(bmi, 2)} ({category})"
        )
        return render_template("bmi.html", bmi_result=round(bmi, 2), bmi_category=category)

    return render_template("bmi.html")


# --- Unit converter ---
@app.route("/unit-converter", methods=["GET", "POST"])
def unit_converter():
    units_by_category = {
        "length": [
            ("mm", "Millimeter (mm)"), ("cm", "Centimeter (cm)"),
            ("m", "Meter (m)"), ("km", "Kilometer (km)"),
            ("in", "Inch (in)"), ("ft", "Foot (ft)"),
            ("yd", "Yard (yd)"), ("mi", "Mile (mi)")
        ],
        "weight": [
            ("mg", "Milligram (mg)"), ("g", "Gram (g)"),
            ("kg", "Kilogram (kg)"), ("lb", "Pound (lb)"), ("oz", "Ounce (oz)")
        ],
        "temperature": [
            ("c", "Celsius (C)"), ("f", "Fahrenheit (F)"), ("k", "Kelvin (K)")
        ],
        "pressure": [
            ("pa", "Pascal (Pa)"), ("kpa", "Kilopascal (kPa)"),
            ("bar", "Bar"), ("atm", "Atmosphere (atm)"), ("psi", "PSI")
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

        def render_err(msg):
            return render_template(
                "unit_converter.html", error_message=msg,
                units_by_category=units_by_category,
                selected_category=selected_category,
                selected_from=selected_from,
                selected_to=selected_to, input_value=input_value
            )

        if selected_category not in units_by_category:
            return render_err("Please select a valid unit category")

        allowed_units = [u[0] for u in units_by_category[selected_category]]
        if selected_from not in allowed_units or selected_to not in allowed_units:
            return render_err("Please select valid units for the selected category")

        if input_value == "":
            return render_err("Please enter a value to convert")

        try:
            value = float(input_value)
        except ValueError:
            return render_err("Please enter a valid number")

        if selected_category == "temperature":
            celsius = (
                value if selected_from == "c"
                else (value - 32) * 5 / 9 if selected_from == "f"
                else value - 273.15
            )
            converted_value = (
                celsius if selected_to == "c"
                else (celsius * 9 / 5) + 32 if selected_to == "f"
                else celsius + 273.15
            )
        else:
            factors = {
                "length":  {"mm": 0.001, "cm": 0.01, "m": 1, "km": 1000,
                            "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mi": 1609.344},
                "weight":  {"mg": 0.000001, "g": 0.001, "kg": 1,
                            "lb": 0.45359237, "oz": 0.028349523125},
                "pressure":{"pa": 1, "kpa": 1000, "bar": 100000,
                            "atm": 101325, "psi": 6894.757293168}
            }
            converted_value = (value * factors[selected_category][selected_from]
                               / factors[selected_category][selected_to])

        save_history(
            tool="unit_converter",
            input_data=f"{value} {selected_from} to {selected_to} ({selected_category})",
            result=round(converted_value, 6)
        )
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


# --- Age calculator ---
def _birthday_for_year(birthdate, year):
    if birthdate.month == 2 and birthdate.day == 29 and not calendar.isleap(year):
        return date(year, 2, 28)
    return date(year, birthdate.month, birthdate.day)


@app.route("/age", methods=["GET", "POST"])
def age_calculator():
    if request.method == "POST":
        dob_str = request.form.get("dob", "").strip()

        if dob_str == "":
            return render_template("age.html", result_message="Please select your birth date")

        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except ValueError:
            return render_template("age.html", result_message="Invalid date format",
                                   dob_value=dob_str)

        today = date.today()
        if dob > today:
            return render_template("age.html",
                                   result_message="Birth date cannot be in the future",
                                   dob_value=dob_str)

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

        total_days   = (today - dob).days
        total_weeks  = total_days // 7
        total_months = years * 12 + months
        day_of_birth = dob.strftime("%A")

        next_birthday = _birthday_for_year(dob, today.year)
        if next_birthday < today:
            next_birthday = _birthday_for_year(dob, today.year + 1)

        days_until_birthday  = (next_birthday - today).days
        age_on_next_birthday = years + 1

        save_history(
            tool="age",
            input_data=f"DOB={dob_str}",
            result=f"{years}y {months}m {days}d"
        )
        return render_template(
            "age.html",
            dob_value=dob_str,
            age_years=years, age_months=months, age_days=days,
            total_months=total_months, total_weeks=total_weeks, total_days=total_days,
            day_of_birth=day_of_birth,
            next_birthday=next_birthday.strftime("%d %b %Y"),
            days_until_birthday=days_until_birthday,
            age_on_next_birthday=age_on_next_birthday
        )

    return render_template("age.html")


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))