import tkinter as tk
from tkinter import messagebox
import json, os, time, random

DATA_FILE = "bank_data.json"

# ---------- BACKEND ----------
class Transaction:
    def __init__(self, t_type, amount, timestamp=None):
        self.type = t_type
        self.amount = amount
        self.time = timestamp if timestamp else time.ctime()

    def to_dict(self):
        return {"type": self.type, "amount": self.amount, "time": self.time}

    @staticmethod
    def from_dict(data):
        return Transaction(data["type"], data["amount"], data["time"])


class Account:
    def __init__(self, acc_no, name, pin, balance=0):
        self.acc_no = acc_no
        self.name = name
        self.__pin = pin
        self.balance = balance
        self.transactions = []
        self.is_locked = False

    def verify_pin(self, pin):
        if self.is_locked:
            return False
        return self.__pin == pin

    def deposit(self, amount):
        self.balance += amount
        self.transactions.append(Transaction("Deposit", amount))

    def withdraw(self, amount):
        if amount > self.balance:
            return "Insufficient"
        self.balance -= amount
        self.transactions.append(Transaction("Withdraw", amount))
        if amount > 50000:
            self.is_locked = True
            return "Fraud"
        return "OK"

    def transfer(self, other, amount):
        if amount > self.balance:
            return False
        self.balance -= amount
        other.balance += amount
        self.transactions.append(Transaction("Transfer Sent", amount))
        other.transactions.append(Transaction("Transfer Received", amount))
        return True

    def to_dict(self):
        return {
            "acc_no": self.acc_no,
            "name": self.name,
            "pin": self._Account__pin,
            "balance": self.balance,
            "transactions": [t.to_dict() for t in self.transactions],
            "is_locked": self.is_locked
        }

    @staticmethod
    def from_dict(data):
        acc = Account(data["acc_no"], data["name"], data["pin"], data["balance"])
        acc.transactions = [Transaction.from_dict(t) for t in data["transactions"]]
        acc.is_locked = data["is_locked"]
        return acc


class Bank:
    def __init__(self):
        self.accounts = {}
        self.load()

    def load(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                for k, v in data.items():
                    self.accounts[int(k)] = Account.from_dict(v)

    def save(self):
        with open(DATA_FILE, "w") as f:
            json.dump({k: v.to_dict() for k, v in self.accounts.items()}, f, indent=4)

    def create_account(self, acc_no, name, pin):
        if acc_no in self.accounts:
            return False
        self.accounts[acc_no] = Account(acc_no, name, pin)
        self.save()
        return True

    def get_account(self, acc_no):
        return self.accounts.get(acc_no)


# ---------- GUI ----------
bank = Bank()
current_user = None

root = tk.Tk()
root.title("Smart Banking System")
root.geometry("420x500")
root.configure(bg="#1e1e2f")


def clear():
    for widget in root.winfo_children():
        widget.destroy()


def styled_button(text, command):
    return tk.Button(root, text=text, command=command,
                     bg="#4CAF50", fg="white",
                     font=("Arial", 10, "bold"),
                     width=22)


# ---------- OTP ----------
def send_otp():
    return random.randint(1000, 9999)


def verify_with_otp(acc, pin):
    if not acc.verify_pin(pin):
        return False
    otp = send_otp()
    print("OTP (simulation):", otp)  # check terminal
    user_otp = simple_input("Enter OTP")
    return user_otp and int(user_otp) == otp


# ---------- INPUT POPUP ----------
def simple_input(title):
    popup = tk.Toplevel()
    popup.title(title)
    popup.geometry("250x120")

    entry = tk.Entry(popup)
    entry.pack(pady=10)

    result = []

    def submit():
        result.append(entry.get())
        popup.destroy()

    tk.Button(popup, text="OK", command=submit).pack()
    popup.wait_window()
    return result[0] if result else None


# ---------- LOGIN ----------
def login_screen():
    clear()

    tk.Label(root, text="Bank Login", bg="#1e1e2f", fg="white",
             font=("Arial", 16)).pack(pady=20)

    acc_entry = tk.Entry(root)
    acc_entry.pack(pady=5)
    acc_entry.insert(0, "Account No")

    pin_entry = tk.Entry(root, show="*")
    pin_entry.pack(pady=5)
    pin_entry.insert(0, "PIN")

    def login():
        global current_user
        try:
            acc = bank.get_account(int(acc_entry.get()))
            if acc and verify_with_otp(acc, int(pin_entry.get())):
                current_user = acc
                dashboard()
            else:
                messagebox.showerror("Error", "Invalid Login")
        except:
            messagebox.showerror("Error", "Invalid Input")

    def register():
        try:
            acc_no = int(acc_entry.get())
            pin = int(pin_entry.get())
            if bank.create_account(acc_no, "User"+str(acc_no), pin):
                messagebox.showinfo("Success", "Account Created")
            else:
                messagebox.showerror("Error", "Account Exists")
        except:
            messagebox.showerror("Error", "Invalid Input")

    styled_button("Login", login).pack(pady=10)
    styled_button("Create Account", register).pack(pady=5)


# ---------- DASHBOARD ----------
def dashboard():
    clear()

    tk.Label(root, text=f"Welcome {current_user.name}",
             bg="#1e1e2f", fg="white",
             font=("Arial", 14)).pack(pady=10)

    def deposit():
        amt = simple_input("Deposit Amount")
        if amt:
            current_user.deposit(float(amt))
            bank.save()

    def withdraw():
        amt = simple_input("Withdraw Amount")
        if amt:
            res = current_user.withdraw(float(amt))
            bank.save()
            if res == "Fraud":
                messagebox.showwarning("Alert", "Account Locked (Fraud Detected)")

    def transfer():
        to = simple_input("Transfer to Account")
        amt = simple_input("Amount")
        if to and amt:
            other = bank.get_account(int(to))
            if other:
                current_user.transfer(other, float(amt))
                bank.save()-

    def show_balance():
        messagebox.showinfo("Balance", f"₹{current_user.balance}")

    def show_statement():
        text = "\n".join([f"{t.time} | {t.type} ₹{t.amount}" for t in current_user.transactions[-5:]])
        messagebox.showinfo("Statement", text if text else "No transactions")

    def show_analytics():
        deposits = sum(t.amount for t in current_user.transactions if t.type == "Deposit")
        withdraws = sum(t.amount for t in current_user.transactions if t.type == "Withdraw")
        transfers = sum(t.amount for t in current_user.transactions if "Transfer" in t.type)

        message = (
            f"Transaction Summary\n\n"
            f"Deposits: ₹{deposits}\n"
            f"Withdrawals: ₹{withdraws}\n"
            f"Transfers: ₹{transfers}\n"
            f"Balance: ₹{current_user.balance}"
        )

        messagebox.showinfo("Analytics", message)

    styled_button("Deposit", deposit).pack(pady=5)
    styled_button("Withdraw", withdraw).pack(pady=5)
    styled_button("Transfer", transfer).pack(pady=5)
    styled_button("Balance", show_balance).pack(pady=5)
    styled_button("Statement", show_statement).pack(pady=5)
    styled_button("Analytics", show_analytics).pack(pady=5)
    styled_button("Logout", login_screen).pack(pady=10)


# ---------- RUN ----------
login_screen()
root.mainloop()