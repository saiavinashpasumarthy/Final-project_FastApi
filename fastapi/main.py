from fastapi import FastAPI , HTTPException
from pydantic import BaseModel, Field
app = FastAPI()
@app.get("/")
def read_root():
    return {"message": "welcome to Quickbite food delivery app"}
#menu card
menu = [
    {"id": 1, "name": "Pizza", "price": 10.99, "category": "Main Course","is_available": True},
    {"id": 2, "name": "Burger", "price": 8.99, "category": "Main Course","is_available": True},
    {"id": 3, "name": "Pasta", "price": 12.99, "category": "Main Course","is_available": True},
    {"id": 4, "name": "Salad", "price": 6.99, "category": "Appetizer","is_available": True},
    {"id": 5, "name": "Fries", "price": 3.99, "category": "Appetizer","is_available": True},
    {"id": 6, "name": "Ice Cream", "price": 4.99, "category": "Dessert","is_available": True},
    {"id": 7, "name": "Cake", "price": 5.99, "category": "Dessert","is_available": True},
]
@app.get("/menu")
def get_menu():
    total_items = len(menu)
    return {"menu": menu, "total_items": total_items}
@app.get("/menu/summary")
def get_summary():
    total_items = len(menu)
    available_items = sum(1 for item in menu if item["is_available"])
    unavailable_items = total_items - available_items
    categories = set(item["category"] for item in menu)
    return {
        "total_items": total_items,
        "available_items": available_items,
        "unavailable_items": unavailable_items,
        "categories": list(categories)
    }
def filter_menu(category: str, max_price: float, is_available: bool):
    filtered_items = []
    for item in menu:
        if (item["category"].lower() == category.lower() and
            item["price"] <= max_price and
            item["is_available"] == is_available):
            filtered_items.append(item)
    return filtered_items
@app.get("/menu/filter")
def filter_menu_items(category: str, max_price: float, is_available: bool):
    filtered_items = filter_menu(category, max_price, is_available)
    return {"filtered_menu": filtered_items, "total_filtered_items": len(filtered_items)}
class NewMenuItem(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0)
    category: str = Field(min_length=1, max_length=30)
    is_available: bool = True
@app.post("/menu/add")
def add_menu_item(new_item: NewMenuItem):
    for item in menu:
        if item["name"].lower() == new_item.name.lower():
            raise HTTPException(status_code=400, detail="Menu item with this name already exists")
    new_id = max(item["id"] for item in menu) + 1 if menu else 1
    menu_item = {
        "id": new_id,
        "name": new_item.name,
        "price": new_item.price,
        "category": new_item.category,
        "is_available": new_item.is_available
    }
    menu.append(menu_item)
    #return with response status code 201 for created
    return {"message": "Menu item added successfully", "item_id": menu_item["id"]}, 201
#helper functions to find menu item by id
def find_menu_item(item_id: int):
    for item in menu:
        if item["id"] == item_id:
            return item
    return None
@app.get("/menu/search")
def search_menu(query: str):
    results = [item for item in menu if query.lower() in item["name"].lower()]
    return {"results": results}
@app.get("/menu/sort")
def sort_menu(sort_by: str, order: str):
    if sort_by not in ["price", "name", "category"]:
        return {"error": "Invalid sort_by value"}
    if order not in ["asc", "desc"]:
        return {"error": "Invalid order value"}
    sorted_menu = sorted(menu, key=lambda x: x[sort_by], reverse=(order == "desc"))
    return {"sorted_menu": sorted_menu}
@app.get("/menu/page")
def get_menu_page(page: int = 1, limit: int = 10):
    start = (page - 1) * limit
    return {"menu": menu[start:start + limit], "page": page, "limit": limit, "total_items": len(menu)}
@app.get("/menu/browse")
def browse_menu(item_name: str,sort_by: str = "price", order: str = "asc",page: int = 1, limit: int = 4):
    filtered_menu = [item for item in menu if item_name.lower() in item["name"].lower()]
    sorted_menu = sorted(filtered_menu, key=lambda x: x[sort_by], reverse=(order == "desc"))
    start = (page - 1) * limit
    return {"menu": sorted_menu[start:start + limit], "page": page, "limit": limit, "total_items": len(sorted_menu)}
@app.get("/menu/{item_id}")
def get_menu_item(item_id: int):
    item = find_menu_item(item_id)
    if item:
        return item
    return {"error": "Item not found"}
orders = []
order_counter = 1
@app.get("/orders")
def get_orders():
    order_count = len(orders)
    return {"orders": orders, "total_orders": order_count}
#pydantic model for order request
#customer name min length 3 and max length 50
class OrderRequest(BaseModel):
    item_id: int = Field(gt=0)
    quantity: int = Field(gt=0,le=20)
    customer_name: str = Field(min_length=3, max_length=50)
    customer_address: str= Field(min_length=10, max_length=100)
    order_type: str = Field(default="delivery", pattern="^(delivery|pickup)$")

def calculate_bill(price: float, quantity: int, order_type: str):
    if order_type == "delivery":
        delivery_fee = 30.0
        return price * quantity + delivery_fee
    return price * quantity

@app.post("/orders")
def place_order(order_request: OrderRequest):
    global order_counter
    item = find_menu_item(order_request.item_id)
    if not item:
        return {"error": "Item not found"}
    if item["is_available"] == False:
        return {"error": "Item is currently unavailable"}
    if order_type := order_request.order_type == "delivery":
        delivery_fee = 30.0
    order = {
        "id": order_counter,
        "item_id": order_request.item_id,
        "quantity": order_request.quantity,
        "price": item["price"],
        "total": calculate_bill(item["price"], order_request.quantity, order_request.order_type),
        "customer_name": order_request.customer_name,
        "customer_address": order_request.customer_address
    }
    orders.append(order)
    order_counter += 1
    return {"message": "Order placed successfully", "order_id": order["id"]}

@app.get("/orders/search")
def search_orders(customer_name: str):
    results = [order for order in orders if customer_name.lower() in order["customer_name"].lower()]
    return {"results": results}
@app.get("/orders/sort")
def sort_orders(price: float = None, order: str = "asc"):
    if price is not None:
        filtered_orders = [order for order in orders if order["price"] <= price]
    else:
        filtered_orders = orders
    sorted_orders = sorted(filtered_orders, key=lambda x: x["price"], reverse=(order == "desc"))
    return {"sorted_orders": sorted_orders}

@app.put("/menu/{item_id}")
def update_menu_item(item_id: int, is_available: bool = True, price: float = None):
    find_item = find_menu_item(item_id)
    if not find_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    find_item["is_available"] = is_available
    if price is not None:
        find_item["price"] = price
    return {"message": "Menu item updated successfully", "item_id": find_item["id"]}
@app.delete("/menu/{item_id}")
def delete_menu_item(item_id: int):
    find_item = find_menu_item(item_id)
    if not find_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    menu.remove(find_item)
    return {"message": "Menu item deleted successfully", "item_id": item_id}
cart = []
@app.post("/cart/add")
def add_to_cart(order_request: OrderRequest):
    item = find_menu_item(order_request.item_id)
    if not item:
        return {"error": "Item not found"}
    total = calculate_bill(item["price"], order_request.quantity, order_request.order_type)
    if order_request.item_id in [cart_item["item_id"] for cart_item in cart]:
        return {"error": "Item already in cart"}
    if item["is_available"] == False:
        return {"error": "Item is currently unavailable"}
    cart_item = {
        "item_id": order_request.item_id,
        "quantity": order_request.quantity,
        "price": item["price"],
        "total": total,
        "customer_name": order_request.customer_name,
        "customer_address": order_request.customer_address
    }
    cart.append(cart_item)
    return {"message": "Item added to cart successfully", "cart_item": cart_item}
@app.get("/cart")
def view_cart():
    if not cart:
        return {"message": "Cart is empty"}
    total_items = len(cart)
    total_cost = sum(item["total"] for item in cart)
    return {"cart": cart, "total_items": total_items, "total_cost including delivery charges": total_cost}
class checkoutRequest(BaseModel):
    customer_name: str = Field(min_length=3, max_length=50)
    customer_address: str= Field(min_length=10, max_length=100)
@app.post("/cart/checkout")
def checkout_cart(checkout_request: checkoutRequest):
    if not cart:
        return {"error": "Cart is empty"}
    total_cost = sum(item["total"] for item in cart)
    cart.clear()
    return {"customer_name": checkout_request.customer_name,"customer_address": checkout_request.customer_address, "message": "Checkout successful", "total_cost including delivery charges": total_cost}
@app.delete("/cart/{item_id}")
def remove_from_cart(item_id: int):
    for cart_item in cart:
        if cart_item["item_id"] == item_id:
            cart.remove(cart_item)
            return {"message": "Item removed from cart successfully", "item_id": item_id}
    return {"error": "Item not found in cart"}

# Run the application using: uvicorn main:app --reload
