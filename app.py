from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Cliente, Vehiculo, Inventario, OrdenCompra, OrdenTrabajo, orden_trabajo_partes
from sqlalchemy import desc, func
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = 'XnB4@lK009g#3120vWxyN43'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()  # Crea tablas si no existen


CHECKLIST_ITEMS = [
    {"key": "refaccion", "label": "Refacción"},
    {"key": "herramienta", "label": "Herramienta"},
    {"key": "luces_general", "label": "Luces generales"},
    {"key": "cristales", "label": "Cristales"},
    {"key": "golpes", "label": "Golpes / Daños visibles"},
    {"key": "check_engine", "label": "Check engine / Luces advertencia"},
    {"key": "wipers", "label": "Wipers (limpiaparabrisas)"},
]

# Lista de zonas clicables (puedes agregar más)
ZONAS_VEHICULO = [
    {"key": "parachoques_delantero", "label": "Parachoques delantero"},
    {"key": "capo", "label": "Capó"},
    {"key": "puerta_delantera_izq", "label": "Puerta delantera izquierda"},
    {"key": "puerta_delantera_der", "label": "Puerta delantera derecha"},
    {"key": "puerta_trasera_izq", "label": "Puerta trasera izquierda"},
    {"key": "puerta_trasera_der", "label": "Puerta trasera derecha"},
    {"key": "parachoques_trasero", "label": "Parachoques trasero"},
    {"key": "techo", "label": "Techo"},
    # Agrega más si quieres: faros, guardabarros, etc.
]
# Página de inicio
@app.route('/')
def index():
    return render_template('index.html')

# Módulo Clientes (CRUD)
@app.route('/clientes', methods=['GET', 'POST'])
def clientes():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        
        # Campos de vehículo (nuevo)
        marca = request.form.get('marca')
        modelo = request.form.get('modelo')
        ano = request.form.get('ano')
        placa = request.form.get('placa')
        kms_actual = request.form.get('kms_actual', 0, type=int)
        
        if nombre and marca and modelo and ano and placa:  # Requerir vehículo al alta
            nuevo_cliente = Cliente(nombre=nombre, telefono=telefono, email=email)
            db.session.add(nuevo_cliente)
            db.session.commit()
            
            nuevo_vehiculo = Vehiculo(marca=marca, modelo=modelo, ano=ano, placa=placa, kms_actual=kms_actual, cliente_id=nuevo_cliente.id)
            db.session.add(nuevo_vehiculo)
            db.session.commit()
            flash('Cliente y vehículo agregados correctamente', 'success')
        else:
            flash('Faltan datos de cliente o vehículo', 'danger')
        return redirect(url_for('clientes'))

    # GET: filtros, búsqueda y paginación
    page = request.args.get('page', 1, type=int)
    busqueda = request.args.get('busqueda', '').strip()
    filtro_vehiculos = request.args.get('filtro_vehiculos', 'todos')  # todos, con_vehiculos, sin_vehiculos

    query = Cliente.query

    # Búsqueda por nombre, teléfono o email
    if busqueda:
        query = query.filter(
            db.or_(
                Cliente.nombre.ilike(f'%{busqueda}%'),
                Cliente.telefono.ilike(f'%{busqueda}%'),
                Cliente.email.ilike(f'%{busqueda}%')
            )
        )

    # Filtro por si tiene vehículos o no
    if filtro_vehiculos == 'con_vehiculos':
        query = query.join(Vehiculo, isouter=True).group_by(Cliente.id).having(db.func.count(Vehiculo.id) > 0)
    elif filtro_vehiculos == 'sin_vehiculos':
        query = query.outerjoin(Vehiculo).group_by(Cliente.id).having(db.func.count(Vehiculo.id) == 0)

    # Orden por nombre alfabético
    query = query.order_by(Cliente.nombre.asc())

    paginacion = query.paginate(page=page, per_page=20, error_out=False)
    clientes_lista = paginacion.items

    # Contadores para dashboard
    total_clientes = Cliente.query.count()
    con_vehiculos = Cliente.query.join(Vehiculo).distinct().count()
    sin_vehiculos = total_clientes - con_vehiculos

    return render_template('clientes.html',
                           clientes=clientes_lista,
                           paginacion=paginacion,
                           busqueda=busqueda,
                           filtro_vehiculos=filtro_vehiculos,
                           total_clientes=total_clientes,
                           con_vehiculos=con_vehiculos,
                           sin_vehiculos=sin_vehiculos)

# Editar cliente
@app.route('/clientes/edit/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    
    if request.method == 'POST':
        cliente.nombre = request.form.get('nombre', cliente.nombre)
        cliente.telefono = request.form.get('telefono', cliente.telefono)
        cliente.email = request.form.get('email', cliente.email)
        
        db.session.commit()
        flash('Cliente actualizado correctamente', 'success')
        return redirect(url_for('clientes'))
    
    return render_template('editar_cliente.html', cliente=cliente)

# Eliminar cliente (con confirmación básica)
@app.route('/clientes/delete/<int:id>', methods=['POST'])
def eliminar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    
    # Opcional: verificar si tiene vehículos antes de eliminar
    if cliente.vehiculos:
        flash('No se puede eliminar el cliente porque tiene vehículos asociados', 'danger')
    else:
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente eliminado correctamente', 'success')
    
    return redirect(url_for('clientes'))

# Similar para Vehículos
@app.route('/vehiculos', methods=['GET', 'POST'])
def vehiculos():
    if request.method == 'POST':
        marca = request.form.get('marca')
        modelo = request.form.get('modelo')
        ano = request.form.get('ano')
        placa = request.form.get('placa')
        cliente_id = request.form.get('cliente_id')

        if not all([marca, modelo, ano, placa, cliente_id]):
            flash('Faltan campos obligatorios', 'danger')
            return redirect(url_for('vehiculos'))

        try:
            ano = int(ano)
            cliente_id = int(cliente_id)
        except ValueError:
            flash('Año o cliente inválido', 'danger')
            return redirect(url_for('vehiculos'))

        # Verificar si la placa ya existe (para evitar duplicados)
        if Vehiculo.query.filter_by(placa=placa).first():
            flash('Esa placa ya está registrada', 'warning')
            return redirect(url_for('vehiculos'))

        nuevo_vehiculo = Vehiculo(
            marca=marca,
            modelo=modelo,
            ano=ano,
            placa=placa.upper(),  # buena práctica: placas en mayúsculas
            cliente_id=cliente_id
        )

        db.session.add(nuevo_vehiculo)
        db.session.commit()           # ← ESTO ES CRUCIAL
        flash('Vehículo registrado correctamente', 'success')

        return redirect(url_for('vehiculos'))

    # GET
    page = request.args.get('page', 1, type=int)
    busqueda = request.args.get('busqueda', '').strip()
    filtro_cliente = request.args.get('cliente_id', 'todos')

    query = Vehiculo.query

    # Búsqueda por placa, marca, modelo
    if busqueda:
        query = query.filter(
            db.or_(
                Vehiculo.placa.ilike(f'%{busqueda}%'),
                Vehiculo.marca.ilike(f'%{busqueda}%'),
                Vehiculo.modelo.ilike(f'%{busqueda}%')
            )
        )

    # Filtro por cliente específico
    if filtro_cliente != 'todos':
        try:
            cliente_id = int(filtro_cliente)
            query = query.filter(Vehiculo.cliente_id == cliente_id)
        except ValueError:
            pass

    # Orden por placa o marca
    query = query.order_by(Vehiculo.placa.asc())

    paginacion = query.paginate(page=page, per_page=20, error_out=False)
    vehiculos_lista = paginacion.items

    clientes = Cliente.query.order_by(Cliente.nombre.asc()).all()

    # Contadores
    total_vehiculos = Vehiculo.query.count()
    # Puedes agregar más si quieres (por marca, año, etc.)

    return render_template('vehiculos.html',
                           vehiculos=vehiculos_lista,
                           paginacion=paginacion,
                           busqueda=busqueda,
                           clientes=clientes,
                           filtro_cliente=filtro_cliente,
                           total_vehiculos=total_vehiculos)

# Inventarios
@app.route('/inventarios', methods=['GET', 'POST'])
def inventarios():
    if request.method == 'POST':
        nombre_parte = request.form.get('nombre_parte')
        cantidad = int(request.form.get('cantidad') or 0)
        precio = float(request.form.get('precio') or 0.0)
        
        if nombre_parte and cantidad >= 0 and precio >= 0:
            nuevo_item = Inventario(
                nombre_parte=nombre_parte,
                cantidad=cantidad,
                precio=precio
            )
            db.session.add(nuevo_item)
            db.session.commit()
            flash('Pieza agregada al inventario', 'success')
        else:
            flash('Datos inválidos. Verifica nombre, cantidad y precio.', 'danger')
        
        return redirect(url_for('inventarios'))

    # GET: filtros, búsqueda y paginación
    page = request.args.get('page', 1, type=int)
    busqueda = request.args.get('busqueda', '').strip()
    filtro_stock = request.args.get('filtro_stock', 'todos')  # todos, bajo, critico, con_stock

    query = Inventario.query

    # Búsqueda por nombre
    if busqueda:
        query = query.filter(Inventario.nombre_parte.ilike(f'%{busqueda}%'))

    # Filtros de stock
    if filtro_stock == 'bajo':
        query = query.filter(Inventario.cantidad <= 20, Inventario.cantidad > 0)
    elif filtro_stock == 'critico':
        query = query.filter(Inventario.cantidad <= 5)
    elif filtro_stock == 'con_stock':
        query = query.filter(Inventario.cantidad > 0)
    # 'todos' → sin filtro

    # Orden por cantidad ascendente (lo que se acaba primero arriba)
    query = query.order_by(Inventario.cantidad.asc())

    paginacion = query.paginate(page=page, per_page=25, error_out=False)
    items = paginacion.items

    # Cálculos para dashboard
    total_piezas = Inventario.query.count()
    total_valor_stock = db.session.query(db.func.sum(Inventario.cantidad * Inventario.precio)).scalar() or 0
    bajo_stock = Inventario.query.filter(Inventario.cantidad <= 20, Inventario.cantidad > 0).count()
    critico_stock = Inventario.query.filter(Inventario.cantidad <= 5).count()

    return render_template('inventarios.html',
                           items=items,
                           paginacion=paginacion,
                           busqueda=busqueda,
                           filtro_stock=filtro_stock,
                           total_piezas=total_piezas,
                           total_valor_stock=total_valor_stock,
                           bajo_stock=bajo_stock,
                           critico_stock=critico_stock)

# Órdenes de Compra
@app.route('/ordenes_compra', methods=['GET', 'POST'])
def ordenes_compra():
    if request.method == 'POST':
        proveedor = request.form['proveedor']
        total = float(request.form['total'])
        parte_id = request.form.get('parte_id')
        cantidad_comprada = request.form.get('cantidad_comprada')
        
        nueva_orden = OrdenCompra(proveedor=proveedor, total=total)
        db.session.add(nueva_orden)
        db.session.commit()
        
        # Lógica operativa: Si se especifica parte, agregar a inventario
        if parte_id and cantidad_comprada:
            try:
                cantidad_comprada = int(cantidad_comprada)
                item = Inventario.query.get(int(parte_id))
                if item:
                    item.cantidad += cantidad_comprada
                    db.session.commit()
                    flash(f'Se agregaron {cantidad_comprada} unidades a {item.nombre_parte}.', 'success')
                else:
                    flash('Parte no encontrada.', 'error')
            except ValueError:
                flash('Cantidad inválida.', 'error')
        
        return redirect(url_for('ordenes_compra'))
    
    ordenes = OrdenCompra.query.all()
    items = Inventario.query.all()  # Para select en template
    return render_template('ordenes_compra.html', ordenes=ordenes, items=items)


from datetime import date, datetime
from flask import flash, redirect, render_template, request, url_for
from sqlalchemy import desc

# ... otras importaciones que ya tengas ...

@app.route('/ordenes_servicio', methods=['GET', 'POST'])
def ordenes_servicio():
    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id')
        vehiculo_id = request.form.get('vehiculo_id')
        falla_reportada = request.form.get('falla_reportada')
        checklist_items = request.form.getlist('checklist[]')          # checkboxes
        fecha_compromiso_str = request.form.get('fecha_compromiso')

        if not all([cliente_id, vehiculo_id, falla_reportada]):
            flash('Faltan campos obligatorios: cliente, vehículo o falla reportada', 'danger')
            return redirect(url_for('ordenes_servicio'))

        # Validar que el vehículo pertenece al cliente
        vehiculo = Vehiculo.query.get(vehiculo_id)
        if not vehiculo or str(vehiculo.cliente_id) != cliente_id:
            flash('El vehículo seleccionado no pertenece al cliente indicado', 'danger')
            return redirect(url_for('ordenes_servicio'))

        # Crear la orden
        nueva_orden = OrdenTrabajo(
            vehiculo_id=vehiculo_id,
            falla_reportada=falla_reportada.strip(),
            estado='Pendiente',
            fecha_creacion=datetime.utcnow(),
        )

        # Folio automático
        ultima_orden = OrdenTrabajo.query.order_by(desc(OrdenTrabajo.id)).first()
        siguiente_num = (ultima_orden.id + 1) if ultima_orden else 1
        nueva_orden.folio = f"F-{siguiente_num:04d}"   # Ej: F-0001, F-0002...

        # Fecha compromiso (opcional)
        if fecha_compromiso_str:
            try:
                nueva_orden.fecha_compromiso = datetime.strptime(fecha_compromiso_str, '%Y-%m-%d').date()
            except:
                flash('Formato de fecha compromiso inválido', 'warning')

        # Checklist
        checklist_data = {}
        for item in CHECKLIST_ITEMS:
            key = item['key']
            si = request.form.get(f'checklist_si_{key}') == 'on'
            obs = request.form.get(f'obs_{key}', '').strip()
            checklist_data[key] = {"si": si, "obs": obs}

        # Daños / golpes
        danios_data = {}
        for zona in ZONAS_VEHICULO:
            key = zona['key']
            marcado = request.form.get(f'danio_marcado_{key}') == 'on'
            descripcion = request.form.get(f'danio_desc_{key}', '').strip()
            if marcado or descripcion:
                danios_data[key] = {"marcado": marcado, "descripcion": descripcion}

        nueva_orden.checklist_revision = checklist_data
        nueva_orden.danios_zonas = danios_data

        db.session.add(nueva_orden)
        db.session.commit()

        flash(f'Orden de servicio creada correctamente → Folio: {nueva_orden.folio}', 'success')
        return redirect(url_for('ordenes_servicio'))

    # ────────────────────────────────────────────────
    #                  GET - Listado + filtros
    # ────────────────────────────────────────────────
    page = request.args.get('page', 1, type=int)
    estado_filtro = request.args.get('estado', 'todas')
    busqueda = request.args.get('busqueda', '').strip()

    query = OrdenTrabajo.query

    if estado_filtro != 'todas':
        query = query.filter(OrdenTrabajo.estado == estado_filtro)

    if busqueda:
        query = query.join(Vehiculo).join(Cliente).filter(
            db.or_(
                Vehiculo.placa.ilike(f'%{busqueda}%'),
                Cliente.nombre.ilike(f'%{busqueda}%'),
                OrdenTrabajo.folio.ilike(f'%{busqueda}%')
            )
        )

    query = query.order_by(desc(OrdenTrabajo.fecha_creacion))

    paginacion = query.paginate(page=page, per_page=15, error_out=False)
    ordenes = paginacion.items

    # Contadores para dashboard
    hoy = date.today()
    total_pendientes         = OrdenTrabajo.query.filter_by(estado='Pendiente').count()
    total_progreso           = OrdenTrabajo.query.filter_by(estado='En progreso').count()
    total_completadas_hoy    = OrdenTrabajo.query.filter(
        OrdenTrabajo.estado == 'Completado',
        OrdenTrabajo.fecha_entrega == hoy
    ).count()
    total_abiertas           = OrdenTrabajo.query.filter(
        OrdenTrabajo.estado.in_(['Pendiente', 'En progreso'])
    ).count()

    clientes = Cliente.query.order_by(Cliente.nombre).all()

    return render_template(
        'ordenes_servicio.html',
        ordenes=ordenes,
        clientes=clientes,
        paginacion=paginacion,
        estado_filtro=estado_filtro,
        busqueda=busqueda,
        total_pendientes=total_pendientes,
        total_progreso=total_progreso,
        total_completadas_hoy=total_completadas_hoy,
        total_abiertas=total_abiertas,
        checklist_items=CHECKLIST_ITEMS,
        zonas_vehiculo=ZONAS_VEHICULO
    )

@app.route('/ordenes_servicio/<int:orden_id>')
def detalle_orden(orden_id):
    """
    Muestra el detalle de una orden de servicio.
    - Sin costos (eliminados por requerimiento del cliente)
    - Permite ver/agregar refacciones solo si está en 'En progreso'
    - Muestra trabajo realizado, checklist, etc.
    """
    orden = OrdenTrabajo.query.get_or_404(orden_id)

    # 1. Partes usadas (sin calcular precios)
    partes_usadas = orden.partes

    # 2. Calcular solo la cantidad total de piezas usadas (opcional, para mostrar un resumen simple)
    total_piezas_usadas = db.session.query(
        func.sum(orden_trabajo_partes.c.cantidad_usada)
    ).filter_by(orden_id=orden.id).scalar() or 0

    # 3. Partes disponibles en inventario para el selector de agregar
    partes_disponibles = Inventario.query.filter(Inventario.cantidad > 0).all()

    # 4. (Opcional) Si quieres pasar un diccionario con cantidades por parte
    cantidades_usadas = {}
    if partes_usadas:
        result = db.session.query(
            orden_trabajo_partes.c.parte_id,
            orden_trabajo_partes.c.cantidad_usada
        ).filter_by(orden_id=orden.id).all()
        
        cantidades_usadas = {r.parte_id: r.cantidad_usada for r in result}

    return render_template(
        'detalle_orden.html',
        orden=orden,
        partes_usadas=partes_usadas,
        cantidades_usadas=cantidades_usadas,       # para usar en el template
        partes_disponibles=partes_disponibles,
        total_piezas_usadas=total_piezas_usadas
    )

def get_dashboard_counts():
    from models import OrdenTrabajo, Inventario
    
    pendientes = OrdenTrabajo.query.filter_by(estado='Pendiente').count()
    en_progreso = OrdenTrabajo.query.filter_by(estado='En progreso').count()
    critico_stock = Inventario.query.filter(Inventario.cantidad <= 5).count()
    
    return {
        'pendientes': pendientes,
        'en_progreso': en_progreso,
        'critico_stock': critico_stock
    }

@app.context_processor
def inject_dashboard_counts():
    return dict(dashboard_counts=get_dashboard_counts())


@app.route('/ordenes_servicio/update_estado/<int:orden_id>', methods=['POST'])
def update_estado_orden(orden_id):
    """
    Actualiza el estado de una orden de trabajo específica.
    Se llama desde la página de detalle o desde la lista (si agregamos dropdown allí).
    """
    orden = OrdenTrabajo.query.get_or_404(orden_id)
    
    nuevo_estado = request.form.get('estado')
    
    # Validar que el estado sea uno de los permitidos
    estados_validos = ['Pendiente', 'En progreso', 'Completado', 'Cancelado']
    if nuevo_estado not in estados_validos:
        flash(f'Estado inválido. Debe ser uno de: {", ".join(estados_validos)}', 'danger')
        return redirect(request.referrer or url_for('ordenes_servicio'))
    
    # Actualizar el estado
    orden.estado = nuevo_estado
    
    # Opcional: si se completa, podrías agregar lógica extra aquí
    if nuevo_estado == 'Completado':
        # Ejemplo: podrías guardar fecha de finalización si agregas el campo
        # orden.fecha_fin = date.today()
        flash('¡Orden marcada como completada!', 'success')
    elif nuevo_estado == 'Cancelado':
        flash('Orden cancelada correctamente.', 'warning')
    else:
        flash(f'Estado actualizado a: {nuevo_estado}', 'info')
    
    db.session.commit()
    
    # Regresar a donde vino el usuario (página de detalle o lista)
    return redirect(request.referrer or url_for('ordenes_servicio'))


@app.route('/vehiculos_por_cliente/<int:cliente_id>')
def vehiculos_por_cliente(cliente_id):
    """API para cargar vehículos de un cliente específico (usado por JS)"""
    vehiculos = Vehiculo.query.filter_by(cliente_id=cliente_id).all()
    return jsonify([{
        'id': v.id,
        'marca': v.marca,
        'modelo': v.modelo,
        'placa': v.placa,
        'texto': f"{v.marca} {v.modelo} — Placa: {v.placa}"
    } for v in vehiculos])


@app.route('/ordenes_servicio/agregar_refaccion/<int:orden_id>', methods=['POST'])
def agregar_refaccion_orden(orden_id):
    orden = OrdenTrabajo.query.get_or_404(orden_id)
    if orden.estado != 'En progreso':
        flash('Solo se pueden agregar refacciones en progreso', 'danger')
        return redirect(url_for('detalle_orden', orden_id=orden_id))
    
    parte_id = request.form.get('parte_id', type=int)
    cantidad = request.form.get('cantidad_usada', type=int)
    
    parte = Inventario.query.get_or_404(parte_id)
    if parte.cantidad < cantidad:
        flash('Stock insuficiente', 'danger')
        return redirect(url_for('detalle_orden', orden_id=orden_id))
    
    # Agregar a relación
    db.session.execute(orden_trabajo_partes.insert().values(orden_id=orden_id, parte_id=parte_id, cantidad_usada=cantidad))
    parte.cantidad -= cantidad  # Actualizar stock
    db.session.commit()
    flash('Refacción agregada', 'success')
    return redirect(url_for('detalle_orden', orden_id=orden_id))

@app.route('/ordenes_servicio/update_trabajo/<int:orden_id>', methods=['POST'])
def update_trabajo_realizado(orden_id):
    orden = OrdenTrabajo.query.get_or_404(orden_id)
    orden.trabajo_realizado = request.form.get('trabajo_realizado')
    db.session.commit()
    flash('Trabajo realizado actualizado', 'info')
    return redirect(url_for('detalle_orden', orden_id=orden_id))

    

if __name__ == '__main__':
    app.run(debug=True)