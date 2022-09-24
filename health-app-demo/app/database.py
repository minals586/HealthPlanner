"""Defines all the functions related to the database"""
from app import db
from flask import Flask, request, make_response, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from sqlalchemy import text, DDL


stored_procedure = DDL("""
DROP PROCEDURE IF EXISTS GetPersonalizedHealthPlan;
CREATE PROCEDURE GetPersonalizedHealthPlan(IN custid INTEGER)
BEGIN
    DECLARE varExerciseName VARCHAR(200);
    DECLARE varCaloriesBurned INTEGER;
    DECLARE varCalorieFloor INTEGER;
    DECLARE varCalorieCeiling INTEGER;
    DECLARE varAvgCaloriesBurned INTEGER;
    DECLARE varRecCalsBurned INTEGER;
    DECLARE varExerciseRec VARCHAR(200);
    DECLARE varExerciseType VARCHAR(200);
    DECLARE loopExit BOOLEAN DEFAULT FALSE;

    DECLARE cur CURSOR FOR (
        SELECT h.CalorieFloor, h.CalorieCeiling, e.ExerciseName, e.CaloriesBurned
		FROM Exercises e, Achieves a JOIN HealthGoals h ON (h.Goal = a.Goal) 
		WHERE a.CustomerID = custid
    );
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET loopExit=TRUE;
    
    DROP TABLE IF EXISTS ExerciseRecs;
    CREATE TABLE ExerciseRecs(
        CalorieFloor INTEGER,
        CalorieCeiling INTEGER,
        ExerciseName VARCHAR(200) PRIMARY KEY,
        CaloriesBurned INTEGER,
        ExerciseType VARCHAR(200)
    );
    
    SET varAvgCaloriesBurned = (SELECT AVG(e.CaloriesBurned)
								FROM Exercises e, Achieves a JOIN HealthGoals h ON (h.Goal = a.Goal)
                                WHERE a.CustomerID = custid
                                GROUP BY h.Goal);
    OPEN cur;
    cloop: LOOP
        FETCH cur INTO varCalorieFloor, varCalorieCeiling, varExerciseName, varCaloriesBurned; 
        IF loopExit THEN LEAVE cloop;
        END IF;
        
        SET varExerciseRec = (SELECT e.ExerciseName
							FROM Exercises e, Achieves a JOIN HealthGoals h ON (h.Goal = a.Goal) 
							WHERE a.CustomerID = custid AND e.CaloriesBurned > h.CalorieFloor AND e.ExerciseName in
							(SELECT e1.ExerciseName
							FROM Exercises e1, Achieves a1 JOIN HealthGoals h1 ON (h1.Goal = a1.Goal)
							WHERE a1.CustomerID = custid AND e1.CaloriesBurned > varAvgCaloriesBurned AND e1.CaloriesBurned < 1000)
							ORDER BY RAND()
							LIMIT 1);
		SET varRecCalsBurned = (SELECT e.CaloriesBurned
							FROM Exercises e
                            WHERE e.ExerciseName = varExerciseRec);
                            
		SET varExerciseType = "Beginner";
		IF varRecCalsBurned >= 450 THEN
            SET varExerciseType = "Advanced";
        ELSEIF varRecCalsBurned >= 400 THEN
            SET varExerciseType = "Intermediate";
        ELSE
            SET varExerciseType = "Beginner";
        END IF;

        INSERT IGNORE INTO ExerciseRecs VALUES (varCalorieFloor, varCalorieCeiling, varExerciseRec, varRecCalsBurned, varExerciseType);
    END LOOP cloop;
    CLOSE cur;
    
    SELECT * FROM ExerciseRecs ORDER BY RAND() LIMIT 20;
END;

""".replace("\n"," "))


trigger = DDL("""
DROP TRIGGER IF EXISTS MacroControl;
CREATE TRIGGER MacroControl
AFTER INSERT ON RestaurantOrder
FOR EACH ROW
BEGIN
    SET @goalName = (SELECT Goal
					FROM Achieves
                    WHERE CustomerID = new.CustomerID);
                    
    SET @varNumOrders = (SELECT COUNT(RestaurantID)
						FROM RestaurantOrder 
						WHERE CustomerID = new.CustomerID);
                        
   IF @varNumOrders > 3 THEN
		  UPDATE HealthGoals
		  SET TargetFat = TargetFat/2
		  WHERE Goal = @goalName;
   END IF;
  END;

""".replace("\n", " "))

def fetch_cust_info(customerid) -> dict:
    """Fetches the user input customer id

    Returns:
        The user's customer id
    """

    conn = db.connect()
    query_result = conn.execute("Select CustomerID,Name,Age,Weight,Height from Customers where CustomerID = %s;", customerid).fetchall()
    conn.close()
    if len(query_result) == 0: return {}
    result = query_result[0]
    cust_info = {
        "CustomerID": result[0],
        "Name": result[1],
        "Age": result[2],
        "Weight": result[3],
        "Height": result[4]
    }
    return cust_info

def fetch_health_goal(customerid) -> dict:
    """Fetches the user's current health goal

    Returns:
        The user's health goal
    """

    conn = db.connect()
    query_result = conn.execute("select a.CustomerID, a.Goal, h.CalorieCeiling, h.CalorieFloor, h.TargetWeight, h.TargetCarbs, h.TargetProtein, h.TargetFat from Achieves a JOIN HealthGoals h USING(Goal) where a.CustomerID = %s;", customerid).fetchall()
    conn.close()
    result = query_result[0]
    goal_info = {
        "CustomerID": result[0],
        "Goal": result[1],
        "CalorieCeiling": result[2],
        "CalorieFloor": result[3],
        "TargetWeight": result[4],
        "TargetCarbs": result[5],
        "TargetProtein": result[6],
        "TargetFat": result[7]
    }

    return goal_info

def fetch_exercises(customerid) -> list:
    
    conn = db.connect()
    results = conn.execute("CALL GetPersonalizedHealthPlan(%s)", customerid).fetchall()
    conn.close()
    query1 = []
    for result in results:
        order = {
            "CalFloor": result[0],
            "CalCeil": result[1],
            "ExcName": result[2],
            "CalBurned": result[3],
            "ExcType": result[4],


        }
        query1.append(order)
    return query1
    

def fetch_food_items(customerid) -> list:

    """ Returns:
        a list of dictionaries containing food item info for this customerid
    """

    conn = db.connect()
    # query_results = conn.execute("Select * from ConsumeItem WHERE ConsumeItem.CustomerId = %s;", customerid).fetchall()
    query_results = conn.execute("select c.CustomerID, c.ItemName, f.Calories, f.Carbs, f.Protein, f.Fat from ConsumeItem c JOIN FoodItems f USING(ItemName) where c.CustomerID = %s;", customerid).fetchall()

    conn.close()
    food_item_info = []
    for result in query_results:
        item = {
            "CustomerID": result[0],
            "ItemName": result[1],
            "Calories": result[2],
            "Carbs": result[3],
            "Protein": result[4],
            "Fat": result[5]
        }
        food_item_info.append(item)

    return food_item_info


def fetch_restaurant_orders(customerid) -> list:

    """ Returns:
        a list of dictionaries containing restaurant order info for this customerid
    """

    conn = db.connect()
    query_results = conn.execute("select r2.CustomerID, r1.RestaurantID, r1.RestaurantName, r1.Address from Restaurants r1 JOIN RestaurantOrder r2 USING(RestaurantID) where r2.CustomerID = %s;", customerid).fetchall()

    conn.close()
    rest_order_info = []
    for result in query_results:
        order = {
            "CustomerID": result[0],
            "RestaurantID": result[1],
            "RestaurantName": result[2],
            "Address": result[3]
        }
        rest_order_info.append(order)

    return rest_order_info


def fetch_query1() -> list:
    """Fetches a list of excercises that burn more than 400 calories (intense) or less than 100 calories (light)
    """
    conn = db.connect()
    query_results = conn.execute("SELECT e.ExerciseName, e.CaloriesBurned FROM Exercises e JOIN Performs p USING(ExerciseName) WHERE e.CaloriesBurned < 100 UNION SELECT e.ExerciseName, e.CaloriesBurned FROM Exercises e JOIN Performs p USING(ExerciseName) WHERE e.CaloriesBurned > 400 ORDER BY RAND();").fetchall()

    conn.close()
    query1 = []
    for result in query_results:
        order = {
            "ExcerciseName": result[0],
            "CaloriesBurned": result[1]
        }
        query1.append(order)

    return query1

def fetch_query2() -> list:
    """Fetches a list of people that are eating healthy! (which is tofy and chicekn)
    """
    conn = db.connect()
    query_results = conn.execute("SELECT c.CustomerID, c.Name, i.ItemName FROM Customers c JOIN ConsumeItem i USING(CustomerID) WHERE i.ItemName LIKE %s UNION SELECT c1.CustomerID, c1.Name,  i1.ItemName FROM Customers c1 JOIN ConsumeItem i1 USING(CustomerID) WHERE i1.ItemName LIKE %s ORDER BY ItemName DESC;", ('%' + 'tofu' + '%', '%' + 'chicken' + '%',)).fetchall()
    conn.close()
    query2 = []
    for result in query_results:
        order = {
            "CustomerID": result[0],
            "Name": result[1],
            "ItemName": result[2]
        }
        query2.append(order)

    return query2

def update_restaurant_order(RestaurantID, RestaurantName, Address) -> None:
    conn = db.connect()
    query = ''
    if RestaurantName == None:
        query = 'Update Restaurants set Address = "{}" where RestaurantID = {};'.format(Address, RestaurantID)
    elif Address == None:
        query = 'Update Restaurants set RestaurantName = "{}" where RestaurantID = {};'.format(RestaurantName, RestaurantID)
    else:
        query = 'Update Restaurants set RestaurantName = "{}", Address = "{}" where RestaurantID = {};'.format(RestaurantName, Address, RestaurantID)
    conn.execute(query)
    conn.close()

def insert_new_restaurant_order(CustomerID, RestaurantName, Address) ->  int:
    conn = db.connect()
    max_id = conn.execute('Select MAX(RestaurantID) from Restaurants;')
    max_id = [x for x in max_id]
    RestaurantID = max_id[0][0] + 1
    print(RestaurantID)
    query = 'Insert into Restaurants (RestaurantID, RestaurantName, Address) values ({}, "{}", "{}");'.format(RestaurantID, RestaurantName, Address)
    conn.execute(query)
    
    query2 = 'Insert into RestaurantOrder (CustomerID, RestaurantID) values ({}, {});'.format(CustomerID, RestaurantID)
    conn.execute(query2)
    conn.close()

    return RestaurantID

def remove_restaurant_order(RestaurantID, CustomerID) -> None:
    """ remove entries based on task ID """
    conn = db.connect()
    query = 'Delete From RestaurantOrder where RestaurantID={} and CustomerID={};'.format(RestaurantID, CustomerID)
    conn.execute(query)
    conn.close()
