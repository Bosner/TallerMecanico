from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    vehiculos = db.relationship('Vehiculo', backref='cliente', lazy=True)

class Vehiculo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(50), nullable=False)
    modelo = db.Column(db.String(50), nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    placa = db.Column(db.String(20), unique=True, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    ordenes_trabajo = db.relationship('OrdenTrabajo', backref='vehiculo', lazy=True)

class Inventario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_parte = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)

class OrdenCompra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proveedor = db.Column(db.String(100), nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    total = db.Column(db.Float, nullable=False)
    # Lógica: Al crear, puedes agregar a inventario (ejemplo en app.py)
    

# Tabla intermedia (asociación) para many-to-many con cantidad
orden_trabajo_partes = db.Table(
    'orden_trabajo_partes',
    db.Column('orden_id', db.Integer, db.ForeignKey('orden_trabajo.id'), primary_key=True),
    db.Column('parte_id', db.Integer, db.ForeignKey('inventario.id'), primary_key=True),
    db.Column('cantidad_usada', db.Integer, nullable=False, default=1)
)

class OrdenTrabajo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehiculo_id = db.Column(db.Integer, db.ForeignKey('vehiculo.id'), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    costo_mano_obra = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(50), default='Pendiente')
    fecha_creacion = db.Column(db.Date, default=date.today)
    
    # Relación many-to-many con Inventario
    partes = db.relationship(
        'Inventario',
        secondary=orden_trabajo_partes,
        backref=db.backref('ordenes_trabajo', lazy='dynamic'),
        lazy='dynamic'
    )

    def __repr__(self):
        return f'<OrdenTrabajo {self.id} - {self.estado}>'
    


