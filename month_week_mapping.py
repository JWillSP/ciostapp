from datetime import date, timedelta
import calendar

def get_first_monday(year):
    d = date(year, 1, 1)
    # Encontrar o primeiro dia da semana (segunda-feira)
    while d.weekday() != 0:
        d += timedelta(days=1)
    return d

def generate_week_dictionary(year):
    month_mapping = {
        'January': 'janeiro',
        'February': 'fevereiro',
        'March': 'março',
        'April': 'abril',
        'May': 'maio',
        'June': 'junho',
        'July': 'julho',
        'August': 'agosto',
        'September': 'setembro',
        'October': 'outubro',
        'November': 'novembro',
        'December': 'dezembro'
    }

    week_dict = {}
    d = get_first_monday(year)
    week = 1
    while d.year == year:
        start_date = d.strftime("%d/%m/%y")
        end_date = (d + timedelta(days=6)).strftime("%d/%m/%y")
        start_month = month_mapping[calendar.month_name[d.month]]
        end_month = month_mapping[calendar.month_name[(d + timedelta(days=6)).month]]
        week_dict[f"{week}ª semana - {start_date} ({start_month}) a {end_date} ({end_month})"] = week
        d += timedelta(days=7)
        week += 1
    return week_dict

# Obter o dicionário para o ano corrente


if __name__ == "__main__":
    # Imprimir o dicionário
    current_year = date.today().year
    month_week_mapping = generate_week_dictionary(current_year)
    for key, value in month_week_mapping.items():
        print(f"{key}: {value}")
