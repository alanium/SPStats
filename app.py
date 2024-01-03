from flask import Flask, render_template, request, redirect,url_for
import json
from collections import defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import data
import base64


app = Flask(__name__)
app.config['SECRET_KEY'] = 'AOHDNBIAAI189SD!A1'

with open('config.json', 'r') as config_file:
    constants = json.load(config_file)

# Constantes
SP = constants['SP']

# salesPersons with name
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


# Controlador

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

            if tag_info['name'] in ['QUALIFIED', 'NOT QUALIFIED']:
                # Replace assigned_to_id with the corresponding name from sales_persons
                assigned_to_name = sales_persons.get(assigned_to_id, "unknown")
                result_dict[assigned_to_name][date_start_full] = tag_info['name']

    return dict(result_dict)

def count_tags_by_month():
    input_dict = get_sales_meetings_data()
    output_dict = {}

    for key, inner_dict in input_dict.items():
        counts = {"QUALIFIED": {}, "NOT QUALIFIED": {}}

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

def calculate_stats():
    result_dict = {}

    #counts_by_month = count_tags_by_month()
    counts_by_month = {'MARK': {'QUALIFIED': {'2024-01': 1, '2023-12': 22, '2023-08': 34, '2023-11': 12, '2023-09': 27, '2023-10': 19, '2023-07': 2}, 'NOT QUALIFIED': {'2023-12': 3, '2023-11': 1, '2023-10': 6, '2023-08': 5, '2023-09': 9}}, 'EDUARDO': {'QUALIFIED': {'2023-12': 4, '2023-11': 2, '2023-09': 1}, 'NOT QUALIFIED': {'2023-12': 8, '2023-11': 4}}, 'MORGAN WEST': {'QUALIFIED': {'2023-11': 9, '2023-09': 20, '2023-12': 7, '2023-08': 11, '2023-10': 6}, 'NOT QUALIFIED': {'2023-12': 10, '2023-08': 3, '2023-09': 4, '2023-11': 1, '2023-10': 5}}, 'MORGAN': {'QUALIFIED': {'2023-08': 8, '2023-05': 12, '2023-07': 21, '2023-06': 12}, 'NOT QUALIFIED': {'2023-05': 7, '2023-07': 5, '2023-06': 3, '2023-08': 2}}, 'JONAS': {'QUALIFIED': {'2023-05': 1, '2023-06': 2, '2023-09': 1}, 'NOT QUALIFIED': {'2023-05': 3, '2023-06': 4}}, 'ALISON': {'QUALIFIED': {'2023-11': 6, '2023-12': 8, '2023-10': 4}, 'NOT QUALIFIED': {'2023-11': 5, '2023-12': 3, '2023-10': 2}}, 'DYLAN': {'QUALIFIED': {'2023-08': 
18, '2023-07': 2, '2023-09': 1}, 'NOT QUALIFIED': {'2023-08': 4}}, 'JAY': {'QUALIFIED': {'2023-07': 9, '2023-09': 9, '2023-08': 1, '2023-06': 3}, 'NOT QUALIFIED': {'2023-07': 5, '2023-10': 1, '2023-08': 1, '2023-06': 3, '2023-09': 1}}, 'unknown': {'QUALIFIED': {'2023-12': 1}, 'NOT QUALIFIED': {}}}

    for key, counts in counts_by_month.items():
        total_qualifies = sum(counts['QUALIFIED'].values())
        total_not_qualifies = sum(counts['NOT QUALIFIED'].values())

        # Finding the month with the maximum 'QUALIFIED' count
        month_goal = max(counts['QUALIFIED'], key=counts['QUALIFIED'].get, default=None)
        month_goal_qualifies_amount = counts['QUALIFIED'].get(month_goal, 0)

        # Calcular los ratios de conversión
        conversion_rate = total_qualifies / (total_qualifies + total_not_qualifies) if total_qualifies + total_not_qualifies > 0 else 0
        not_qualifies_rate = 1 - conversion_rate

        result_dict[key] = {
            'total_qualifies': total_qualifies,
            'total_not_qualifies': total_not_qualifies,
            'month_goal': month_goal,
            'month_goal_qualifies_amount': month_goal_qualifies_amount,
            'conversion_rate': conversion_rate,
            'not_qualifies_rate': not_qualifies_rate
        }

    return result_dict

def extract_id_from_read_item(id):
    response = data.read_item(id)
    
    assigned_to = response.get('properties', {}).get('Assigned to', {})
    if assigned_to.get('people'):
        return assigned_to['people'][0].get('id')
    else:
        return None

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
                'Month Goal': month_goal,
                'Month Goal Qualifies Amount': month_goal_qualifies_amount,
                'Total Qualifies': total_qualifies,
                'Total Not Qualifies': total_not_qualifies,
                'Conversion Rate': f"{conversion_rate:.2%}",
                'Not Qualifies Rate': f"{not_qualifies_rate:.2%}"
            }

    return filtered_stats_data

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
def index():
    stats_data = calculate_stats()

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
        conversion_rate = stats['conversion_rate']
        not_qualifies_rate = stats['not_qualifies_rate']

        summary_data[salesperson] = {
            'Month Goal': month_goal,
            'Month Goal Qualifies Amount': month_goal_qualifies_amount,
            'Total Qualifies': total_qualifies,
            'Total Not Qualifies': total_not_qualifies,
            'Conversion Rate': f"{conversion_rate:.2%}",
            'Not Qualifies Rate': f"{not_qualifies_rate:.2%}"
        }

    return render_template('index.html', img_base64=img_base64, summary_data=summary_data)

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

#--

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