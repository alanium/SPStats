from flask import Flask, render_template, request, redirect,url_for
import json
from collections import defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import data
import base64
import io




app = Flask(__name__)
app.config['SECRET_KEY'] = 'AOHDNBIAAI189SD!A1'

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
def get_sales_meetings_data():
    entries = data.read(SP)
    result_dict = defaultdict(dict)

    for entry in entries:
        assigned_to = entry['properties']['Assigned to']['people']
        tags = entry['properties']['Tags']['multi_select']
        date_start_full = entry['properties']['Day/Hour']['date']['start'] if entry['properties']['Day/Hour']['date'] else None

        if assigned_to and tags and date_start_full:
            assigned_to_id = assigned_to[0]['id']
            tag_info = tags[0]

            if tag_info['name'] in ['QUALIFIED', 'NOT QUALIFIED', 'CANCELLED', 'PLANNING', 'CLOSING', 'TURN', 'RESCHEDULE']:
                # Replace assigned_to_id with the corresponding name from sales_persons
                assigned_to_name = sales_persons.get(assigned_to_id, "unknown")
                result_dict[assigned_to_name][date_start_full] = tag_info['name']

    return dict(result_dict)

def count_tags_by_month():
    input_dict = get_sales_meetings_data()
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

def calculate_stats():
    result_dict = {}

    #counts_by_month = count_tags_by_month()

    counts_by_month = {'MARK': {'QUALIFIED': {'2024-01': 6, '2023-12': 21, '2023-08': 34, '2023-11': 12, '2023-09': 27, '2023-10': 19, '2023-07': 2}, 'NOT QUALIFIED': {'2024-01': 1, '2023-12': 3, '2023-11': 1, '2023-10': 6, '2023-08': 5, '2023-09': 9}, 'CANCELLED': {'2023-10': 2, '2023-11': 2, '2023-09': 3, '2023-12': 1}, 'PLANNING': {'2024-01': 2, '2023-12': 12, '2023-11': 10, '2023-09': 3, '2023-10': 4, '2023-08': 1}, 'CLOSING': {'2023-12': 3, '2023-10': 4, '2023-08': 2, '2023-11': 1}, 'TURN': {'2023-12': 1, '2023-11': 3, '2023-10': 1}, 'RESCHEDULE': {'2023-12': 1, '2023-09': 3, '2023-08': 1, '2023-10': 2, '2023-11': 1}}, 'MORGAN WEST': {'QUALIFIED': {'2023-11': 9, '2023-09': 20, '2023-12': 7, '2023-08': 11, '2023-10': 6, '2024-01': 1}, 'NOT QUALIFIED': {'2024-01': 1, '2023-12': 10, '2023-08': 3, '2023-09': 4, '2023-11': 1, '2023-10': 5}, 'CANCELLED': {'2023-08': 1, '2023-09': 2}, 'PLANNING': {'2023-11': 1}, 'CLOSING': {'2023-08': 1}, 'TURN': {'2023-10': 3}, 'RESCHEDULE': {'2023-09': 1, '2023-11': 1}}, 'EDUARDO': {'QUALIFIED': {'2023-12': 
4, '2023-11': 2, '2023-09': 1}, 'NOT QUALIFIED': {'2023-12': 8, '2023-11': 4}, 'CANCELLED': {'2023-11': 3, '2023-10': 1, '2023-12': 3}, 'PLANNING': {'2023-11': 2}, 'CLOSING': {'2023-11': 1}, 'TURN': {}, 'RESCHEDULE': {'2023-12': 1}}, 'MORGAN': {'QUALIFIED': {'2023-08': 8, '2023-05': 12, '2023-07': 21, '2023-06': 12}, 'NOT QUALIFIED': {'2023-05': 7, '2023-07': 5, '2023-06': 3, '2023-08': 2}, 'CANCELLED': {'2023-08': 3, '2023-06': 4, '2023-07': 4, '2023-05': 6}, 'PLANNING': {'2023-06': 1}, 'CLOSING': {}, 'TURN': {}, 'RESCHEDULE': {'2023-07': 1, '2023-06': 1, '2023-05': 3}}, 'JONAS': {'QUALIFIED': {'2023-05': 1, '2023-06': 2, '2023-09': 1}, 'NOT QUALIFIED': {'2023-05': 3, '2023-06': 4}, 'CANCELLED': {'2023-05': 5, '2023-08': 1}, 'PLANNING': {}, 'CLOSING': {}, 'TURN': {'2023-11': 1}, 'RESCHEDULE': {'2023-06': 1}}, 'ALISON': {'QUALIFIED': {'2023-11': 6, '2023-12': 7, '2023-10': 4}, 'NOT QUALIFIED': {'2023-11': 5, '2023-12': 3, '2023-10': 2}, 'CANCELLED': {'2023-12': 2, '2023-11': 1}, 'PLANNING': {'2023-12': 2}, 'CLOSING': {'2023-12': 1}, 'TURN': {}, 'RESCHEDULE': {'2023-11': 1}}, 'DYLAN': {'QUALIFIED': {'2023-08': 18, '2023-07': 2, '2023-09': 1}, 'NOT QUALIFIED': {'2023-08': 4}, 'CANCELLED': {'2023-07': 2}, 'PLANNING': {}, 'CLOSING': {}, 'TURN': {}, 'RESCHEDULE': {}}, 'JAY': {'QUALIFIED': {'2023-07': 9, '2023-09': 9, '2023-08': 1, '2023-06': 3}, 'NOT QUALIFIED': {'2023-07': 5, '2023-10': 1, '2023-08': 1, '2023-06': 3, '2023-09': 1}, 'CANCELLED': {'2023-07': 1, '2023-05': 1, '2023-06': 1}, 'PLANNING': {'2023-11': 1}, 'CLOSING': {'2023-09': 1, '2023-08': 1}, 'TURN': {}, 'RESCHEDULE': {'2023-06': 2, '2023-10': 1, '2023-07': 1}}, 'unknown': {'QUALIFIED': {'2023-12': 1}, 'NOT QUALIFIED': {}, 'CANCELLED': {}, 'PLANNING': {}, 'CLOSING': {}, 'TURN': {}, 'RESCHEDULE': {}}, 'MILAGROS': {'QUALIFIED': {}, 'NOT QUALIFIED': {}, 'CANCELLED': {}, 'PLANNING': {'2023-06': 1}, 'CLOSING': {}, 'TURN': {}, 'RESCHEDULE': {}}}

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

def count_total_qualifies_by_month():
    input_dict = get_sales_meetings_data()
    output_dict = {}

    for key, inner_dict in input_dict.items():
        counts = {"QUALIFIED": {}}

        for date_str, value in inner_dict.items():
            # Parsea la fecha de entrada
            date_object = datetime.fromisoformat(date_str.split(".")[0])

            # Formatea la fecha como "aaaa-mm"
            formatted_date = date_object.strftime("%Y-%m")

            # Actualiza el recuento para las calificaciones y el mes correspondiente
            if value == 'QUALIFIED':
                counts["QUALIFIED"][formatted_date] = counts["QUALIFIED"].get(formatted_date, 0) + 1

        # Actualiza el diccionario externo con el diccionario de recuento
        output_dict[key] = counts

    return output_dict


# by month
def filter_stats_by_month(stats_data, selected_month):
    filtered_stats_data = {}
    for salesperson, stats in stats_data.items():
        month_goal = stats['month_goal']
        month_goal_qualifies_amount = stats['month_goal_qualifies_amount']
        total_qualifies = stats['total_qualifies']
        total_not_qualifies = stats['total_not_qualifies']
        conversion_rate = stats['conversion_rate']
        not_qualifies_rate = stats['not_qualifies_rate']

        if month_goal and month_goal.startswith(selected_month):
            filtered_stats_data[salesperson] = {                
                'Total Qualifies': total_qualifies,
                'Total Not Qualifies': total_not_qualifies,
                'Month Goal': month_goal,
                'Month Goal Qualifies Amount': month_goal_qualifies_amount,
                'Conversion Rate': f"{conversion_rate:.2%}",
                'Not Qualifies Rate': f"{not_qualifies_rate:.2%}"
            }

    return filtered_stats_data

# by range
def filter_stats_by_range(stats_data, start_year, start_month, end_year, end_month):
    filtered_stats_data = {}
    for salesperson, stats in stats_data.items():
        month_goal = stats['month_goal']
        month_goal_qualifies_amount = stats['month_goal_qualifies_amount']
        total_qualifies = stats['total_qualifies']
        total_not_qualifies = stats['total_not_qualifies']
        conversion_rate = stats['conversion_rate']
        not_qualifies_rate = stats['not_qualifies_rate']

        if month_goal:
            goal_year, goal_month = map(int, month_goal.split('-'))

            # Adaptar el formato de mes y año a 'YYYY/MM'
            formatted_goal_month = f"{goal_year}/{goal_month:02d}"

            formatted_start_month = f"{start_year}/{start_month:02d}"
            formatted_end_month = f"{end_year}/{end_month:02d}"

            if formatted_start_month <= formatted_goal_month <= formatted_end_month:
                filtered_stats_data[salesperson] = {
                    'Month Goal': month_goal,
                    'Month Goal Qualifies Amount': month_goal_qualifies_amount,
                    'Total Qualifies': total_qualifies,
                    'Total Not Qualifies': total_not_qualifies,
                    'Conversion Rate': f"{conversion_rate:.2%}",
                    'Not Qualifies Rate': f"{not_qualifies_rate:.2%}"
                }

    return filtered_stats_data



# Routes
@app.route('/')
def main_menu():
    return render_template('main_menu.html')

@app.route('/get_stats')
def get_stats():
    stats_data = calculate_stats()
    stats_data_last_30_days = calculate_stats_last_30_days()
    total_qualifies_by_month = count_total_qualifies_by_month()

    # Crear gráfico de barras para el total de calificaciones por mes
    plt.figure(figsize=(12, 6))
    months = list(total_qualifies_by_month['MARK']['QUALIFIED'].keys())
    x_positions = range(len(months))

    # Crear barras para Total Qualifies por mes
    total_qualifies_values = [sum(stats.get('QUALIFIED', {}).get(month, 0) for stats in total_qualifies_by_month.values()) for month in months]
    plt.bar(x_positions, total_qualifies_values, color='#666666')

    # Etiquetas en la punta de cada barra
    for x, total_qualifies in zip(x_positions, total_qualifies_values):
        plt.text(x, total_qualifies, str(total_qualifies), ha='center', va='bottom')

    plt.xlabel('Month')
    plt.ylabel('Total Qualifies')
    plt.title('Total Qualifies by Month')
    plt.xticks(x_positions, months)  # Posicionar etiquetas en el centro de cada barra

    # Guardar la imagen en BytesIO
    img_bytesio = BytesIO()
    plt.savefig(img_bytesio, format='png')
    img_bytesio.seek(0)

    # Convertir BytesIO a base64 para incrustar en la plantilla HTML
    img_base64_total_qualifies = f"data:image/png;base64,{base64.b64encode(img_bytesio.getvalue()).decode()}"

    # Crear gráfico circular
    plt.figure(figsize=(20, 6))
    labels = ['Qualified', 'Not Qualified']
    sizes = [
        sum(stats['total_qualifies'] for stats in stats_data_last_30_days.values()),
        sum(stats['total_not_qualifies'] for stats in stats_data_last_30_days.values())
    ]
    colors = ['#666666', '#262626']  # Colores más vibrantes

    # Configuración del gráfico
    plt.pie(sizes, labels=labels, colors=colors, autopct=lambda p: '{:.0f}'.format(p * sum(sizes) / 100),
            startangle=90, wedgeprops=dict(width=0.4, edgecolor='w'), pctdistance=0.80)
    
    # Configuración del porcentaje (tamaño y color)
    plt.gcf().get_axes()[0].texts[1].set_fontsize(16)
    plt.gcf().get_axes()[0].texts[1].set_color('white')
    plt.gcf().get_axes()[0].texts[0].set_fontsize(20)
    plt.gcf().get_axes()[0].texts[3].set_fontsize(16)
    plt.gcf().get_axes()[0].texts[3].set_color('white')
    plt.gcf().get_axes()[0].texts[2].set_fontsize(20)

    # Decoraciones adicionales
    plt.title('Last 30 Days', fontsize=16)
    plt.axis('equal')

    # Guardar la imagen en BytesIO
    img_bytesio = io.BytesIO()
    plt.savefig(img_bytesio, format='png', bbox_inches='tight')
    img_bytesio.seek(0)

    # Convertir BytesIO a base64 para incrustar en la plantilla HTML
    img_base64_last_30_days = f"data:image/png;base64,{base64.b64encode(img_bytesio.getvalue()).decode()}"
    
    # Crear gráfico de barras
    plt.figure(figsize=(12, 6))
    width = 0.35  # Ancho de las barras
    salespersons = list(stats_data.keys())
    x_positions = range(len(salespersons))

    # Crear barras para Qualified
    qualified_values = [stats['total_qualifies'] for stats in stats_data.values()]
    plt.bar(x_positions, qualified_values, width, label='Qualified', color='green')

    # Crear barras para Not Qualified al lado de las barras de Qualified
    not_qualified_values = [stats['total_not_qualifies'] for stats in stats_data.values()]
    plt.bar([x + width for x in x_positions], not_qualified_values, width, label='Not Qualified', color='red')

    # Etiquetas en la punta de cada barra
    for x, (qualified, not_qualified) in zip(x_positions, zip(qualified_values, not_qualified_values)):
        plt.text(x, qualified, str(qualified), ha='center', va='bottom')
        plt.text(x + width, not_qualified, str(not_qualified), ha='center', va='bottom')

    plt.xlabel('Salespersons')
    plt.ylabel('Count')
    plt.title('Qualified and Not Qualified Counts for Salespersons')
    plt.xticks([x + width / 2 for x in x_positions], salespersons)  # Posicionar etiquetas en el centro de cada par de barras
    plt.legend()

    # Guardar la imagen en BytesIO
    img_bytesio = BytesIO()
    plt.savefig(img_bytesio, format='png')
    img_bytesio.seek(0)

    # Convertir BytesIO a base64 para incrustar en la plantilla HTML
    img_base64 = f"data:image/png;base64,{base64.b64encode(img_bytesio.getvalue()).decode()}"

    # Crear resumen de cada salesperson
    summary_data = {}
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

        summary_data[salesperson] = {
            'Month Goal': month_goal,
            'Month Goal Qualifies Amount': month_goal_qualifies_amount,
            'Total Qualifies': total_qualifies,
            'Total Not Qualifies': total_not_qualifies,
            'Total Cancelled': total_cancelled,
            'visited': visited,
            'Conversion Rate': f"{conversion_rate:.2%}",
            'Not Qualifies Rate': f"{not_qualifies_rate:.2%}",
            'Cancelled Rate': f"{cancelled_rate:.2%}"
        }

    return render_template('index.html', img_base64_total_qualifies=img_base64_total_qualifies, img_base64_last_30_days = img_base64_last_30_days, img_base64=img_base64, summary_data=summary_data)

@app.route('/select_month', methods=['GET', 'POST'])
def select_month():
    if request.method == 'POST':
        selected_year = request.form['year']
        selected_month = request.form['month']
        selected_month_year = f"{selected_year}-{selected_month}"
        return redirect(url_for('show_selected_month', selected_month=selected_month_year))
    return render_template('select_month.html')

@app.route('/show_selected_month/<selected_month>')
def show_selected_month(selected_month):
    stats_data = calculate_stats()
    filtered_stats_data = filter_stats_by_month(stats_data, selected_month)

    return render_template('selected_month.html', selected_month=selected_month, filtered_stats_data=filtered_stats_data)

@app.route('/select_range', methods=['GET', 'POST'])
def select_range():
    if request.method == 'POST':
        start_year = request.form['start_year']
        start_month = request.form['start_month']
        end_year = request.form['end_year']
        end_month = request.form['end_month']

        return redirect(f'/show_selected_range/{start_year}/{start_month}-{end_year}/{end_month}')

    return render_template('select_range.html')

@app.route('/show_selected_range/<int:selected_year_first>/<int:selected_month_first>-<int:selected_year_second>/<int:selected_month_second>')
def show_selected_range(selected_year_first, selected_month_first, selected_year_second, selected_month_second):
    stats_data = calculate_stats()
    filtered_stats_data = filter_stats_by_range(stats_data, selected_year_first, selected_month_first, selected_year_second, selected_month_second)
    selected_range = f"{selected_year_first}/{selected_month_first}-to-{selected_year_second}/{selected_month_second}"
    return render_template('show_selected_range.html', selected_range=selected_range, filtered_stats_data=filtered_stats_data)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

