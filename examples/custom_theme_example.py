import customtkinter

#Use set_default_color_theme() to load all default settings for all widgets.
customtkinter.set_default_color_theme("blue")

#Optionally, you can use multiple times add_color_theme() to append new "theme_keys" or change existing ones.
if False:
    customtkinter.add_color_theme("custom_theme1.json")
    customtkinter.add_color_theme("custom_theme2.json")
    #...

#For custom JSON files, we suggest always using set_default_color_theme() with a built-in theme first,
# followed by add_color_theme() with your file. In this way, if new attributes or widgets are added to the library,
# you can upgrade it without the need to update your custom theme. If you use directly set_default_color_theme()
# with your custom theme, you risk that multiple KeyErrors would be raised after a library upgrade.


customtkinter.set_appearance_mode("dark")
app = customtkinter.CTk(title="CustomTkinter custom_theme_example.py")
frame = customtkinter.CTkFrame(master=app)
frame.pack(pady=20, padx=60, fill="both", expand=True)
radiobutton_var = customtkinter.IntVar(value=1)


#You can also create or update any keys programmatically using ThemeManager.add_key() and ThemeManager.update_key().
# Consider that custom theme_keys don't need to specify all values for a specific Widget: you can include just the items
# that you want to change with respect to default values. At the same time, you can specify additional settings that the
# widgets don't use: they simply will be ignored when not needed. This is also true for custom JSON files.
customtkinter.ThemeManager.add_key("MyButton",
                                   corner_radius=1000,
                                   border_width=7,
                                   border_color="white")

button_1 = customtkinter.CTkButton(master=frame, text="Default settings")
button_1.pack(pady=10, padx=10)

button_2 = customtkinter.CTkButton(master=frame, theme_key="MyButton", text="MyButton settings")
button_2.pack(pady=10, padx=10)

#Even if you provide a theme_key, you can always override the settings by providing the values to be used as parameters.
button_3 = customtkinter.CTkButton(master=frame,
                                   theme_key="MyButton",
                                   border_color="black",
                                   text="MyButton+Parameters settings")
button_3.pack(pady=10, padx=10)


#With this instruction, ALL CTkRadioButtons will have provided values as the default ones.
# It is equivalent to changing the values inside the JSON files that are provided with the library.
customtkinter.ThemeManager.update_key("CTkRadioButton",
                                      fg_color="red",
                                      hover=False,
                                      text="New Default settings")

radiobutton_1 = customtkinter.CTkRadioButton(master=frame,
                                             variable=radiobutton_var,
                                             value=1)
radiobutton_1.pack(pady=10, padx=10)

radiobutton_2 = customtkinter.CTkRadioButton(master=frame,
                                             variable=radiobutton_var,
                                             value=2)
radiobutton_2.pack(pady=10, padx=10)

#As always, you can change the default values using the parameters.
radiobutton_3 = customtkinter.CTkRadioButton(master=frame,
                                             variable=radiobutton_var,
                                             value=3,
                                             fg_color="yellow",
                                             hover=True,
                                             text="Parameters settings")
radiobutton_3.pack(pady=10, padx=10)

#You can easily generate a JSON file with the current settings by calling ThemeManager.save_theme(),
# so that you can restore it later.
if False:
    customtkinter.ThemeManager.save_theme("custom_theme.json")

app.mainloop()
