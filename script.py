import sys
import sqlite3
import secrets
import string
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QCheckBox, QLineEdit, QPushButton, QSpinBox, QListWidget, 
    QListWidgetItem, QSizePolicy, QMessageBox
)
import webbrowser

class PasswordItemWidget(QWidget):
    def __init__(self, id, password_name, login, password, description, website, usage_count, created_at, last_used, app):
        super().__init__()

        self.id = id
        self.password_name = password_name
        self.login = login
        self.password = password
        self.description = description
        self.website = website
        self.usage_count = usage_count
        self.created_at = created_at
        self.last_used = last_used
        self.app = app

        self.name_label = QLabel(f"#{id} {password_name}")
        self.delete_button = QPushButton('X')
        self.delete_button.clicked.connect(self.delete_password)
        self.delete_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)  # Set fixed size policy

        layout = QHBoxLayout()
        layout.addWidget(self.name_label)
        layout.addWidget(self.delete_button)

        self.setLayout(layout)

        # Set the tooltip to display the description
        self.setToolTip(f"Description: {description}\nCreated at: {created_at}\nLast used: {last_used}")

        # Connect the row click event to copy_password method
        self.mousePressEvent = self.copy_password

    def copy_password(self, event):
        clipboard = QApplication.clipboard()
        if self.website:
            webbrowser.open(self.website)
        if self.login:
            clipboard.setText(f"{self.login} {self.password}")
        else:
            clipboard.setText(self.password)
            
        print(f"Copied password to clipboard: {self.password}")

    def delete_password(self):
        reply = QMessageBox.question(self, 'Delete Password', f"Are you sure you want to delete the password for {self.password_name}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.app.delete_password(self.id)
            print(f"Deleted password: {self.password_name}")

class PasswordGenerator(QWidget):
    def __init__(self):
        super().__init__()

        self.symbols_checkbox = QCheckBox('Include Symbols')
        self.numbers_checkbox = QCheckBox('Include Numbers')
        self.capitalize_checkbox = QCheckBox('Capitalize Symbols')

        self.length_label = QLabel('Password Length:')
        self.length_spinbox = QSpinBox()
        self.length_spinbox.setRange(1, 50)
        self.length_spinbox.setValue(12)

        self.count_label = QLabel('Number of Passwords:')
        self.count_spinbox = QSpinBox()
        self.count_spinbox.setRange(1, 10)
        self.count_spinbox.setValue(10)

        self.generate_button = QPushButton('Generate Passwords')
        self.generate_button.clicked.connect(self.generate_passwords)

        self.password_list = QListWidget()

        self.name_label = QLabel('Password Name:')
        self.name_input = QLineEdit()

        self.login_label = QLabel('Login:')
        self.login_input = QLineEdit()

        self.description_label = QLabel('Description:')
        self.description_input = QLineEdit()

        self.website_label = QLabel('Website:')
        self.website_input = QLineEdit()

        self.save_button = QPushButton('Save Password')
        self.save_button.clicked.connect(self.save_password)

        self.saved_passwords_list = QListWidget()  # List to display saved passwords
        self.db_connection = sqlite3.connect('passwords.db')
        self.create_table()
        self.load_saved_passwords()

        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        left_layout.addWidget(self.symbols_checkbox)
        left_layout.addWidget(self.numbers_checkbox)
        left_layout.addWidget(self.capitalize_checkbox)
        left_layout.addWidget(self.length_label)
        left_layout.addWidget(self.length_spinbox)
        left_layout.addWidget(self.count_label)
        left_layout.addWidget(self.count_spinbox)
        left_layout.addWidget(self.generate_button)
        left_layout.addWidget(self.password_list)
        left_layout.addWidget(self.name_label)
        left_layout.addWidget(self.name_input)
        left_layout.addWidget(self.login_label)  # Added login label
        left_layout.addWidget(self.login_input)
        left_layout.addWidget(self.website_label)
        left_layout.addWidget(self.website_input)
        left_layout.addWidget(self.description_label)
        left_layout.addWidget(self.description_input)
        left_layout.addWidget(self.save_button)

        right_layout.addWidget(self.saved_passwords_list)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.setLayout(main_layout)
        self.setWindowTitle('Password Generator')

        self.password_list.itemClicked.connect(self.copy_password)

    def create_table(self):
        # Create a table if it doesn't exist
        with self.db_connection:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS passwords (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    login TEXT,
                    password TEXT,
                    description TEXT NULL,
                    website TEXT NULL,
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP
                );
            ''')

    def generate_passwords(self):
        symbols = string.ascii_letters
        if self.symbols_checkbox.isChecked():
            symbols += string.punctuation
        if self.numbers_checkbox.isChecked():
            symbols += string.digits

        passwords = []
        for _ in range(self.count_spinbox.value()):
            password = ''.join(secrets.choice(symbols) for _ in range(self.length_spinbox.value()))
            if self.capitalize_checkbox.isChecked():
                password = password.capitalize()
            passwords.append(password)

        self.password_list.clear()
        self.password_list.addItems(passwords)

    def copy_password(self, item):
        # Copy the selected password to the clipboard
        password = item.text()
        clipboard = QApplication.clipboard()
        clipboard.setText(password)
        print(f"Copied password to clipboard: {password}")

    def save_password(self):
        password_name = self.name_input.text()
        if password_name:
            selected_passwords = self.password_list.selectedItems()
            if selected_passwords:
                password = selected_passwords[0].text()
                self.insert_password(password_name, password)
                print(f"Saved Password: {password_name} - {password}")
                self.load_saved_passwords()  # Refresh the saved passwords list
            else:
                print("No password selected.")
        else:
            print("Please enter a password name.")

    def insert_password(self, name, password, login=None,  description=None, website=None):
        with self.db_connection:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO passwords (name, login, password, description, website)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, login, password, description, website))

    def load_saved_passwords(self):
        with self.db_connection:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                SELECT id, name, login, password, description, website, usage_count, created_at, last_used
                FROM passwords
            ''')
            saved_passwords = cursor.fetchall()
            self.saved_passwords_list.clear()
            for id, name, login, password, description, website, usage_count, created_at, last_used in saved_passwords:
                password_item_widget = PasswordItemWidget(
                    id, name, login, password, description, website, usage_count, created_at, last_used, self
                )
                item = QListWidgetItem(self.saved_passwords_list)
                item.setSizeHint(password_item_widget.sizeHint())
                self.saved_passwords_list.addItem(item)
                self.saved_passwords_list.setItemWidget(item, password_item_widget)

    def delete_password(self, id):
        with self.db_connection:
            cursor = self.db_connection.cursor()
            cursor.execute('DELETE FROM passwords WHERE id = ?', (id,))
        self.load_saved_passwords()  
        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PasswordGenerator()
    window.show()
    sys.exit(app.exec())
