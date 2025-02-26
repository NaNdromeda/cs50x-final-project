from cs50 import SQL
from datetime import date
from flask import Flask, redirect, render_template, request, jsonify
import json

app = Flask(__name__)

db = SQL("sqlite:///project.db")


@app.route("/pantry", methods=["GET","POST"])
def pantry():
    ingredients = db.execute("SELECT * FROM ingredients")
    pantry = db.execute("SELECT * FROM pantry")
    if request.method == "GET":
        return render_template("pantry.html", ingredients=ingredients, pantry=pantry)
    if request.method == "POST":
        if "add_to_pantry" in request.form:
            if request.form.get("ingredient") == "":
                print("Input valid ingredient")
                return render_template("pantry.html", ingredients=ingredients, pantry=pantry)
            if request.form.get("measurement") == "0":
                print("Input a number to add to pantry")
                return render_template("pantry.html", ingredients=ingredients, pantry=pantry)
            else:
                for row in ingredients:
                    if row["name"].lower() == request.form.get("ingredient").lower():
                        db.execute("INSERT INTO pantry (ingredient_id, quantity, quantity_measurement) VALUES (?, ?, ?)", row["id"], request.form.get("quantity"), request.form.get("measurement"))
                        updated_pantry = db.execute("SELECT * FROM pantry")
                        return render_template("pantry.html", ingredients=ingredients, pantry=updated_pantry)
                db.execute("INSERT INTO ingredients (name) VALUES (?)", request.form.get("ingredient"))
                ingredient_name = db.execute("SELECT id, name FROM ingredients WHERE name = ?", request.form.get("ingredient"))
                db.execute("INSERT INTO pantry (ingredient_id, quantity, quantity_measurement) VALUES (?, ?, ?)", ingredient_name[0]["id"], request.form.get("quantity"), request.form.get("measurement"))
                updated_ingredients = db.execute("SELECT * FROM ingredients")
                updated_pantry = db.execute("SELECT * FROM pantry")
                return render_template("pantry.html", ingredients=updated_ingredients, pantry=updated_pantry)
        elif "add_to_shopping" in request.form:
            if request.form.get("ingredient") == None:
                print("Input valid ingredient")
            else:
                for row in ingredients:
                    if row["name"].lower() == request.form.get("ingredient").lower() and row["to_buy"] == 0:
                        db.execute("UPDATE ingredients SET to_buy = 1 WHERE name = ?", request.form.get("ingredient").lower())
                        updated_ingredients = db.execute("SELECT * FROM ingredients")
                        return render_template("pantry.html", ingredients=updated_ingredients, pantry=pantry)
                    if row["name"].lower() == request.form.get("ingredient").lower() and row["to_buy"] == 1:
                        return render_template("pantry.html", ingredients=ingredients, pantry=pantry)
                db.execute("INSERT INTO ingredients (name, to_buy) VALUES (?, 1)", request.form.get("ingredient"))
                updated_ingredients = db.execute("SELECT * FROM ingredients")
                return render_template("pantry.html", ingredients=updated_ingredients, pantry=pantry)

@app.route("/pantry/searchpantry", methods=["GET","POST"])
def pantry_search():
    query = request.args.get("query")
    if query:
        pantry_ingredients = db.execute("SELECT * FROM pantry JOIN (SELECT name, category, id AS ingredients_id FROM ingredients) ON ingredient_id=ingredients_id WHERE name LIKE ? ORDER BY category, ingredient_id", "%" + query + "%")
        return jsonify(pantry_ingredients)
    else:
        pantry_ingredients = db.execute("SELECT * FROM pantry JOIN (SELECT name, category, id AS ingredients_id FROM ingredients) ON ingredient_id=ingredients_id ORDER BY category, ingredient_id")
        return jsonify(pantry_ingredients)

@app.route("/shoppinglist", methods=["GET", "POST"])
def shoppinglist():
    if request.method == "GET":
        checklist = db.execute("SELECT * FROM ingredients LEFT JOIN (SELECT id AS price_id, price.ingredient_id AS price_ingredient_id, price, date FROM price JOIN (SELECT ingredient_id, MAX(date) AS maxdate FROM price GROUP BY ingredient_id) AS max_date ON date=max_date.maxdate AND price_ingredient_id=max_date.ingredient_id) AS current_price ON ingredients.id=price_ingredient_id WHERE to_buy = 1")
        return render_template("shoppinglist.html", checklist=checklist)
    if request.method == "POST":
        data = request.get_json()
        pantry_object_array = data['pantry']
        price_object_array = data['price']
        print(price_object_array)
        if pantry_object_array:
            for pantry_object in pantry_object_array:
                id = pantry_object['ingredient_id']
                quantity = pantry_object['quantity']
                quantity_measurement = pantry_object['quantity_measurement']
                db.execute("INSERT INTO pantry (ingredient_id, quantity, quantity_measurement, last_purchased_ingredient) VALUES (?, ?, ?, ?)", id, quantity, quantity_measurement, date.today())
                db.execute("UPDATE ingredients SET to_buy = 0 WHERE id = ?", id)
        if price_object_array:
            for price_object in price_object_array:
                id = price_object['ingredient_id']
                price = price_object['price']
                db.execute("INSERT INTO price (ingredient_id, price, date) VALUES (?, ?, ?)", id, price, date.today())
        ingredients = db.execute("SELECT * FROM ingredients")
        pantry = db.execute("SELECT * FROM pantry")
        return render_template("pantry.html", ingredients=ingredients, pantry=pantry)

@app.route("/recipes", methods=["GET"])
def test():
    recipe = db.execute("SELECT * FROM recipe")
    recipe_steps = db.execute("SELECT * FROM recipe JOIN (SELECT recipe_step_number, recipe_step_instructions, recipe_id AS recipe_steps_recipe_id FROM recipe_steps) ON recipe.id = recipe_steps_recipe_id ORDER BY recipe.id, recipe_step_number")
    recipe_ingredients = db.execute("SELECT * FROM recipe JOIN (SELECT name, ingredient_id, ingredient_quantity, unit_measurement, ingredient_optional, recipe_id AS ingredients_recipe_id FROM recipe_ingredients JOIN (SELECT id AS ingredients_id, name FROM ingredients) ON recipe_ingredients.ingredient_id = ingredients_id) AS ingredients_with_names ON recipe.id = ingredients_with_names.ingredients_recipe_id")
    pantry = db.execute("SELECT name FROM pantry JOIN ingredients ON pantry.ingredient_id = ingredients.id")
    return render_template("recipes.html", recipe=recipe, recipe_ingredients=recipe_ingredients, recipe_steps=recipe_steps, pantry=pantry)

@app.route("/update", methods=["POST"])
def update():
    if list(request.get_json().keys())[0] == 'id':
        db.execute("DELETE FROM pantry WHERE id = ?", request.get_json().get('id'))
        return {"success":True}
    if list(request.get_json().keys())[0] == 'quantity':
        db.execute("UPDATE pantry SET quantity = ? WHERE id = ?", request.get_json().get('quantity'), request.get_json().get('id'))
        return {"success":True}
    if list(request.get_json().keys())[0] == 'last_purchased_ingredient':
        db.execute("UPDATE pantry SET last_purchased_ingredient = ? WHERE id = ?", request.get_json().get('last_purchased_ingredient'), request.get_json().get('id'))
        return {"success":True}

@app.route("/")
def index():
    return redirect("/pantry")



