# sap_functions
Library with utility classes and functions to facilitate the development of SAP automations in python.

This module is built on top of [SAP](https://sap.com) Scripting and aims to making the development of automated workflows easier and quicker.

## Implementation example
```python
from sap_functions import SAP

sap = SAP()
sap.select_transaction("COOIS")
```
This scripts:
1. Checks for existant SAP GUI instances.
2. Connects to that instance.
3. Write "COOIS" in the transaction field.

## Classes overview

### SAP
Handle general functions for SAP interactions.

**Attributes**:

`shell_obj`: Object with SAP native functions.  
`session`: the SAP user session.  
`window`: the SAP user session specific window.  
`side_index`: Saves temporary data of private functions.  
`desired_operator`: Saves temporary data of private functions.  
`desired_text`: Saves temporary data of private functions.  
`field_name`: Saves temporary data of private functions.  
`target_index`: Saves temporary data of private functions.  

**Methods**:

`__get_sap_connection(connection_str: str) -> win32com.client.CDispatch`: Get sap session or throw error.  
`__count_and_create_sap_screens(connection: win32com.client.CDispatch, window: int) -> None`: Create SAP windows until its the number passed.  
`__active_window() -> int`: Get active window number.  
`__scroll_through_tabs(area: win32com.client.CDispatch, extension: str, selected_tab: int) -> win32com.client.CDispatch`: Recursively searches for items in an area.  
`__scroll_through_shell(shell: win32com.client.CDispatch, extension: str) -> win32com.client.CDispatch`: Recursively searches for items in an shell based on extension.  
`__scroll_through_table(table: win32com.client.CDispatch, extension: str) -> win32com.client.CDispatch`: Recursively searches for items in an table based on extension.  
`__scroll_through_fields(area: win32com.client.CDispatch) -> win32com.client.CDispatch`: Recursively searched for items in a field area.  
`__scroll_through_fields(area: win32com.client.CDispatch) -> None`: Conditionals for different function calling.  
`select_transaction(transaction_code: str) -> None`: Select a transaction.  
`select_main_screen() -> None`: Get to main screen.  
`clean_all_fields() -> None`: Clean all fields in current screen.  
`run_actual_transaction() -> None`: Run actual transaction.  
`insert_variant(variant_name: str) -> None`: Insert variant in transaction.  
`change_active_tab(tab_index: int) -> None`: Change tab if there are more than one (popups).  
`write_text_field(field_id: str, text: str) -> None`: Write text to a specific field.  
`write_text_field_until(field_id: str, text: str, until: str) -> None`: Write text to a specific field "until" section.  
`choose_text_combo(field_id: str, option: str) -> None`: Interacts with choose text combo of a given field.  
`flag_field(field_id: str, flag: bool) -> None`: Flag checkbox fields.  
`flag_field_at_side(field_id: str, flag: bool) -> None`: Flag checkbox fields on the side.  
`option_field(field_id: str, option_index: int) -> None`: Chooses a radio button within a field.  
`press_button(button_id: str) -> None`: Interacts with a button by pressing it.  
`multiple_selection_field(field_id: str, values: list[str]) -> None`: Interacts with multiple selection of a given field.  
`find_text_field(field_id: str) -> str | None`: Get the value of a field or None if not found.  
`get_text_at_side(field_id: str) -> str | None`: Get the value at the side of a field.  
`multiple_selection_paste_data(field_id: str, data: str) -> None`: Paste a string into the multiple selection field.  
`navigate_into_menu_header(menu_path: list[str]) -> None`: Choose a path to go in the menu_header.  
`save_file(file_path: str, file_format: str) -> None`: Save a file in specific format and path.  
`get_table(table_id: str) -> win32com.client.CDispatch`: Get Table instance.  
`get_shell(shell_id: str) -> win32com.client.CDispatch`: Get Shell instance.  
`get_footer_message() -> str | None`: Get footer message.  

### Shell
Represents a SAP shell

**Attributes**:

`shell_obj`: Object with SAP native functions.  
`session`: the SAP user session.  

**Methods**:  
`select_layout(layout: str) -> None`: Select layout within a shell.  
`count_rows() -> int`: Get number of rows.   
`get_cell_value(index: int, column_id: str) -> str`: Get value of given cell.  
`get_shell_content() -> list[list[str]]`: Get the shell content in an object.  
`select_all_content() -> None`: Select all the shell content.  
`click_cell(index: int, column_id: str) -> None`: Click on specific cell.  
`press_button(field_name: str, skip_error: bool = False) -> None`: Press button in shell toolbar.  
`press_nested_button(*nested_fields: str, skip_error: bool = False) -> None`: Press nested button in shell toolbar.  
`select_column(column_id: int) -> None`: Select a column in the shell.  

### Table
Represents a SAP table

**Attributes**:

`table_obj`: Object with SAP native functions. 

**Methods**:

`get_cell_value(row: int, column: str) -> str`: Get value of given cell.

## Contributing

The sap_functions module is open for contributing, feel free to create an issue or submit your pr. 

## Maintainers

Gabriel Volles Marinho - gabrielvmarinho1711@gmail.com  
Robert Aron Zimmermann - robert.raz@gmail.com