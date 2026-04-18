from fastapi import FastAPI, HTTPException, Header
from typing import Optional
from pydantic import BaseModel

app = FastAPI(title="Shop API")


class Item(BaseModel):
    name: str
    price: float


class ItemInDB(Item):
    id: int


db: dict[int, ItemInDB] = {
    1: ItemInDB(id=1, name="Макбук", price=189900),
    2: ItemInDB(id=2, name="Айфон", price=99900),
    3: ItemInDB(id=3, name="Айпад", price=69900),
    4: ItemInDB(id=4, name="Эйрподс", price=19900),
}


@app.get("/")
def healthcheck():
    return {"status": "ok"}


@app.get("/items", response_model=list[ItemInDB])
def list_items():
    return list(db.values())


@app.get("/items/search", response_model=list[ItemInDB])
def search_items(name: str):
    # TODO: найди все товары, в названии которых есть подстрока name (без учёта регистра)
    # верни найденные товары как список
    search_name = name.lower()
    result = []

    for item in db.values():
        if search_name in item.name.lower():
            result.append(item)

    return result

@app.get("/items/expensive", response_model=list[ItemInDB])
def get_expensive_items(min_price: float):
    # TODO: найди все товары с ценой >= min_price
    # верни их как список
    result = []

    for item in db.values():
        if item.price >= min_price:
            result.append(item)

    return result


@app.get("/items/{item_id}", response_model=ItemInDB)
def get_item(item_id: int):
    # TODO: проверь наличие ключа в db и верни значение
    # если ключа нет - raise HTTPException(status_code=404, detail="Item not found")
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    return db[item_id]


@app.post("/items", response_model=ItemInDB, status_code=201)
def create_item(item: Item, authorization: Optional[str] = Header(None)):
    # TODO: проверь админа: require_admin(get_user_from_token(authorization))
    # сгенерируй новый id (max ключ в db + 1)
    # создай ItemInDB и добавь в db по ключу
    # верни созданный объект
    require_admin(get_user_from_token(authorization))

    new_id = max(db.keys()) + 1
    new_item = ItemInDB(id=new_id, name=item.name, price=item.price)

    db[new_id] = new_item
    return new_item


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int, authorization: Optional[str] = Header(None)):
    # TODO: проверь админа: require_admin(get_user_from_token(authorization))
    # проверь наличие ключа и удали элемент из db
    # если ключа нет - raise HTTPException(status_code=404, detail="Item not found")
    require_admin(get_user_from_token(authorization))

    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")

    del db[item_id]


@app.put("/items/{item_id}", response_model=ItemInDB)
def update_item(item_id: int, item: Item, authorization: Optional[str] = Header(None)):
    # TODO: проверь админа: require_admin(get_user_from_token(authorization))
    # проверь наличие ключа в db
    # если нет - raise HTTPException(status_code=404, detail="Item not found")
    # обнови name и price у существующего элемента
    # верни обновлённый объект
    require_admin(get_user_from_token(authorization))

    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")

    db[item_id].name = item.name
    db[item_id].price = item.price

    return db[item_id]


@app.get("/stats")
def get_stats(authorization: Optional[str] = Header(None)):
    # TODO: проверь админа: require_admin(get_user_from_token(authorization))
    # верни статистику: {"total_items": ..., "total_value": ...}
    # total_items — количество товаров в db
    # total_value — сумма цен всех товаров
    require_admin(get_user_from_token(authorization))

    total_items = len(db)
    total_value = 0

    for item in db.values():
        total_value += item.price

    return {
        "total_items": total_items,
        "total_value": total_value
    }


# --- Пользователи ---

class User(BaseModel):
    name: str
    email: str
    password: str
    is_admin: bool = False


class UserInDB(User):
    id: int


users_db: dict[int, UserInDB] = {
    1: UserInDB(id=1, name="Админ", email="admin@shop.com", password="admin123", is_admin=True),
    2: UserInDB(id=2, name="Клиент", email="customer@shop.com", password="user123", is_admin=False),
}


class LoginRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Авторизация ---

def get_user_from_token(authorization: Optional[str]) -> Optional[UserInDB]:
    # Извлечь email из заголовка "Bearer <email>"
    if not authorization or not authorization.startswith("Bearer "):
        return None
    email = authorization[7:]  # убрать "Bearer "
    for user in users_db.values():
        if user.email == email:
            return user
    return None


def require_admin(user: Optional[UserInDB]):
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")


# --- Пользователи ---

@app.get("/users", response_model=list[UserInDB])
def list_users():
    # TODO: верни все значения из users_db как список
    return list(users_db.values())


@app.get("/users/{user_id}", response_model=UserInDB)
def get_user(user_id: int, authorization: Optional[str] = Header(None)):
    # TODO: проверь админа: require_admin(get_user_from_token(authorization))
    # проверь наличие ключа в users_db и верни значение
    # если ключа нет - raise HTTPException(status_code=404, detail="User not found")
    require_admin(get_user_from_token(authorization))

    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]


@app.post("/users", response_model=UserInDB, status_code=201)
def create_user(user: User):
    # TODO: сгенерируй новый id (max ключ в users_db + 1)
    # создай UserInDB и добавь в users_db по ключу
    # верни созданный объект
    new_id = max(users_db.keys()) + 1
    new_user = UserInDB(
        id=new_id,
        name=user.name,
        email=user.email,
        password=user.password,
        is_admin=user.is_admin
    )

    user_db[new_id] = new_user
    return new_user

@app.post("/login")
def login(login_req: LoginRequest):
    # TODO: найди пользователя по email в users_db
    # если не найден - raise HTTPException(status_code=401, detail="Invalid credentials")
    # проверь пароль (простое сравнение)
    # если неверный - raise HTTPException(status_code=401, detail="Invalid credentials")
    # верни {"access_token": email, "token_type": "bearer"}
    pass


@app.get("/me", response_model=UserInDB)
def get_current_user(email: str):
    # TODO: найди пользователя по email в query параметре
    # если не найден - raise HTTPException(status_code=404, detail="User not found")
    # верни найденного пользователя
    found_user = None

    for user in users_db.values():
        if user.email == login_req.email:
            found_user = user
            break

    if found_user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if found_user.password != login_req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"access_token": found_user.email, "token_type": "bearer"}


# --- Корзина ---

class CartItem(BaseModel):
    item_id: int
    quantity: int


class CartItemInDB(CartItem):
    id: int


cart_db: dict[int, CartItemInDB] = {}


@app.get("/cart", response_model=list[CartItemInDB])
def get_cart(authorization: Optional[str] = Header(None)):
    # TODO: верни все значения из cart_db как список
    # проверь авторизацию: user = get_user_from_token(authorization)
    # если нет пользователя - raise HTTPException(status_code=401, detail="Authorization required")
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")

    return list(cart_db.values())


@app.post("/cart/items", response_model=CartItemInDB, status_code=201)
def add_to_cart(cart_item: CartItem, authorization: Optional[str] = Header(None)):
    # TODO: сгенерируй новый id (max ключ в cart_db + 1)
    # создай CartItemInDB и добавь в cart_db по ключу
    # верни созданный объект
    # проверь авторизацию: user = get_user_from_token(authorization)
    # если нет пользователя - raise HTTPException(status_code=401, detail="Authorization required")
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")

    new_id = max(cart_db.keys(), default=0) + 1
    new_cart_item = CartItemInDB(
        id=new_id,
        item_id=cart_item.item_id,
        quantity=cart_item.quantity
    )

    cart_db[new_id] = new_cart_item
    return new_cart_item


@app.delete("/cart/items/{cart_item_id}", status_code=204)
def remove_from_cart(cart_item_id: int, authorization: Optional[str] = Header(None)):
    # TODO: проверь наличие ключа в cart_db и удали элемент
    # если ключа нет - raise HTTPException(status_code=404, detail="Cart item not found")
    # проверь авторизацию: user = get_user_from_token(authorization)
    # если нет пользователя - raise HTTPException(status_code=401, detail="Authorization required")
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")

    if cart_item_id not in cart_db:
        raise HTTPException(status_code=404, detail="Cart item not found")

    del cart_db[cart_item_id]


@app.get("/cart/total")
def get_cart_total(authorization: Optional[str] = Header(None)):
    # TODO: посчитай общую стоимость товаров в корзине
    # для каждого товара в cart_db найди цену в db
    # умножь на quantity и сложи всё вместе
    # верни {"total": ...}
    # проверь авторизацию: user = get_user_from_token(authorization)
    # если нет пользователя - raise HTTPException(status_code=401, detail="Authorization required")
    user = get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authorization required")

    total = 0

    for cart_item in cart_db.values():
        item = db[cart_item.item_id]
        total += item.price * cart_item.quantity

    return {"total": total}
