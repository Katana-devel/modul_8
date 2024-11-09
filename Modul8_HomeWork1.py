from collections import UserDict
from datetime import datetime, date, timedelta
import re
import pickle

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

def string_to_date(date_string):
    return datetime.strptime(date_string, "%Y.%m.%d").date()

def date_to_string(date):
    return date.strftime("%Y.%m.%d")

def prepare_user_list(user_data):
    prepared_list = []
    for user in user_data:
        prepared_list.append({"name": user["name"], "birthday": string_to_date(user["birthday"])})
    return prepared_list

def find_next_weekday(start_date, weekday):
    days_ahead = weekday - start_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)

def adjust_for_weekend(birthday):
    if birthday.weekday() >= 5:
        return find_next_weekday(birthday, 0)
    return birthday


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    def __init__(self, name):
        super().__init__(name)

class Phone(Field):
    def __init__(self, phone):
        if len(phone) == 10 and phone.isdigit():
            super().__init__(phone)
        else:
            raise ValueError("Phone number must contain exactly 10 digits.")

class Birthday(Field):
    def __init__(self, value):
        super().__init__(value)
        verification = r"^\d{2}\.\d{2}\.\d{4}$"
        try:
            if re.match(verification, value):
                self.value = value
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self,phone_number):
        new_phone = Phone(phone_number)
        self.phones.append(new_phone)


    def remove_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                self.phones.remove(phone)
                break

    def edit_phone(self, old_number, new_number):
        Phone(new_number)
        for phone in self.phones:
            if phone.value == old_number:
                phone.value = new_number
                break
        else:
            raise ValueError(f"Can`t find {old_number}.")

    def find_phone(self, phone_number):
        try:
            for phone in self.phones:
                if phone.value == phone_number:
                    return phone
            return None
        except ValueError:
            return None

    def add_birthday(self, birthday):
        new_birthday = Birthday(birthday)
        self.birthday = new_birthday

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"

class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name, None)

    def delete(self, name):
        if name in self.data:
            self.data.pop(name)

    def get_upcoming_birthdays(self, days=7):
        upcoming_birthdays = []
        today = date.today()
        for user in self.data.values():
            if user.birthday is None:
                continue

            birthday_this_year = user.birthday.replace(year=today.year)
            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            if 0 <= (birthday_this_year - today).days <= days:
                congratulation_date = adjust_for_weekend(birthday_this_year)
                upcoming_birthdays.append(
                    {"name": user.name.value, "congratulation_date": date_to_string(congratulation_date)}
                )

        return upcoming_birthdays

    def __str__(self):
        contacts = "\n".join(str(record) for record in self.data.values())
        return f"Information about contacts:\n{contacts}"

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return "Give me name and phone please."
        except KeyError:
            return "Wrong key"
        except IndexError:
            return "Wrong index"
        except Exception as e:
            return f"An unexpected error occurred: {e}"

    return inner


def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    message = "Contact changed."
    if record is not None:
        record.edit_phone(old_phone, new_phone)
    else:
        message = "Contact not found"
    return message

@input_error
def show_phone(args,  book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record:
        return '; '.join(phone.value for phone in record.phones)
    return 'Contact not found'

@input_error
def show_all(book: AddressBook):
    result = []
    for name, record in book.data.items():
        phone_numbers = '; '.join(phone.value for phone in record.phones)
        birthday_str = f", Birthday: {record.birthday.value}" if record.birthday else ""
        result.append(f"{name}: {phone_numbers}{birthday_str}")

    return '\n'.join(result)

@input_error
def add_birthday(args, book: AddressBook):
    name, birthday, *_ = args
    record = book.find(name)
    message = "Birthday updated."

    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact and Birthday added."

    try:
        birthday_date = datetime.strptime(birthday, '%d.%m.%Y').date()
    except ValueError:
        return "Error: Invalid date format. Please use DD.MM.YYYY"

    record.birthday = birthday_date
    return message

@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if not record is None:
        if record.birthday is not None:
            return record.birthday.value
        else:
            return "Birthday not found"
    else:
        return "Contact and Birthday added"


@input_error
def birthdays(book: AddressBook):
    days = 7
    upcoming_birthdays = book.get_upcoming_birthdays(days)

    if not upcoming_birthdays:
        return "Немає днів народження на найближчі 7 днів."

    result = "Дні народження на найближчі 7 днів:\n"
    for birthday_info in upcoming_birthdays:
        name = birthday_info["name"]
        congratulation_date = birthday_info["congratulation_date"]
        result += f"{name}: {congratulation_date}\n"

    return result


def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            save_data(book)
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))
            save_data(book)

        elif command == "change":
            print(change_contact(args,book))
            save_data(book)

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))
            save_data(book)

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(book))
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()

