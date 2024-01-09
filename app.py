from flask import Flask, render_template, request, redirect,url_for
from flask_caching import Cache

import json
from collections import defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import data
import base64
import io
import numpy as np
import matplotlib
matplotlib.use('Agg')


app = Flask(__name__)
app.config['SECRET_KEY'] = 'AOHDNBIAAI189SD!A1'

# Configuración de la caché
cache = Cache(app, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 86400})


with open('config.json', 'r') as config_file:
    constants = json.load(config_file)

# Constantes
SP = constants['SP']

sales_persons = {
    "4c260962-bd4b-47d9-a300-5f3ceb378a6e": "MORGAN WEST",
    "a723c745-89f6-4b1f-b5f7-2a0a2f90b347": "MARK",
    "e8bbf3ee-ace8-46d1-bd8b-77bd9299c24f": "ALISON",
    "8a1687d6-9a78-4016-9de2-d82ff13a11ed": "EDUARDO",
    "04ea9165-0af4-4831-b589-754193ef73f3": "JAY",
    "f3293da0-45e8-469a-ac20-3e72a59de1c0": "DYLAN",
    "9ab5e80c-3bb6-4c4b-af75-5c568ac4953a": "JONAS",
    "20bf548a-e262-4313-9c19-c547d83f7fb3": "MORGAN",
    "a61f6179-b49e-4d07-a5ca-59a482b1e8cb": "MILAGROS"
}


# Controller
@cache.cached()
def get_data():
    return data.read(SP)

def get_sales_meetings_data(start_year=None, start_month=None, end_year=None, end_month=None):
    entries = get_data()
    result_dict = defaultdict(dict)

    for entry in entries:
        assigned_to = entry['properties']['Assigned to']['people']
        tags = entry['properties']['Tags']['multi_select']
        date_start_full = entry['properties']['Day/Hour']['date']['start'] if entry['properties']['Day/Hour']['date'] else None

        if assigned_to and tags and date_start_full:
            assigned_to_id = assigned_to[0]['id']
            tag_info = tags[0]

            if tag_info['name'] in ['QUALIFIED', 'NOT QUALIFIED', 'CANCELLED', 'PLANNING', 'CLOSING', 'TURN', 'RESCHEDULE']:
                assigned_to_name = sales_persons.get(assigned_to_id, "unknown")

                # Parse the input date string
                try:
                    date_object = datetime.fromisoformat(date_start_full.split("T")[0])

                    # Check if the date is within the specified range
                    if start_year and start_month and end_year and end_month:
                        if not (start_year <= date_object.year <= end_year and start_month <= date_object.month <= end_month):
                            continue

                    result_dict[assigned_to_name][date_start_full] = tag_info['name']

                except ValueError:
                    # Handle different date formats if parsing fails
                    continue

    return dict(result_dict)

def count_tags_by_month(start_year=None, start_month=None, end_year=None, end_month=None):
    input_dict = get_sales_meetings_data(start_year, start_month, end_year, end_month)
    output_dict = {}

    for key, inner_dict in input_dict.items():
        counts = {"QUALIFIED": {}, "NOT QUALIFIED": {}, "CANCELLED": {}, "PLANNING": {}, "CLOSING": {}, "TURN": {}, "RESCHEDULE" : {}}

        for date_str, value in inner_dict.items():
            # Parse the input date string
            date_object = datetime.fromisoformat(date_str.split(".")[0])

            # Format the date as "aaaa-mm"
            formatted_date = date_object.strftime("%Y-%m")

            # Update the count for the corresponding qualification and month
            if value not in counts:
                counts[value] = {}

            counts[value][formatted_date] = counts[value].get(formatted_date, 0) + 1

        # Update the outer dictionary with the count dictionary
        output_dict[key] = counts

    return output_dict

def calculate_stats(start_year=None, start_month=None, end_year=None, end_month=None):
    result_dict = {}

    counts_by_month = count_tags_by_month(start_year, start_month, end_year, end_month)
    
    for key, counts in counts_by_month.items():
        qualifies = sum(counts.get('QUALIFIED', {}).values())
        not_qualifies = sum(counts.get('NOT QUALIFIED', {}).values())
        cancelled = sum(counts.get('CANCELLED', {}).values())
        planning = sum(counts.get('PLANNING', {}).values())
        closing = sum(counts.get('CLOSING', {}).values())
        turn = sum(counts.get('TURN', {}).values())
        reschedule = sum(counts.get('RESCHEDULE', {}).values())

        total_qualifies = qualifies + planning + turn + closing
        total_not_qualifies = not_qualifies + cancelled
        visited = total_qualifies + total_not_qualifies

        # Encontrar el mes con la máxima cantidad de 'QUALIFIED'
        month_goal = max(counts.get('QUALIFIED', {}), key=counts.get('QUALIFIED', {}).get, default=None)
        month_goal_qualifies_amount = counts.get('QUALIFIED', {}).get(month_goal, 0)

        # Calcular las tasas de conversión
        conversion_rate = total_qualifies / (total_qualifies + total_not_qualifies) if total_qualifies + total_not_qualifies > 0 else 0
        not_qualifies_rate = 1 - conversion_rate

        cancelled_rate = cancelled / total_not_qualifies if not_qualifies > 0 else 0

        total_cancelled = cancelled + reschedule


        result_dict[key] = {
            'total_qualifies': total_qualifies,
            'total_not_qualifies': total_not_qualifies,
            'total_cancelled': total_cancelled,
            'month_goal': month_goal,
            'month_goal_qualifies_amount': month_goal_qualifies_amount,
            'conversion_rate': conversion_rate,
            'not_qualifies_rate': not_qualifies_rate,
            'cancelled_rate':cancelled_rate,
            'visited': visited
        }

    return result_dict

def count_tags_last_30_days():
    input_dict = get_sales_meetings_data()
    output_dict = {}

    # Obtén la fecha actual
    current_date = datetime.now()

    for key, inner_dict in input_dict.items():
        counts = {"QUALIFIED": {}, "NOT QUALIFIED": {}, "CANCELLED": {}, "PLANNING": {}, "CLOSING": {}, "TURN": {}, "RESCHEDULE" : {}}

        for date_str, value in inner_dict.items():
            # Parsea la fecha de entrada
            date_object = datetime.fromisoformat(date_str.split(".")[0])

            # Calcula la diferencia de días entre la fecha actual y la fecha de la reunión
            days_difference = (current_date - date_object).days

            # Si la reunión ocurrió en los últimos 30 días, procesa la información
            if 0 <= days_difference <= 30:
                # Formatea la fecha como "aaaa-mm"
                formatted_date = date_object.strftime("%Y-%m")

                # Actualiza el recuento para la calificación y el mes correspondientes
                if value not in counts:
                    counts[value] = {}

                counts[value][formatted_date] = counts[value].get(formatted_date, 0) + 1

        # Actualiza el diccionario externo con el diccionario de recuento
        output_dict[key] = counts

    return output_dict

def calculate_stats_last_30_days():
    result_dict = {}

    #counts_by_month = count_tags_last_30_days()

    counts_by_month = {'MARK': {'QUALIFIED': {'2024-01': 6, '2023-12': 18}, 'NOT QUALIFIED': {'2024-01': 1, '2023-12': 2}, 'CANCELLED': {'2023-12': 1}, 'PLANNING': {'2024-01': 2, '2023-12': 10}, 'CLOSING': {'2023-12': 3}, 'TURN': {'2023-12': 1}, 'RESCHEDULE': {'2023-12': 1}}, 'MORGAN WEST': {'QUALIFIED': {'2023-12': 7, '2024-01': 1}, 'NOT QUALIFIED': {'2024-01': 1, '2023-12': 6}, 'CANCELLED': {}, 'PLANNING': {}, 'CLOSING': {}, 'TURN': {}, 'RESCHEDULE': {}}, 'EDUARDO': {'QUALIFIED': {'2023-12': 3}, 'NOT QUALIFIED': {'2023-12': 7}, 'CANCELLED': {'2023-12': 2}, 'PLANNING': {}, 'CLOSING': {}, 'TURN': {}, 'RESCHEDULE': {'2023-12': 1}}, 'MORGAN': {'QUALIFIED': {}, 'NOT QUALIFIED': {}, 'CANCELLED': {}, 'PLANNING': {}, 'CLOSING': {}, 'TURN': {}, 'RESCHEDULE': {}}, 'JONAS': {'QUALIFIED': {}, 'NOT QUALIFIED': {}, 'CANCELLED': {}, 'PLANNING': {}, 'CLOSING': {}, 'TURN': {}, 'RESCHEDULE': {}}, 'ALISON': {'QUALIFIED': {'2023-12': 6}, 'NOT QUALIFIED': {'2023-12': 3}, 'CANCELLED': {'2023-12': 1}, 'PLANNING': {'2023-12': 1}, 'CLOSING': {'2023-12': 1}, 'TURN': {}, 'RESCHEDULE': {}}, 'DYLAN': {'QUALIFIED': {}, 'NOT QUALIFIED': {}, 'CANCELLED': {}, 'PLANNING': {}, 'CLOSING': {}, 'TURN': {}, 'RESCHEDULE': {}}, 'JAY': {'QUALIFIED': {}, 'NOT QUALIFIED': {}, 'CANCELLED': {}, 'PLANNING': {}, 'CLOSING': {}, 'TURN': {}, 'RESCHEDULE': {}}, 'unknown': {'QUALIFIED': {'2023-12': 1}, 'NOT QUALIFIED': {}, 'CANCELLED': {}, 'PLANNING': {}, 'CLOSING': {}, 'TURN': {}, 'RESCHEDULE': {}}, 'MILAGROS': {'QUALIFIED': {}, 'NOT QUALIFIED': {}, 'CANCELLED': {}, 'PLANNING': {}, 'CLOSING': {}, 'TURN': {}, 'RESCHEDULE': {}}}

    for key, counts in counts_by_month.items():
        qualifies = sum(counts.get('QUALIFIED', {}).values())
        not_qualifies = sum(counts.get('NOT QUALIFIED', {}).values())
        cancelled = sum(counts.get('CANCELLED', {}).values())
        planning = sum(counts.get('PLANNING', {}).values())
        closing = sum(counts.get('CLOSING', {}).values())
        turn = sum(counts.get('TURN', {}).values())
        reschedule = sum(counts.get('RESCHEDULE', {}).values())

        total_qualifies = qualifies + planning + turn + closing
        total_not_qualifies = not_qualifies + cancelled
        visited = total_qualifies + total_not_qualifies

        # Encontrar el mes con la máxima cantidad de 'QUALIFIED'
        month_goal = max(counts.get('QUALIFIED', {}), key=counts.get('QUALIFIED', {}).get, default=None)
        month_goal_qualifies_amount = counts.get('QUALIFIED', {}).get(month_goal, 0)

        # Calcular las tasas de conversión
        conversion_rate = total_qualifies / (total_qualifies + total_not_qualifies) if total_qualifies + total_not_qualifies > 0 else 0
        not_qualifies_rate = 1 - conversion_rate

        cancelled_rate = cancelled / total_not_qualifies if not_qualifies > 0 else 0

        total_cancelled = cancelled + reschedule


        result_dict[key] = {
            'total_qualifies': total_qualifies,
            'total_not_qualifies': total_not_qualifies,
            'total_cancelled': total_cancelled,
            'month_goal': month_goal,
            'month_goal_qualifies_amount': month_goal_qualifies_amount,
            'conversion_rate': conversion_rate,
            'not_qualifies_rate': not_qualifies_rate,
            'cancelled_rate':cancelled_rate,
            'visited': visited
        }

    return result_dict

def aggregate_qualified_by_month():
    sales_data = get_sales_meetings_data()
    result_dict = defaultdict(int)

    for person, person_data in sales_data.items():
        for date, status in person_data.items():
            if status in ['QUALIFIED', 'PLANNING', 'TURN', 'CLOSING']:
                # Extract the year and month from the date
                year_month = date[:7]
                result_dict[year_month] += 1

    sorted_result = dict(sorted(result_dict.items()))  # Ordenar el diccionario por las claves

    return sorted_result

def aggregate_not_qualified_by_month():
    sales_data = get_sales_meetings_data()
    result_dict = defaultdict(int)

    for person, person_data in sales_data.items():
        for date, status in person_data.items():
            if status in ['NOT QUALIFIED', 'CANCELLED']:
                year_month = date[:7]
                result_dict[year_month] += 1

    sorted_result = dict(sorted(result_dict.items()))

    return sorted_result

def get_leads_and_customers_count():
    entries = get_data()
    result_dict = defaultdict(lambda: {'total_leads': 0, 'total_customers': 0})

    for entry in entries:
        assigned_to = entry['properties']['Assigned to']['people']
        tags = entry['properties']['Tags']['multi_select']
        contact_type = entry['properties']['Formula']['formula']['string'] if entry['properties']['Formula']['formula'] else None

        if assigned_to and tags and contact_type:
            assigned_to_id = assigned_to[0]['id']

            assigned_to_name = sales_persons.get(assigned_to_id, "unknown")

            if contact_type == 'LEAD':
                result_dict[assigned_to_name]['total_leads'] += 1
            elif contact_type == 'CUSTOMER':
                result_dict[assigned_to_name]['total_customers'] += 1

    return dict(result_dict)


# Routes
@app.route('/')
def get_stats():
    start_year = request.args.get('start_year', None)
    start_month = request.args.get('start_month', None)
    end_year = request.args.get('end_year', None)
    end_month = request.args.get('end_month', None)

    # Convertir a int o manejar None según sea necesario
    start_year = int(start_year) if start_year else None
    start_month = int(start_month) if start_month else None
    end_year = int(end_year) if end_year else None
    end_month = int(end_month) if end_month else None

    stats_data = calculate_stats(start_year=start_year, start_month=start_month, end_year=end_year, end_month=end_month)

    stats_data_last_30_days = calculate_stats_last_30_days()
    qualified_by_month = aggregate_qualified_by_month()
    not_qualified_by_month = aggregate_not_qualified_by_month()
    leads_and_customers_data  = get_leads_and_customers_count()

    light_blue = '#5A95DB'
    dark_blue = '#142F50'

    # ---------------- gráfico de barras ----------------
    plt.figure(figsize=(12, 6))
    months = list(qualified_by_month.keys())
    x_positions = range(len(months))
    bar_width = 0.4  # Ancho de cada barra

    # Crear barras para Qualified y Not Qualified por mes
    plt.bar(x_positions, list(qualified_by_month.values()), width=bar_width, color=light_blue, label='Qualified')
    plt.bar([x + bar_width for x in x_positions], list(not_qualified_by_month.values()), width=bar_width, color=dark_blue, label='Not Qualified')

    # Etiquetas en la punta de cada barra
    for x, (qualified, not_qualified) in enumerate(zip(qualified_by_month.values(), not_qualified_by_month.values())):
        plt.text(x, qualified, str(qualified), ha='center', va='bottom', fontsize=16)
        plt.text(x + bar_width, not_qualified, str(not_qualified), ha='center', va='bottom', fontsize=16)

    plt.title('Total Meetings', fontsize=16)
    plt.xticks([x + bar_width / 2 for x in x_positions], months, fontsize=15)
    plt.legend()

    plt.box(False)

    # Guardar la imagen en BytesIO
    img_bytesio = BytesIO()
    plt.savefig(img_bytesio, format='png')
    img_bytesio.seek(0)

    # Convertir BytesIO a base64 para incrustar en la plantilla HTML
    img_base64_total_qualifies = f"data:image/png;base64,{base64.b64encode(img_bytesio.getvalue()).decode()}"

    # ----------------gráfico circular----------------
    labels = ['Qualified', 'Not Qualified']
    values = [
        sum(stats['total_qualifies'] for stats in stats_data_last_30_days.values()),
        sum(stats['total_not_qualifies'] for stats in stats_data_last_30_days.values())
    ]

    # Append data and assign color
    labels.append("")
    values.append(sum(values))  # 50% blank
    colors = [light_blue, dark_blue, 'white']

    # Plot
    fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
    wedges, _ = ax.pie(values, colors=colors, wedgeprops=dict(width=0.4))

    # Decoraciones adicionales
    plt.title('Last 30 Days', fontsize=16)

    # Agregar círculo blanco
    ax.add_artist(plt.Circle((0, 0), 0.6, color='white'))

    # Ajustar el diseño para que se vea más limpio
    ax.axis('equal')

    # Añadir cantidad debajo de los labels
    ax.text(0.8, -0.2, f'{values[0]} Qualifies', ha='center', va='center', color='black', fontsize=16)
    ax.text(-0.8, -0.2, f'{values[1]} Not Qualifies', ha='center', va='center', color='black', fontsize=16)

    # Quitar la caja de estadísticas
    ax.legend().set_visible(False)

    # Convertir el diagrama a BytesIO y luego a Base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    img_base64_last_30_days = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"


    # ---------------- gráfico de barras ----------------
    plt.figure(figsize=(12, 6))
    width = 0.35  # Ancho de las barras
    salespersons = list(stats_data.keys())
    x_positions = range(len(salespersons))

    # Crear barras para Qualified
    qualified_values = [stats['total_qualifies'] for stats in stats_data.values()]
    plt.bar(x_positions, qualified_values, width, label='Qualified', color=light_blue)

    # Crear barras para Not Qualified al lado de las barras de Qualified
    not_qualified_values = [stats['total_not_qualifies'] for stats in stats_data.values()]
    plt.bar([x + width for x in x_positions], not_qualified_values, width, label='Not Qualified', color=dark_blue)

    # Etiquetas en la punta de cada barra
    for x, (qualified, not_qualified) in zip(x_positions, zip(qualified_values, not_qualified_values)):
        plt.text(x, qualified, str(qualified), ha='center', va='bottom')
        plt.text(x + width, not_qualified, str(not_qualified), ha='center', va='bottom')

    plt.xlabel('Salespersons')
    plt.ylabel('Count')
    plt.title('Qualified and Not Qualified Counts for Salespersons')
    plt.xticks([x + width / 2 for x in x_positions], salespersons)  # Posicionar etiquetas en el centro de cada par de barras
    plt.legend()
    plt.box(False)

    # Guardar la imagen en BytesIO
    img_bytesio = BytesIO()
    plt.savefig(img_bytesio, format='png')
    img_bytesio.seek(0)

    # Convertir BytesIO a base64 para incrustar en la plantilla HTML
    img_base64 = f"data:image/png;base64,{base64.b64encode(img_bytesio.getvalue()).decode()}"


    # Crear resumen de cada salesperson
    summary_data = {}
    leads_and_customers_data = get_leads_and_customers_count()

    for salesperson, stats in stats_data.items():
        month_goal = stats['month_goal']
        month_goal_qualifies_amount = stats['month_goal_qualifies_amount']
        total_qualifies = stats['total_qualifies']
        total_not_qualifies = stats['total_not_qualifies']
        total_cancelled = stats['total_cancelled']
        visited = stats['visited']
        conversion_rate = stats['conversion_rate']
        not_qualifies_rate = stats['not_qualifies_rate']
        cancelled_rate = stats['cancelled_rate']

        # Obtener las estadísticas de LEADs y CUSTOMERs del diccionario leads_and_customers_data
        leads_customers_stats = leads_and_customers_data.get(salesperson, {'total_leads': 0, 'total_customers': 0})

        summary_data[salesperson] = {
            'Month Goal': month_goal,
            'Month Goal Qualifies Amount': month_goal_qualifies_amount,
            'Total Qualifies': total_qualifies,
            'Total Not Qualifies': total_not_qualifies,
            'Total Cancelled': total_cancelled,
            'visited': visited,
            'Conversion Rate': f"{conversion_rate:.2%}",
            'Not Qualifies Rate': f"{not_qualifies_rate:.2%}",
            'Cancelled Rate': f"{cancelled_rate:.2%}",
            'Total Leads': leads_customers_stats['total_leads'],
            'Total Customers': leads_customers_stats['total_customers']
        }

    return render_template('index.html', img_base64_total_qualifies=img_base64_total_qualifies, img_base64_last_30_days = img_base64_last_30_days, img_base64=img_base64, summary_data=summary_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
