from flask import Flask, render_template
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

    counts_by_month = count_tags_by_month()

    for key, counts in counts_by_month.items():
        total_qualifies = sum(counts['QUALIFIED'].values())
        total_not_qualifies = sum(counts['NOT QUALIFIED'].values())

        # Finding the month with the maximum 'QUALIFIED' count
        month_goal = max(counts['QUALIFIED'], key=counts['QUALIFIED'].get, default=None)
        month_goal_qualifies_amount = counts['QUALIFIED'].get(month_goal, 0)

        result_dict[key] = {
            'total_qualifies': total_qualifies,
            'total_not_qualifies': total_not_qualifies,
            'month_goal': month_goal,
            'month_goal_qualifies_amount': month_goal_qualifies_amount
        }

    return result_dict

def extract_id_from_read_item(id):
    response = data.read_item(id)
    
    assigned_to = response.get('properties', {}).get('Assigned to', {})
    if assigned_to.get('people'):
        return assigned_to['people'][0].get('id')
    else:
        return None

test = {'MARK': {'total_qualifies': 117, 'total_not_qualifies': 24, 'month_goal': '2023-08', 'month_goal_qualifies_amount': 34}, 'EDUARDO': {'total_qualifies': 7, 'total_not_qualifies': 12, 'month_goal': '2023-12', 'month_goal_qualifies_amount': 4}, 'MORGAN WEST': {'total_qualifies': 53, 'total_not_qualifies': 23, 'month_goal': '2023-09', 'month_goal_qualifies_amount': 20}, 'MORGAN': {'total_qualifies': 53, 'total_not_qualifies': 17, 'month_goal': '2023-07', 'month_goal_qualifies_amount': 21}, 'JONAS': {'total_qualifies': 4, 'total_not_qualifies': 7, 'month_goal': '2023-06', 'month_goal_qualifies_amount': 2}, 'ALISON': {'total_qualifies': 18, 'total_not_qualifies': 10, 'month_goal': '2023-12', 'month_goal_qualifies_amount': 8}, 'DYLAN': {'total_qualifies': 21, 'total_not_qualifies': 4, 'month_goal': '2023-08', 'month_goal_qualifies_amount': 18}, 'JAY': {'total_qualifies': 22, 'total_not_qualifies': 11, 'month_goal': '2023-07', 'month_goal_qualifies_amount': 9}, 'unknown': {'total_qualifies': 1, 'total_not_qualifies': 0, 'month_goal': '2023-12', 'month_goal_qualifies_amount': 1}}

#todo: usar test para motivos de testing en lugar de usar alculate_stats

@app.route('/')
def index():
    stats_data = test

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

        summary_data[salesperson] = {
            'Month Goal': month_goal,
            'Month Goal Qualifies Amount': month_goal_qualifies_amount,
            'Total Qualifies': total_qualifies,
            'Total Not Qualifies': total_not_qualifies
        }

    return render_template('index.html', img_base64=img_base64, summary_data=summary_data)



if __name__ == '__main__':
    app.run(debug=True)