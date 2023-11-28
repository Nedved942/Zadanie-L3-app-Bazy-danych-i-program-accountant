from flask import Flask, render_template, request, flash
from datetime import datetime
from json import dumps, loads
from json.decoder import JSONDecodeError

app = Flask(__name__)
app.config["SECRET_KEY"] = "Tajny klucz"


def give_operation_date():
    present_date = datetime.now()
    return present_date.strftime("%d-%m-%Y %H:%M:%S")


def read_amount_in_account():
    try:
        with open("data_amount_in_account.txt") as file_stream:
            amount_txt_data = file_stream.readline()

            if amount_txt_data:
                return amount_txt_data
    except FileNotFoundError:
        print("Nie pobrano danych z pliku.")


def read_warehouse():
    try:
        with open("warehouse.json") as file_stream:
            warehouse_txt_data = file_stream.read()

            if not warehouse_txt_data:
                print("Plik jest pusty.")
            else:
                return loads(warehouse_txt_data)
    except FileNotFoundError:
        print("Nie pobrano danych z pliku.")
    except JSONDecodeError as e:
        print(f"Wystąpił nieoczekiwany błąd {e}.")


def read_operation_history():
    try:
        with open("operation_history.json") as file_stream:
            operation_history_txt_data = file_stream.read()

            if not operation_history_txt_data:
                pass
                print("Plik jest pusty.")
            else:
                return loads(operation_history_txt_data)
    except FileNotFoundError:
        print("Nie pobrano danych z pliku.")
    except JSONDecodeError as e:
        print(f"Wystąpił nieoczekiwany błąd {e}.")


@app.route("/", methods=["GET", "POST"])
def index():
    # Odczytanie danych z plików
    amount_in_account = int(read_amount_in_account())
    warehouse = read_warehouse()
    operation_history = read_operation_history()

    # Dodanie lub odjęcie wartości od kwoty na koncie
    # Pobranie danych wejściowych
    difference_in_account = request.form.get("difference_in_account")

    if difference_in_account:
        difference_in_account = int(difference_in_account)
        amount_in_account += difference_in_account

        # Aktualizacja historii operacji - Saldo
        operation_history.append({"Nazwa operacji": "Saldo",
                                  "Opis operacji":
                                      (
                                          f"Kwota operacji: {difference_in_account}",
                                          f"Stan konta po operacji: {amount_in_account}"
                                      ),
                                  "Data operacji": give_operation_date()})

        # Dodanie komunikatu - Saldo
        flash("Zmieniono stan konta!")

    # Zakup produktu
    # Pobranie danych wejściowych
    product_to_buy_name = request.form.get("product_to_buy_name")
    product_to_buy_price = request.form.get("product_to_buy_price")
    product_to_buy_amount = request.form.get("product_to_buy_amount")

    if product_to_buy_name and product_to_buy_price and product_to_buy_amount:
        product_to_buy_price = int(product_to_buy_price)
        product_to_buy_amount = int(product_to_buy_amount)

        amount_in_account = amount_in_account - (product_to_buy_price * product_to_buy_amount)

        #  Zwiększenie ilości i zamiana ceny produktu, jeśli jest na magazynie
        if product_to_buy_name in warehouse:
            warehouse[product_to_buy_name]["amount"] = warehouse[product_to_buy_name]["amount"] \
                                                       + product_to_buy_amount
            warehouse[product_to_buy_name]["price"] = product_to_buy_price
        else:
            # Dodanie produktu do słownika magazynu
            warehouse[product_to_buy_name] = {
                "price": product_to_buy_price,
                "amount": product_to_buy_amount
            }

        # Aktualizacja historii operacji
        operation_history.append({"Nazwa operacji": "Zakup",
                                  "Opis operacji":
                                      (
                                          f"Nazwa zakupionego produktu: {product_to_buy_name}",
                                          f"Kwota zakupu za jeden produkt: {product_to_buy_price}",
                                          f"Ilość zakupionych produktów: {product_to_buy_amount}",
                                          f"Stan konta po operacji: {amount_in_account}"
                                      ),
                                  "Data operacji": give_operation_date()})

        # Dodanie komunikatu - Zakup
        flash("Dokonano wpisu zakupu!")

    # Sprzedaż produktu
    # Pobranie danych wejściowych
    product_to_sell_name = request.form.get("product_to_sell_name")
    product_to_sell_price = request.form.get("product_to_sell_price")
    product_to_sell_amount = request.form.get("product_to_sell_amount")

    if product_to_sell_name and product_to_sell_price and product_to_sell_amount:
        product_to_sell_price = int(product_to_sell_price)
        product_to_sell_amount = int(product_to_sell_amount)
        if product_to_sell_name not in warehouse:
            flash("Podanego produktu nie ma w spisie magazynowym!")
            return render_template("index.html", amount_in_account=amount_in_account)
        if product_to_sell_amount >= warehouse[product_to_sell_name]["amount"]:
            flash("Sprzedano całą ilość danego produktu.")

        # Odjęcie z magazynu sprzedawanej ilości towaru
        warehouse[product_to_sell_name]["amount"] = \
            warehouse[product_to_sell_name]["amount"] - product_to_sell_amount

        # Sprawdzenie czy jest wystarczająca ilość towaru w magazynie
        if warehouse[product_to_sell_name]["amount"] < 0:
            product_to_sell_amount = product_to_sell_amount + warehouse[product_to_sell_name]["amount"]
            print(f"Brak wystarczającej ilości danego towaru w magazynie. "
                  f"Sprzedano {product_to_sell_amount} sztuk.")
            warehouse[product_to_sell_name]["amount"] = 0

        # Dodanie do konta kwoty sprzedaży
        amount_in_account = amount_in_account + (product_to_sell_price * product_to_sell_amount)

        # Jeśli ilość danego towaru = 0 usunięcie towaru z kartoteki magazynu
        if warehouse[product_to_sell_name]["amount"] == 0:
            del warehouse[product_to_sell_name]

        # Aktualizacja historii operacji
        operation_history.append({"Nazwa operacji": "Sprzedaż",
                                  "Opis operacji":
                                      (
                                          f"Nazwa sprzedanego produktu: {product_to_sell_name}",
                                          f"Kwota sprzedaży za jeden produkt: {product_to_sell_price}",
                                          f"Ilość sprzedanych produktów: {product_to_sell_amount}",
                                          f"Stan konta po operacji: {amount_in_account}"
                                      ),
                                  "Data operacji": give_operation_date()})

        # Dodanie komunikatu - Sprzedaż
        flash("Dokonano wpisu sprzedaży!")

    # Zapisanie danych do plików
    with open("data_amount_in_account.txt", "w") as file_stream:
        file_stream.write(str(amount_in_account))

    with open("warehouse.json", "w") as file_stream:
        file_stream.write(dumps(warehouse))

    with open("operation_history.json", "w") as file_stream:
        file_stream.write(dumps(operation_history))

    print("Poprawnie zapisano dane.")
    return render_template("index.html", amount_in_account=amount_in_account)


@app.route("/historia/", methods=["GET", "POST"])
def history():
    # Odczytanie danych z plików
    operation_history = read_operation_history()

    # Określenie początkowego i końcowego indeksu odczytu historii
    start = request.form.get("start_operation")
    end = request.form.get("end_operation")
    if start and end:
        start = int(start)
        end = int(end) + 1
    else:
        start = 0
        end = len(operation_history)

    return render_template("history.html", operation_history=operation_history, start=start, end=end)


@app.route("/stan/")
def store():
    # Odczytanie danych z plików
    warehouse = read_warehouse()
    amount_in_account = read_amount_in_account()
    return render_template("store.html", warehouse=warehouse, amount_in_account=amount_in_account)
