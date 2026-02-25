from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime

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
    kms_actual = db.Column(db.Integer)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    ordenes_trabajo = db.relationship('OrdenTrabajo', backref='vehiculo', lazy=True)

class Inventario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_parte = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    numero_parte = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float, nullable=False)
    # Tabla intermedia para refacciones con cantidad
    orden_trabajo_partes = db.Table(
        'orden_trabajo_partes',
        db.Column('orden_id', db.Integer, db.ForeignKey('orden_trabajo.id'), primary_key=True),
        db.Column('parte_id', db.Integer, db.ForeignKey('inventario.id'), primary_key=True),
        db.Column('cantidad_usada', db.Integer, nullable=False, default=1)
    )

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
    db.Column('cantidad_usada', db.Integer, nullable=False, default=1),
    extend_existing=True
)

class OrdenTrabajo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    folio = db.Column(db.String(20), unique=True)  # Nuevo: Folio secuencial como en Excels (ej: 'FOLIO-001')
    vehiculo_id = db.Column(db.Integer, db.ForeignKey('vehiculo.id'), nullable=False)
    falla_reportada = db.Column(db.Text, nullable=False)  # Nuevo: Falla que reporta el cliente (de Excels)
    checklist_revision = db.Column(db.Text)  # Nuevo: Checklist visual (JSON o texto serializado, ej: "Luces: OK, Frenos: Mal")
    trabajo_realizado = db.Column(db.Text)  # Nuevo: Servicio realizado (de Excels)
    estado = db.Column(db.String(50), default='Pendiente')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_compromiso = db.Column(db.Date)  # Nuevo: Fecha compromiso entrega (de Excels)
    fecha_entrega = db.Column(db.Date)
    
    # Relación many-to-many con Inventario
    partes = db.relationship(
        'Inventario',
        secondary=orden_trabajo_partes,
        backref=db.backref('ordenes_trabajo', lazy='dynamic'),
        lazy='select'
    )
    
    def generar_folio(self):
        ultimo = OrdenTrabajo.query.order_by(desc(OrdenTrabajo.id)).first()
        num = (ultimo.id + 1) if ultimo else 1
        self.folio = f"FOLIO-{num:03d}"
    
    def get_partes_con_cantidad(self):
        return db.session.query(
            Inventario,
            orden_trabajo_partes.c.cantidad_usada
        ).join(
            orden_trabajo_partes,
            Inventario.id == orden_trabajo_partes.c.parte_id
        ).filter(
            orden_trabajo_partes.c.orden_id == self.id
        ).all()

    def __repr__(self):
        return f'<OrdenTrabajo {self.id} - {self.estado}>'
    


