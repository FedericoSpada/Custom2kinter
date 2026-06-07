import customtkinter
import os


class ScrollableCheckBoxFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, item_list, command=None, **kwargs) -> None:
        super().__init__(master, **kwargs)

        self.command = command
        self.checkbox_list: list[customtkinter.CTkCheckBox] = []
        for item in item_list:
            self.add_item(item)

    def add_item(self, item) -> None:
        checkbox = customtkinter.CTkCheckBox(self, text=item)
        if self.command is not None:
            checkbox.configure(command=self.command)
        checkbox.grid(row=len(self.checkbox_list), column=0, pady=(0, 10))
        self.checkbox_list.append(checkbox)

    def remove_item(self, item) -> None:
        for checkbox in self.checkbox_list:
            if item == checkbox.cget("text"):
                checkbox.destroy()
                self.checkbox_list.remove(checkbox)
                return

    def get_checked_items(self) -> None:
        return [checkbox.cget("text") for checkbox in self.checkbox_list if checkbox.get() == 1]


class ScrollableRadiobuttonFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, item_list, command=None, **kwargs) -> None:
        super().__init__(master, **kwargs)

        self.command = command
        self.radiobutton_variable = customtkinter.StringVar()
        self.radiobutton_list: list[customtkinter.CTkRadioButton] = []
        for item in item_list:
            self.add_item(item)

    def add_item(self, item) -> None:
        radiobutton = customtkinter.CTkRadioButton(self, text=item, value=item, variable=self.radiobutton_variable)
        if self.command is not None:
            radiobutton.configure(command=self.command)
        radiobutton.grid(row=len(self.radiobutton_list), column=0, pady=(0, 10))
        self.radiobutton_list.append(radiobutton)

    def remove_item(self, item) -> None:
        for radiobutton in self.radiobutton_list:
            if item == radiobutton.cget("text"):
                radiobutton.destroy()
                self.radiobutton_list.remove(radiobutton)
                return

    def get_checked_item(self) -> str:
        return self.radiobutton_variable.get()


class ScrollableLabelButtonFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, command=None, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.command = command
        self.radiobutton_variable = customtkinter.StringVar()
        self.label_list: list[customtkinter.CTkLabel] = []
        self.button_list: list[customtkinter.CTkButton] = []

    def add_item(self, item, image=None) -> None:
        label = customtkinter.CTkLabel(self, text=item, image=image, compound="left", anchor="w")
        button = customtkinter.CTkButton(self, text="Command", width=100, height=24)
        if self.command is not None:
            button.configure(command=lambda: self.command(item))
        label.grid(row=len(self.label_list), column=0, pady=(0, 10), sticky="w")
        button.grid(row=len(self.button_list), column=1, pady=(0, 10), padx=5)
        self.label_list.append(label)
        self.button_list.append(button)

    def remove_item(self, item) -> None:
        for label, button in zip(self.label_list, self.button_list):
            if item == label.cget("text"):
                label.destroy()
                button.destroy()
                self.label_list.remove(label)
                self.button_list.remove(button)
                return


class App(customtkinter.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("CTkScrollableFrame example")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # create scrollable checkbox frame
        self.scrollable_checkbox_frame = ScrollableCheckBoxFrame(master=self, width=200, command=self.checkbox_frame_event,
                                                                 item_list=[f"item {i}" for i in range(50)])
        self.scrollable_checkbox_frame.grid(row=0, column=0, padx=15, pady=15, sticky="ns")
        self.scrollable_checkbox_frame.add_item("new item")

        # create scrollable radiobutton frame
        self.scrollable_radiobutton_frame = ScrollableRadiobuttonFrame(master=self, width=500, command=self.radiobutton_frame_event,
                                                                       item_list=[f"item {i}" for i in range(100)],
                                                                       label={"text": "ScrollableRadiobuttonFrame"})
        self.scrollable_radiobutton_frame.grid(row=1, column=0, padx=15, pady=15, sticky="ns")
        self.scrollable_radiobutton_frame.configure(width=200)
        self.scrollable_radiobutton_frame.remove_item("item 3")

        # create scrollable label and button frame
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.scrollable_label_button_frame = ScrollableLabelButtonFrame(master=self, width=300, command=self.label_button_frame_event, corner_radius=0)
        self.scrollable_label_button_frame.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        for i in range(20):  # add items with images
            self.scrollable_label_button_frame.add_item(f"image and item {i}",
                                                        image=customtkinter.CTkImage(light_image=os.path.join(current_dir, "test_images", "chat_light.png"),
                                                                                     height=20))

        # create scrollable frame containing scrollable widgets
        self.scrollable_frame_wsw = customtkinter.CTkScrollableFrame(master=self, corner_radius=0, label={"text": "Contains scrollable widgets"})
        self.scrollable_frame_wsw.grid(row=1, column=1, padx=0, pady=(5, 0), sticky="nsew")
        for n in range(5):
            slider = customtkinter.CTkSlider(self.scrollable_frame_wsw)
            slider.pack(pady=5)
            slider.set(0.25 * n)
        for n in range(3):
            scrollbar = customtkinter.CTkScrollbar(self.scrollable_frame_wsw, orientation="horizontal")
            scrollbar.pack(pady=5)
            scrollbar.set(0.3*n, 0.1 + 0.4*n)
        self.nested_scrollble_frame = customtkinter.CTkScrollableFrame(master=self.scrollable_frame_wsw, height=200, label={"text": "Nested CTkScrollableFrame"})
        self.nested_scrollble_frame.pack(fill="x", expand=True, padx = 5, pady=5)
        self.nested_scrollble_frame.grid_rowconfigure((0, 1), weight=1)
        self.nested_scrollble_frame.grid_columnconfigure((0, 1), weight=1)
        for n in range(4):
            textbox = customtkinter.CTkTextbox(self.nested_scrollble_frame, height=200)
            textbox.grid(row=n//2, column=n%2, padx=10, pady=10, sticky="nsew")
            textbox.insert("0.0", f"Textbox {n+1}\n" + "\n".join(f"Line {i+1}" for i in range(20*n)))

    def checkbox_frame_event(self) -> None:
        print(f"checkbox frame modified: {self.scrollable_checkbox_frame.get_checked_items()}")

    def radiobutton_frame_event(self) -> None:
        print(f"radiobutton frame modified: {self.scrollable_radiobutton_frame.get_checked_item()}")

    def label_button_frame_event(self, item) -> None:
        print(f"label button frame clicked: {item}")


if __name__ == "__main__":
    customtkinter.set_appearance_mode("dark")
    app = App()
    app.mainloop()
