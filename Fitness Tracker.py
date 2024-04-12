import sqlite3
import datetime
import requests
import config

# Modify the setup_database function with enhanced error handling
def setup_database():
    try:
        conn = sqlite3.connect('fitness_tracker.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS meals (
                            id INTEGER PRIMARY KEY,
                            name TEXT,
                            calories REAL,
                            protein REAL,
                            carbs REAL,
                            fats REAL,
                            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS workouts (
                            id INTEGER PRIMARY KEY,
                            date TEXT,
                            total_calories_burned REAL
                        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS workout_exercises (
                            id INTEGER PRIMARY KEY,
                            workout_id INTEGER,
                            name TEXT,
                            duration INTEGER,
                            calories_burned REAL,
                            FOREIGN KEY (workout_id) REFERENCES workouts(id)
                        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS recipes (
                            id INTEGER PRIMARY KEY,
                            name TEXT,
                            ingredients TEXT,
                            calories REAL,
                            protein REAL,
                            carbs REAL,
                            fats REAL
                        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS weight_history (
                            id INTEGER PRIMARY KEY,
                            date TEXT,
                            weight REAL
                        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS goal_information (
                            id INTEGER PRIMARY KEY,
                            current_weight REAL,
                            goal_weight REAL,
                            goal_protein_ratio REAL,
                            calories_difference REAL,
                            protein_difference REAL
                        )''')

        conn.commit()
        print("Database setup completed successfully!")
    except sqlite3.Error as e:
        print("Error setting up the database:", e)
    finally:
        conn.close()

# Function to display the main menu and handle user choices
def main_menu():
    while True:
        print("Fitness Tracker Main Menu")
        print("1. Log Meal")
        print("2. Log Workout")
        print("3. View Recipes")
        print("4. Log Weight")
        print("5. View Weight History")
        print("6. Calculate Difference in Calories and Proteins for Goal Weight")
        print("7. View Meals")
        print("8. Log Recipe")
        print("9. Exit")

        choice = input("Enter your choice: ")
        if choice == '1':
            log_meal()
        elif choice == '2':
            log_workout()
        elif choice == '3':
            view_recipes()
        elif choice == '4':
            log_weight()
        elif choice == '5':
            view_weight_history()
        elif choice == '6':
            calculate_goal_difference()
        elif choice == '7':
            view_meals()
        elif choice == '8':
            log_recipe()
        elif choice == '9':
            print("Exiting program...")
            exit()
        else:
            print("Invalid choice. Please try again.")



# Function to log a meal
def log_meal():
    print("Log Meal:")
    while True:
        print("1. Use Existing Recipe")
        print("2. Create New Recipe")
        choice = input("Enter your choice: ")

        if choice == '1':
            # Use Existing Recipe
            view_recipes()
            recipe_id = input("Enter the ID of the recipe you want to use: ")
            # Retrieve the selected recipe from the database
            recipe = get_recipe_by_id(recipe_id)
            if recipe:
                save_meal(recipe)
                break
            else:
                print("Recipe not found.")
        elif choice == '2':
            # Create New Recipe
            recipe = create_new_recipe()
            if recipe:
                save_meal(recipe)
                break
        else:
            print("Invalid choice. Please enter '1' or '2'.")

def get_recipe_by_id(recipe_id):
    # Connect to the database
    conn = sqlite3.connect('fitness_tracker.db')
    cursor = conn.cursor()
    
    # Retrieve the selected recipe from the database
    cursor.execute('''
        SELECT * FROM recipes WHERE id = ?
    ''', (recipe_id,))
    recipe = cursor.fetchone()
    
    conn.close()
    return recipe

def create_new_recipe():
    name = input("Enter the name of the new recipe: ")
    ingredients = input("Enter the ingredients (separated by commas): ").split(',')
    # Fetch nutritional information for each ingredient
    ingredients_info = []
    for ingredient in ingredients:
        ingredient_info = fetch_nutritional_info(ingredient.strip())
        if ingredient_info:
            ingredients_info.append(ingredient_info)
        else:
            print(f"Could not find nutritional information for {ingredient.strip()}. Skipping.")
            return None
    # Calculate total nutritional information for the recipe
    total_calories = sum(ingredient_info.get('calories', 0) for ingredient_info in ingredients_info)
    total_protein = sum(ingredient_info.get('protein', 0) for ingredient_info in ingredients_info)
    total_carbs = sum(ingredient_info.get('carbs', 0) for ingredient_info in ingredients_info)
    total_fats = sum(ingredient_info.get('fat', 0) for ingredient_info in ingredients_info)
    
    # Return the recipe details
    return (name, ','.join(ingredients), total_calories, total_protein, total_carbs, total_fats)

def fetch_nutritional_info(ingredient):
    try:
        api_key = config.API_KEY
        api_url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={api_key}&query={ingredient}"
        
        response = requests.get(api_url)
        response.raise_for_status()

        data = response.json()
        if 'foods' in data and data['foods']:
            food_item = data['foods'][0]
            nutritional_info = {
                'calories': food_item['foodNutrients'][3]['value'],
                'protein': food_item['foodNutrients'][0]['value'],
                'carbs': food_item['foodNutrients'][1]['value'],
                'fat': food_item['foodNutrients'][2]['value']
            }
            return nutritional_info
        else:
            return f"No nutritional information found for {ingredient}."
    except requests.RequestException as e:
        return f"Error fetching nutritional information for {ingredient}: {e}"
    except (KeyError, IndexError) as e:
        return f"Error parsing nutritional information for {ingredient}: {e}"

# Function to view logged meals
def view_meals():
    # Connect to the database
    conn = sqlite3.connect('fitness_tracker.db')
    cursor = conn.cursor()

    # Retrieve logged meals from the database
    cursor.execute('''
        SELECT * FROM meals
    ''')
    meals = cursor.fetchall()

    # Check if there are any logged meals
    if not meals:
        print("No meals logged yet.")
        return

    # Display the logged meals
    print("Logged Meals:")
    print("ID\tName\tCalories\tProtein\tCarbs\tFats")
    for meal in meals:
        print(f"{meal[0]}\t{meal[1]}\t{meal[2]}\t{meal[3]}\t{meal[4]}\t{meal[5]}")

    conn.close()



# Function to retrieve MET value of an exercise from an API
def get_met_from_api(exercise_name):
    # Construct the API URL to search for the exercise by name
    url = f"https://wger.de/api/v2/exercise/?name={exercise_name}"
    # Send a GET request to the API
    response = requests.get(url)
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        # Check if any exercises match the provided name
        if data["count"] > 0:
            # Retrieve the first exercise (assuming it's the most relevant)
            exercise = data["results"][0]
            # Return the MET value of the exercise
            return exercise["met"]
    return None

# Function to calculate calories burned during an exercise
def calculate_calories_burned(exercise_name, weight_kg, sets, reps_per_set):
    try:
        met_value = get_met_from_api(exercise_name)
        if met_value is not None:
            total_reps = sets * reps_per_set
            total_duration_minutes = total_reps * 10 / 60
            calories_burned_per_minute = met_value * weight_kg * (3.5 / 200)
            total_calories_burned = calories_burned_per_minute * total_duration_minutes
            return total_calories_burned
        else:
            return "Exercise not found."
    except Exception as e:
        return f"Error calculating calories burned: {e}"

# Function to log a workout, including multiple exercises
def log_workout():
    print("Log Workout:")
    total_calories_burned = 0
    exercise_details = []

    while True:
        exercise_name = input("Enter the name of the exercise (or type 'done' to finish): ")
        if exercise_name.lower() == 'done':
            break
        weight_kg = float(input("Enter your weight in kilograms: "))
        sets = int(input("Enter the number of sets: "))
        reps_per_set = int(input("Enter the number of reps per set: "))

        calories_burned = calculate_calories_burned(exercise_name, weight_kg, sets, reps_per_set)
        if isinstance(calories_burned, str):  # Check if calories_burned is an error message
            print(calories_burned)
            continue

        exercise_details.append((exercise_name, sets * reps_per_set, calories_burned))
        total_calories_burned += calories_burned

    log_workout_to_database(exercise_details, total_calories_burned)

# Function to log the workout details into the database
def log_workout_to_database(exercise_details, total_calories_burned):
    try:
        conn = sqlite3.connect('fitness_tracker.db')
        cursor = conn.cursor()

        # Start a transaction
        conn.execute('BEGIN TRANSACTION')
        
        try:
            # Insert total calories burned for the workout into the database
            cursor.execute("INSERT INTO workouts (date, total_calories_burned) VALUES (?, ?)", (datetime.date.today(), total_calories_burned))
            workout_id = cursor.lastrowid

            # Insert exercise details into the database with the associated workout ID
            for exercise in exercise_details:
                cursor.execute("INSERT INTO workout_exercises (workout_id, name, duration, calories_burned) VALUES (?, ?, ?, ?)", (workout_id, *exercise))

            conn.commit()
            print("Workout logged successfully!")
        except sqlite3.Error as e:
            print("Error logging workout:", e)
            conn.rollback()  # Rollback the transaction in case of an error
        finally:
            conn.close()
    except sqlite3.Error as e:
        print("Error connecting to the database:", e)



# Function to view saved recipes
def view_recipes():
    try:
        # Connect to the database
        conn = sqlite3.connect('fitness_tracker.db')
        cursor = conn.cursor()
        try:
            # Retrieve recipes from the database
            cursor.execute('''
                SELECT id, name FROM recipes
            ''')
            recipes = cursor.fetchall()

            # Check if there are any recipes
            if not recipes:
                print("No recipes found.")
                return

            # Display the list of recipes
            print("Recipes:")
            for recipe in recipes:
                print(f"{recipe[0]}. {recipe[1]}")

            # Prompt user to select a recipe for detailed view
            recipe_id = input("Enter the ID of the recipe you want to view, or type 'back' to return to the main menu: ")

            if recipe_id.lower() == 'back':
                return

            # Retrieve the selected recipe from the database
            cursor.execute('''
                SELECT * FROM recipes WHERE id = ?
            ''', (recipe_id,))
            selected_recipe = cursor.fetchone()

            # Check if the recipe exists
            if selected_recipe:
                print("\nSelected Recipe:")
                print(f"Name: {selected_recipe[1]}")
                print("Ingredients:")
                print(selected_recipe[2])
                print("Nutritional Information:")
                print(f"Calories: {selected_recipe[3]}")
                print(f"Protein: {selected_recipe[4]}")
                print(f"Carbs: {selected_recipe[5]}")
                print(f"Fats: {selected_recipe[6]}")
            else:
                print("Recipe not found.")
        except sqlite3.Error as e:
            print("Error fetching recipes:", e)
        finally:
            conn.close()
    except sqlite3.Error as e:
        print("Error connecting to the database:", e)

# Function to log/add a recipe
def log_recipe():
    try:
        name = input("Enter the name of the recipe: ")

        # Validate name
        if not name:
            print("Recipe name cannot be empty.")
            return

        ingredients_input = input("Enter the ingredients (separated by commas): ")
        ingredients = [ingredient.strip() for ingredient in ingredients_input.split(',') if ingredient.strip()]

        # Validate ingredients
        if not ingredients:
            print("Please provide at least one ingredient.")
            return

        # Fetch nutritional information for each ingredient
        ingredients_info = []
        for ingredient in ingredients:
            ingredient_info = fetch_nutritional_info(ingredient)
            if ingredient_info:
                ingredients_info.append(ingredient_info)
            else:
                print(f"Could not find nutritional information for {ingredient}. Please try again.")
                return

        # Calculate total nutritional information for the recipe
        total_calories = sum(ingredient_info.get('calories', 0) for ingredient_info in ingredients_info)
        total_protein = sum(ingredient_info.get('protein', 0) for ingredient_info in ingredients_info)
        total_carbs = sum(ingredient_info.get('carbs', 0) for ingredient_info in ingredients_info)
        total_fats = sum(ingredient_info.get('fat', 0) for ingredient_info in ingredients_info)

        # Connect to the database
        try:
            conn = sqlite3.connect('fitness_tracker.db')
            cursor = conn.cursor()

            # Insert the recipe into the recipes table
            cursor.execute('''
                INSERT INTO recipes (name, ingredients, calories, protein, carbs, fats)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, ','.join(ingredients), total_calories, total_protein, total_carbs, total_fats))

            conn.commit()
            print("Recipe logged successfully!")
        except sqlite3.Error as e:
            print("Error logging recipe:", e)
        finally:
            conn.close()
    except ValueError as e:
        print("Error:", e)



def log_weight():
    try:
        # Get current date
        today_date = datetime.date.today().strftime("%Y-%m-%d")

        # Get weight from user input with input validation
        weight = float(input("Enter your weight (kg): "))
        if weight <= 0:
            print("Weight must be a positive number.")
            return

        # Connect to the database
        conn = sqlite3.connect('fitness_tracker.db')
        cursor = conn.cursor()

        # Insert weight data into the weight history table
        cursor.execute('''
            INSERT INTO weight_history (date, weight)
            VALUES (?, ?)
        ''', (today_date, weight))

        # Recalculate goal difference
        recalculate_goal_difference(conn, cursor)

        conn.commit()
        conn.close()

        print("Weight logged successfully!")
    except ValueError:
        print("Invalid input. Please enter a valid weight (e.g., 70.5).")
    except sqlite3.Error as e:
        print("Error:", e)

# Function to view weight history
def view_weight_history():
    # Connect to the database
    conn = sqlite3.connect('fitness_tracker.db')
    cursor = conn.cursor()

    # Retrieve weight history from the database
    cursor.execute('''
        SELECT date, weight FROM weight_history ORDER BY date DESC
    ''')
    weight_history = cursor.fetchall()

    # Print weight history
    print("Weight History:")
    print("Date\t\tWeight (kg)")
    for entry in weight_history:
        print(f"{entry[0]}\t{entry[1]}")

    conn.close()



# Function to calculate Basal Metabolic Rate (BMR) using the Harris-Benedict equation
def calculate_bmr(weight, height, age, gender):
    if gender.lower() == 'male':
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    elif gender.lower() == 'female':
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    else:
        raise ValueError("Invalid gender. Please enter 'male' or 'female'.")
    return bmr

# Function to calculate Total Daily Energy Expenditure (TDEE) based on activity level
def calculate_tdee(bmr, activity_level):
    activity_factors = {
        'sedentary': 1.2,
        'lightly active': 1.375,
        'moderately active': 1.55,
        'very active': 1.725,
        'extra active': 1.9
    }
    if activity_level.lower() not in activity_factors:
        raise ValueError("Invalid activity level.")
    tdee = bmr * activity_factors[activity_level.lower()]
    return tdee

# Function to calculate protein requirements based on weight and fitness goals
def calculate_protein_requirement(weight, goal_weight, goal_protein_ratio):
    if goal_weight <= 0 or goal_protein_ratio <= 0:
        raise ValueError("Goal weight and goal protein ratio must be positive values.")
    protein_requirement = weight * goal_protein_ratio
    return protein_requirement

# Function to recalculate goal difference based on the latest weight entry
def recalculate_goal_difference(conn, cursor):
    # Retrieve the latest weight entry from the database
    cursor.execute('''
        SELECT weight FROM weight_history ORDER BY date DESC LIMIT 1
    ''')
    latest_weight = cursor.fetchone()[0]

    # Retrieve goal information from the database
    cursor.execute('''
        SELECT current_weight, goal_weight, goal_protein_ratio FROM goal_information ORDER BY id DESC LIMIT 1
    ''')
    goal_info = cursor.fetchone()

    if latest_weight and goal_info:
        current_weight, goal_weight, goal_protein_ratio = goal_info
        current_bmr = calculate_bmr(current_weight, height, age, gender)
        current_tdee = calculate_tdee(current_bmr, activity_level)
        current_protein_requirement = calculate_protein_requirement(current_weight, current_weight, goal_protein_ratio)

        goal_bmr = calculate_bmr(goal_weight, height, age, gender)
        goal_tdee = calculate_tdee(goal_bmr, activity_level)
        goal_protein_requirement = calculate_protein_requirement(goal_weight, goal_weight, goal_protein_ratio)

        calories_difference = goal_tdee - current_tdee
        protein_difference = goal_protein_requirement - current_protein_requirement

        # Update goal information in the database
        cursor.execute('''
            UPDATE goal_information
            SET current_weight = ?, calories_difference = ?, protein_difference = ?
            WHERE id = (SELECT id FROM goal_information ORDER BY id DESC LIMIT 1)
        ''', (latest_weight, calories_difference, protein_difference))

        conn.commit()

# Function to calculate the difference in calories and proteins needed to achieve the goal weight
def calculate_goal_difference():
    try:
        current_weight = float(input("Enter your current weight (kg): "))
        goal_weight = float(input("Enter your goal weight (kg): "))
        goal_protein_ratio = float(input("Enter your desired protein intake per kg of body weight (g): "))

        # Calculate BMR and TDEE for current weight
        gender = input("Enter your gender (male/female): ")
        height = float(input("Enter your height (cm): "))
        age = int(input("Enter your age: "))
        activity_level = input("Enter your activity level (sedentary/lightly active/moderately active/very active/extra active): ")

        current_bmr = calculate_bmr(current_weight, height, age, gender)
        current_tdee = calculate_tdee(current_bmr, activity_level)
        current_protein_requirement = calculate_protein_requirement(current_weight, current_weight, goal_protein_ratio)

        # Calculate BMR and TDEE for goal weight
        goal_bmr = calculate_bmr(goal_weight, height, age, gender)
        goal_tdee = calculate_tdee(goal_bmr, activity_level)
        goal_protein_requirement = calculate_protein_requirement(goal_weight, goal_weight, goal_protein_ratio)

        calories_difference = goal_tdee - current_tdee
        protein_difference = goal_protein_requirement - current_protein_requirement

        print(f"Difference in Calories Needed: {calories_difference:.2f} kcal")
        print(f"Difference in Proteins Needed: {protein_difference:.2f} g")
        print(f"Calories Needed: {goal_tdee:.2f} kcal")
        print(f"Proteins Needed: {goal_protein_requirement:.2f} g")
    except ValueError as e:
        print("Error:", e)



# Entry point of the program
if __name__ == "__main__":
    setup_database()  # Set up the database
    main_menu()  # Display the main menu
