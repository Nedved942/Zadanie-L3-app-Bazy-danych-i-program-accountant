from flask import Flask, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from json import dumps, loads
from json.decoder import JSONDecodeError
from sqlalchemy import Text

app = Flask(__name__)
app.config["SECRET_KEY"] = "Tajny klucz"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db = SQLAlchemy(app)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer)


class Warehouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_of_product = db.Column(db.String(150))
    price_of_product = db.Column(db.Integer)
    amount_of_product = db.Column(db.Integer)


class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_of_operation = db.Column(db.String(120))
    description_of_operation = db.Column(Text)
    date_of_operation = db.Column(db.String(120))

    @staticmethod
    def list_to_json(list_of_description):
        return dumps(list_of_description)

    def give_description_of_operation(self):
        return loads(self.description_of_operation)


with app.app_context():
    db.create_all()


def give_operation_date():
    present_date = datetime.now()
    return present_date.strftime("%d-%m-%Y %H:%M:%S")


def read_amount_in_account():
    account = Account.query.first()
    if account:
        return account.amount
    else:
        return 0


def save_amount_in_account(amount_in_account):
    account = Account.query.first()
    if account:
        account.amount = amount_in_account
        db.session.commit()
    else:
        new_account = Account(amount=0)
        db.session.add(new_account)


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
    # Odczytanie stanu konta z bazy danych
    amount_in_account = read_amount_in_account()

    # Zmiana salda
    # Pobranie danych wejściowych
    difference_in_account = request.form.get("difference_in_account")

    if difference_in_account:
        difference_in_account = int(difference_in_account)
        amount_in_account += difference_in_account

        # Aktualizacja historii operacji - Dodanie operacji do tabeli bazy danych
        name_of_operation = "Saldo"
        description_of_operation = (f"Kwota operacji: {difference_in_account}",
                                    f"Stan konta po operacji: {amount_in_account}")
        date_of_operation = give_operation_date()

        new_operation = History(name_of_operation=name_of_operation,
                                description_of_operation=History.list_to_json(description_of_operation),
                                date_of_operation=date_of_operation)

        db.session.add(new_operation)

        # Commit do tabel bazy danych
        db.session.commit()

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

        #  Zwiększenie ilości i zamiana ceny produktu, jeśli jest na magazynie, jeśli nie dodanie go
        product_from_warehouse = Warehouse.query.filter(Warehouse.name_of_product == product_to_buy_name).first()
        if product_from_warehouse:
            product_from_warehouse.amount_of_product += product_to_buy_amount
            product_from_warehouse.price_of_product = product_to_buy_price
        else:
            new_product = Warehouse(name_of_product=product_to_buy_name,
                                    price_of_product=product_to_buy_price,
                                    amount_of_product=product_to_buy_amount)
            db.session.add(new_product)

        # Aktualizacja historii operacji
        name_of_operation = "Zakup"
        description_of_operation = (f"Nazwa zakupionego produktu: {product_to_buy_name}",
                                    f"Kwota zakupu za jeden produkt: {product_to_buy_price}",
                                    f"Ilość zakupionych produktów: {product_to_buy_amount}",
                                    f"Stan konta po operacji: {amount_in_account}")
        date_of_operation = give_operation_date()

        new_operation = History(name_of_operation=name_of_operation,
                                description_of_operation=History.list_to_json(description_of_operation),
                                date_of_operation=date_of_operation)

        db.session.add(new_operation)

        # Commit do tabel bazy danych
        db.session.commit()

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

        # Sprawdzenie czy produkt znajduje się w magazynie
        product_from_warehouse = Warehouse.query.filter(Warehouse.name_of_product == product_to_sell_name).first()
        if not product_from_warehouse:
            flash("Podanego produktu nie ma w spisie magazynowym!")
            return render_template("index.html", amount_in_account=amount_in_account)
        if product_from_warehouse:
            if product_to_sell_amount >= product_from_warehouse.amount_of_product:
                flash("Sprzedano całą ilość danego produktu.")

        # Odjęcie z magazynu sprzedawanej ilości towaru
        product_from_warehouse.amount_of_product -= product_to_sell_amount

        # Sprawdzenie czy jest wystarczająca ilość towaru w magazynie
        if product_from_warehouse.amount_of_product < 0:
            product_to_sell_amount += product_from_warehouse.amount_of_product
            print(f"Brak wystarczającej ilości danego towaru w magazynie. "
                  f"Sprzedano {product_to_sell_amount} sztuk.")
            product_from_warehouse.amount_of_product = 0

        # Dodanie do konta kwoty sprzedaży
        amount_in_account += (product_to_sell_price * product_to_sell_amount)

        # Jeśli ilość danego towaru = 0 usunięcie towaru z kartoteki magazynu
        if product_from_warehouse.amount_of_product == 0:
            Warehouse.query.filter(Warehouse.name_of_product == product_to_sell_name).delete()

        # Aktualizacja historii operacji
        name_of_operation = "Sprzedaż"
        description_of_operation = (f"Nazwa sprzedanego produktu: {product_to_sell_name}",
                                    f"Kwota sprzedaży za jeden produkt: {product_to_sell_price}",
                                    f"Ilość sprzedanych produktów: {product_to_sell_amount}",
                                    f"Stan konta po operacji: {amount_in_account}")
        date_of_operation = give_operation_date()

        new_operation = History(name_of_operation=name_of_operation,
                                description_of_operation=History.list_to_json(description_of_operation),
                                date_of_operation=date_of_operation)

        db.session.add(new_operation)

        # Commit do tabel bazy danych
        db.session.commit()

        # Dodanie komunikatu - Sprzedaż
        flash("Dokonano wpisu sprzedaży!")

    # Zapis stanu konta do bazy danych
    save_amount_in_account(amount_in_account)

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
