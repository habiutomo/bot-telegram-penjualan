from werkzeug.security import generate_password_hash, check_password_hash

class Admin:
    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product:
    def __init__(self, id, name, description, price, stock, image_url=None):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.stock = stock
        self.image_url = image_url
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            description=data.get('description', ''),
            price=float(data.get('price', 0)),
            stock=int(data.get('stock', 0)),
            image_url=data.get('image_url')
        )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'image_url': self.image_url
        }

class User:
    def __init__(self, id, username, first_name, last_name=None):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            username=data.get('username', ''),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name')
        )
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name
        }

class Order:
    def __init__(self, id, user_id, items, total, address, status, created_at):
        self.id = id
        self.user_id = user_id
        self.items = items
        self.total = total
        self.address = address
        self.status = status
        self.created_at = created_at
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            items=data.get('items', {}),
            total=float(data.get('total', 0)),
            address=data.get('address', ''),
            status=data.get('status', 'pending'),
            created_at=data.get('created_at')
        )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'items': self.items,
            'total': self.total,
            'address': self.address,
            'status': self.status,
            'created_at': self.created_at
        }
