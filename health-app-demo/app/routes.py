""" Specifies routing for the application"""
from flask import render_template, request, jsonify, redirect, url_for
from app import app
from app import database as db_helper

customerid = -1

@app.route("/edit/<int:RestaurantID>", methods=['POST'])
def update(RestaurantID):
    """ recieved post requests for entry updates """

    data = request.get_json()

    try:
        if "RestaurantName" in data and 'Address' in data:
            if len(data["RestaurantName"]) != 0 and len(data['Address']) != 0:
                db_helper.update_restaurant_order(RestaurantID, data['RestaurantName'], data['Address'])
                result = {'success': True, 'response': 'Name and Address Updated'}
            elif len(data["RestaurantName"]) != 0:
                db_helper.update_restaurant_order(RestaurantID, data['RestaurantName'], None)
                result = {'success': True, 'response': 'Name Updated'}
            elif len(data['Address']) != 0:
                db_helper.update_restaurant_order(RestaurantID, None, data['Address'])
                result = {'success': True, 'response': 'Address Updated'}
        else:
            result = {'success': True, 'response': 'Nothing Updated'}
    except:
        result = {'success': False, 'response': 'Something went wrong'}

    return jsonify(result)


@app.route("/create", methods=['POST'])
def create():
    """ recieves post requests to add new task """
    data = request.get_json()
    # insert new restaurant and new restaurant order
    print(customerid)
    db_helper.insert_new_restaurant_order(customerid, data['RestaurantName'], data['Address'])
    result = {'success': True, 'response': 'Done'}
    return jsonify(result)

# Route for handling the customer id input logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        global customerid
        customerid = request.form.get('custid')
        if int(customerid) < 0 or int(customerid) > 1000:
            error = 'Invalid Customer ID. Please try again.'
            return redirect(url_for('login'))
        else:
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


@app.route("/index")
def index():
    """ returns rendered homepage """
    # items = db_helper.fetch_todo()
    # food_items = db_helper.fetch_food_items(customerid)
    items = []
    cust_info = db_helper.fetch_cust_info(customerid)
    health_goals = db_helper.fetch_health_goal(customerid)
    rest_orders = db_helper.fetch_restaurant_orders(customerid)
    # query1 = db_helper.fetch_query1()
    # query2 = db_helper.fetch_query2()

    items.append(cust_info)
    items.append(health_goals)
    items.append(rest_orders)
    # items.append(query1)
    # items.append(query2)
    return render_template("index.html", items=items)

@app.route("/")
def start():
    """ returns rendered start page """
    return render_template("login.html")

@app.route("/delete/<string:RestaurantID>/<string:CustomerID>", methods=['POST'])
def delete(RestaurantID, CustomerID):
    """ recieved post requests for entry delete """

    try:
        db_helper.remove_restaurant_order(int(RestaurantID), int(CustomerID))
        result = {'success': True, 'response': 'Removed task'}
    except:
        result = {'success': False, 'response': 'Something went wrong'}

    return jsonify(result)

@app.route("/exercise-query")
def get_exercises_in_calorie_range():
    items = db_helper.fetch_query1()
    return render_template("exercise-query.html", items=items)

@app.route("/food-query")
def get_foods_in_macro_range():
    items = db_helper.fetch_query2()
    return render_template("food-query.html", items=items)

@app.route("/get-personalized-plan")
def get_personalized_plan():
    items = db_helper.fetch_exercises(customerid)
    return render_template("get-personalized-plan.html", items=items)