import concurrent.futures
import tkinter as tk
from tkinter import ttk, messagebox
import business

"""
This module contains a class to construct a gui application to convert USD into 169 other currencies. 

Methods:
--------
    create_widgets(self):
        Creates the widgets in the GUI form
    on_load(self):
        Loads initial text into text display, starts thread to request currency data from the Treasury API
    convert_onclick(self):
        Handles the click event for the convert button
    on_close(self):
        Ends any non daemon thread on form close
    request_currency_data_for_combobox(self):
        Retrieves currency data from Treasury API
    on_currency_data_received_first_load(self, future):
        Passes currency data dict to the main thread to be displayed on in the country combobox. 
    update_conversion_form_first_load(self, currency_dict):
        Handles updating the gui (country dropdown) after successful treasury api call. 
    request_currency_data_for_convert(self):
        Starts a new thread to retrieve currency data from Treasury api for conversion. 
    on_currency_data_received_for_convert(self, future):
        Passes currency dict data to the main thread after non-daemon thread is done running.
    update_conversion_form_for_convert(self, currency_dict):
        Updates the GUI with the conversion calculation(s)
    update_gui_on_error(self, error):
        Updates the GUI if there is an error in either non-daemon thread
    update_text(self, message):
        Updates results_text with a given message
    validate_usd(self):
        Validates the user input within the USD entry
    validate_combobox(self):
        Validates that a country is selected from the combobox
    is_float(self, value):
        Determines if a given value is a float
"""


class ConversionForm(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Currency Converter')
        self.create_widgets()
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.on_load()

    def create_widgets(self):
        """
        Creates the widgets in the GUI form ConversionForm
        :return: n/a
        """
        # Currency label/dropdown
        self.select_currency_label = ttk.Label(self, text='Select Currency: ')
        self.select_currency_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.currency_dropdown = ttk.Combobox(self, state='disabled')
        self.currency_dropdown.grid(row=0, column=1, padx=5, pady=5)

        # USD amount label/entry
        self.enter_usd_label = ttk.Label(self, text="Enter amount in USD: ")
        self.enter_usd_label.grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.usd_entry = ttk.Entry(self)
        self.usd_entry.grid(row=1, column=1, padx=5, pady=5)

        # Convert button
        self.convert_button = ttk.Button(self, text='Convert', command=self.convert_onclick, state='disabled')
        self.convert_button.grid(row=2, column=1, padx=5, pady=5)

        # Result label & text
        self.result_label = ttk.Label(self, text="Result: ")
        self.result_label.grid(row=3, column=0, padx=5, pady=5)
        self.result_text = tk.Text(self, width=50, height=5, state='disabled')
        self.result_text.grid(row=3, column=1, padx=5, pady=5)

    def on_load(self):
        """
        Loads initial text into text display, starts thread to request currency data from the Treasury API
        :return: N/A
        """
        self.update_text("Loading currency list, one moment.")
        self.request_currency_data_for_combobox()

    def convert_onclick(self):
        """
        Handles the click event for the convert button
        :return: n/a
        """
        # lock button so it cannot be spammed.
        self.convert_button.config(state='disabled')
        self.request_currency_data_for_convert()

    def on_close(self):
        """
        Ends any non daemon thread on form close
        :return: n/a
        """
        self.executor.shutdown()
        self.destroy()

    def request_currency_data_for_combobox(self):
        """
        Retrieves currency data from Treasury API
        :return: n/a
        """
        future = self.executor.submit(business.get_currency_data)
        future.add_done_callback(self.on_currency_data_received_first_load)

    def on_currency_data_received_first_load(self, future):
        """
        Passes currency data dict to the main thread to be displayed on in the country combobox.
        :param future: callback response from executor
        :return: currency_dict, a dict of Currency objects.
        """
        try:
            currency_dict = future.result()
            self.after(0, self.update_conversion_form_first_load, currency_dict)
        except Exception as e:
            self.after(0, self.update_gui_on_error, e)

    def update_conversion_form_first_load(self, currency_dict):
        """
        Handles updating the gui (country dropdown) after successful treasury api call.
        :param currency_dict: a dict of Currency objects.
        :return: n/a
        """
        # self.check_which_countries_have_more_than_one_currency(currency_dict)
        key_list = list(currency_dict.keys())
        # self.check_for_duplicates(key_list)
        self.currency_dropdown.config(values=key_list)
        self.update_text("Currencies loaded, ready to convert!")
        self.currency_dropdown.config(state='readonly')
        self.convert_button.config(state='normal')

    def request_currency_data_for_convert(self):
        """
        Starts a new thread to retrieve currency data from Treasury api for conversion.
        :return: n/a
        """
        future = self.executor.submit(business.get_currency_data)
        future.add_done_callback(self.on_currency_data_received_for_convert)

    def on_currency_data_received_for_convert(self, future):
        """
        Passes currency dict data to the main thread after non-daemon thread is done running.
        :param future: callback response from executor
        :return: currency_dict, a dict of currency objects
        """
        try:
            currency_dict = future.result()
            self.after(0, self.update_conversion_form_for_convert, currency_dict)
        except Exception as e:
            self.after(0, self.update_gui_on_error(e))

    def update_conversion_form_for_convert(self, currency_dict):
        """
        Updates the GUI with the conversion calculation(s)
        :param currency_dict: a dict of currency objects
        :return: n/a
        """
        # grab the usd amount
        if self.validate_combobox() and self.validate_usd():
            usd_amount = self.usd_entry.get()
            # grab the country name from the dropdown
            country_to_convert = self.currency_dropdown.get()
            # unlock result text & delete what's in it.
            self.result_text.config(state='normal')
            self.result_text.delete('1.0', tk.END)
            # in some cases there are more than one currency per country, which is why I'm looping here.
            for currency in currency_dict[country_to_convert]:
                # grab the conversion from the Currency object.
                conversion_string = currency.convert(float(usd_amount))
                # put it in the result text
                self.result_text.insert(tk.END, f"{conversion_string}\n")
            # lock the result text again
            self.result_text.config(state='disabled')
            # unlock the convert button
            self.convert_button.config(state='normal')
        else:
            # if there is an invalid value or something is missing, reset entry and unlock convert button.
            self.usd_entry.delete(0, tk.END)
            self.convert_button.config(state='normal')

    def update_gui_on_error(self, error):
        """
        Updates the GUI if there is an error in either non-daemon thread
        :param error: error that has been caught
        :return: n/a
        """
        self.update_text(f"Error loading currency data, {error}")

    def update_text(self, message):
        """
        Updates results_text with a given message
        :param message: message to display to results_text
        :return: n/a
        """
        self.result_text.config(state='normal')
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert(tk.END, f"{message}")
        self.result_text.config(state='disabled')

    def validate_usd(self):
        """
        Validates the user input within the USD entry (not blank and is a float)
        :return: false if it fails, true if pass
        """
        usd_amount = self.usd_entry.get().strip()
        if usd_amount == "":
            messagebox.showinfo('Error', "You must enter a USD amount to convert!")
            return False
        if not self.is_float(usd_amount):
            messagebox.showinfo('Error', "USD amount can only be numbers (and decimal point...)")
            return False
        else:
            return True

    def validate_combobox(self):
        """
        Validates that a country is selected from the combobox
        :return: False if combobox has no selection, True if it has a selection.
        """
        selected_item = self.currency_dropdown.get()
        if selected_item == "":
            messagebox.showinfo('Error', "You have to select a currency!")
            return False
        else:
            return True

    def is_float(self, value):
        """
        determines if a user's input is a float
        :param value: the value to evaluate
        :return: true if the value is a float, false if not
        """
        try:
            float(value)
        except ValueError:
            return False
        if float(value) > 0.0:  # almost forgot to make sure it was positive!
            return True
        else:
            return False

    # def check_for_duplicates(self, input_list):
    #     # just for testing
    #     already_checked_items = []
    #     for item in input_list:
    #         if item in already_checked_items:
    #             print(item)
    #         already_checked_items.append(item)
    #     print('no duplicates!')

    # def check_which_countries_have_more_than_one_currency(self, currency_dict):
    #     # for testing
    #     for each_list in currency_dict.values():
    #         if len(each_list) > 1:
    #             print(each_list)



