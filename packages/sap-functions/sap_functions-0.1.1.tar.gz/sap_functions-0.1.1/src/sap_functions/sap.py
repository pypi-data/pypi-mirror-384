import win32com.client
import re
import os
import time
import warnings
from .shell import Shell
from .table import Table
from typing import Union

# SAP Scripting Documentation:
# https://help.sap.com/docs/sap_gui_for_windows/b47d018c3b9b45e897faf66a6c0885a8/a2e9357389334dc89eecc1fb13999ee3.html

# module SAP Functions, development started in 2024/03/01
class SAP:

    def __init__(self, window: int = 0) -> None:
        self.side_index = None
        self.desired_operator = None
        self.desired_text = None
        self.field_name = None
        self.target_index = None

        connection = self.__get_sap_connection()

        if connection.Children(0).info.user == '':
            raise Exception("SAP user is logged out!\nYou need to log in to SAP to run this script! Please log in and try again.")

        if connection.Children(0).info.systemName == 'EQ0':
            print("You're with SAP Quality Assurance open, (SAP QA)\nMany things may not happen as desired!")

        self.__count_and_create_sap_screens(connection, window)
        self.session = connection.Children(window)
        self.window = self.__active_window()

    def __get_sap_connection(self) -> win32com.client.CDispatch:
        try:
            sapguiauto = win32com.client.GetObject('SAPGUI')
            application = sapguiauto.GetScriptingEngine
            return application.Children(0)
        except:
            raise Exception(
                "SAP is not open!\nSAP must be open to run this script! Please, open it and try to run again.")

    def __count_and_create_sap_screens(self, connection:win32com.client.CDispatch, window: int):
        while len(connection.sessions) < window + 1:
            connection.Children(0).createSession()
            time.sleep(3)

    def __active_window(self) -> int:
        regex = re.compile('[0-9]')
        matches = regex.findall(self.session.ActiveWindow.name)
        for match in matches:
            return int(match)

    def __scroll_through_tabs(self, area: win32com.client.CDispatch, extension: str, selected_tab: int) -> win32com.client.CDispatch:
        children = area.Children
        for child in children:
            if child.Type == "GuiTabStrip":
                extension = extension + "/tabs" + child.name
                return self.__scroll_through_tabs(self.session.findById(extension), extension, selected_tab)
            if child.Type == "GuiTab":
                extension = extension + "/tabp" + str(children[selected_tab].name)
                return self.__scroll_through_tabs(self.session.findById(extension), extension, selected_tab)
            if child.Type == "GuiSimpleContainer":
                extension = extension + "/sub" + child.name
                return self.__scroll_through_tabs(self.session.findById(extension), extension, selected_tab)
            if child.Type == "GuiScrollContainer" and 'tabp' in extension:
                extension = extension + "/ssub" + child.name
                area = self.session.findById(extension)
                return area
        return area

    def __scroll_through_shell(self, extension: str) -> Union[bool, win32com.client.CDispatch]:
        if self.session.findById(extension).Type == 'GuiShell':
            try:
                var = self.session.findById(extension).RowCount
                return self.session.findById(extension)
            except:
                pass
        children = self.session.findById(extension).Children
        result = False
        for i in range(len(children)):
            if result:
                break
            if children[i].Type == 'GuiCustomControl':
                result = self.__scroll_through_shell(extension + '/cntl' + children[i].name)
            if children[i].Type == 'GuiSimpleContainer':
                result = self.__scroll_through_shell(extension + '/sub' + children[i].name)
            if children[i].Type == 'GuiScrollContainer':
                result = self.__scroll_through_shell(extension + '/ssub' + children[i].name)
            if children[i].Type == 'GuiTableControl':
                result = self.__scroll_through_shell(extension + '/tbl' + children[i].name)
            if children[i].Type == 'GuiTab':
                result = self.__scroll_through_shell(extension + '/tabp' + children[i].name)
            if children[i].Type == 'GuiTabStrip':
                result = self.__scroll_through_shell(extension + '/tabs' + children[i].name)
            if children[
                i].Type in ("GuiShell GuiSplitterShell GuiContainerShell GuiDockShell GuiMenuBar GuiToolbar "
                            "GuiUserArea GuiTitlebar"):
                result = self.__scroll_through_shell(extension + '/' + children[i].name)
        return result

    def __scroll_through_grid(self, extension: str) -> Union[bool, win32com.client.CDispatch]:
        if self.session.findById(extension).Type == 'GuiShell':
            try:
                var = self.session.findById(extension).RowCount
                return self.session.findById(extension)
            except:
                pass
        children = self.session.findById(extension).Children
        result = False
        for i in range(len(children)):
            if result:
                break
            if children[i].Type == 'GuiCustomControl':
                result = self.__scroll_through_grid(extension + '/cntl' + children[i].name)
            if children[i].Type == 'GuiSimpleContainer':
                result = self.__scroll_through_grid(extension + '/sub' + children[i].name)
            if children[i].Type == 'GuiScrollContainer':
                result = self.__scroll_through_grid(extension + '/ssub' + children[i].name)
            if children[i].Type == 'GuiTableControl':
                result = self.__scroll_through_grid(extension + '/tbl' + children[i].name)
            if children[i].Type == 'GuiTab':
                result = self.__scroll_through_grid(extension + '/tabp' + children[i].name)
            if children[i].Type == 'GuiTabStrip':
                result = self.__scroll_through_grid(extension + '/tabs' + children[i].name)
            if children[
                i].Type in ("GuiShell GuiSplitterShell GuiContainerShell GuiDockShell GuiMenuBar GuiToolbar "
                            "GuiUserArea GuiTitlebar"):
                result = self.__scroll_through_grid(extension + '/' + children[i].name)
        return result

    def __scroll_through_table(self, extension: str) -> Union[bool, win32com.client.CDispatch]:
        if 'tbl' in extension:
            try:
                return self.session.findById(extension)
            except:
                pass
        children = self.session.findById(extension).Children
        result = False
        for i in range(len(children)):
            if result:
                break
            if children[i].Type == 'GuiCustomControl':
                result = self.__scroll_through_table(extension + '/cntl' + children[i].name)
            if children[i].Type == 'GuiSimpleContainer':
                result = self.__scroll_through_table(extension + '/sub' + children[i].name)
            if children[i].Type == 'GuiScrollContainer':
                result = self.__scroll_through_table(extension + '/ssub' + children[i].name)
            if children[i].Type == 'GuiTableControl':
                result = self.__scroll_through_table(extension + '/tbl' + children[i].name)
            if children[i].Type == 'GuiTab':
                result = self.__scroll_through_table(extension + '/tabp' + children[i].name)
            if children[i].Type == 'GuiTabStrip':
                result = self.__scroll_through_table(extension + '/tabs' + children[i].name)
            if children[
                i].Type in ("GuiShell GuiSplitterShell GuiContainerShell GuiDockShell GuiMenuBar GuiToolbar "
                            "GuiUserArea GuiTitlebar"):
                result = self.__scroll_through_table(extension + '/' + children[i].name)
        return result

    def __scroll_through_fields(self, extension: str, objective: str, selected_tab: int) -> bool:
        children = self.session.findById(extension).Children
        result = False
        for i in range(len(children)):
            if not result:
                result = self.__generic_conditionals(i, children, objective)

            if result:
                break

            if not result and children[i].Type == "GuiTabStrip" and 'ssub' not in extension:
                result = self.__scroll_through_fields(extension + "/tabs" + children[i].name, objective, selected_tab)

            if not result and children[i].Type == "GuiTab" and 'tabp' not in extension:
                result = self.__scroll_through_fields(extension + "/tabp" + str(children[selected_tab].name), objective,
                                                      selected_tab)

            if not result and children[i].Type == "GuiSimpleContainer":
                result = self.__scroll_through_fields(extension + "/sub" + children[i].name, objective, selected_tab)

            if not result and children[i].Type == "GuiScrollContainer":
                result = self.__scroll_through_fields(extension + "/ssub" + children[i].name, objective, selected_tab)

            if not result and children[i].Type == "GuiCustomControl":
                result = self.__scroll_through_fields(extension + "/cntl" + children[i].name, objective, selected_tab)

            if not result and children[i].Type in (
            "GuiShell GuiSplitterShell GuiContainerShell GuiDockShell GuiMenuBar GuiToolbar GuiUserArea GuiTitlebar"):
                result = self.__scroll_through_fields(extension + "/" + children[i].name, objective, selected_tab)

        return result

    # Contains generic conditional statements for different objectives.
    def __generic_conditionals(self, index: int, children: win32com.client.CDispatch, objective: str) -> bool:
        if objective == 'write_text_field':
            if children(index).Text == self.field_name:
                if self.target_index == 0:
                    try:
                        children(index + 1).Text = self.desired_text
                        return True
                    except:
                        return False
                else:
                    self.target_index -= 1

        if objective == 'write_text_field_until':
            if children(index).Text == self.field_name:
                if self.target_index == 0:
                    try:
                        children(index + 3).Text = self.desired_text
                        return True
                    except:
                        return False
                else:
                    self.target_index -= 1

        if objective == 'find_text_field':
            child = children(index)
            if (self.field_name in child.Text or
                    ('HTMLControl' in child.Text and self.field_name in child.BrowserHandle.document.all(0).innerText)):
                return True
            return False

        if objective == 'multiple_selection_field':
            if children(index).Text == self.field_name:
                if self.target_index == 0:
                    try:
                        field = children(index).name
                        initial_position = field.find("%") + 1
                        final_position = field.find("-", initial_position)
                        field = field[initial_position:final_position] + "-VALU_PUSH"
                        for j in range(index, len(children)):
                            Obj = children[j]
                            if field in Obj.name:
                                Obj.press()
                                return True
                    except:
                        return False
                    return False
                else:
                    self.target_index -= 1

        if objective == 'flag_field':
            if children(index).Text == self.field_name:
                if self.target_index == 0:
                    try:
                        children(index).Selected = self.desired_operator
                        return True
                    except:
                        return False
                else:
                    self.target_index -= 1

        if objective == 'flag_field_at_side':
            if children(index).Text == self.field_name:
                if self.target_index == 0:
                    try:
                        children(index + self.side_index).Selected = self.desired_operator
                        return True
                    except:
                        return False
                else:
                    self.target_index -= 1

        if objective == 'option_field':
            if children(index).Text == self.field_name:
                if self.target_index == 0:
                    try:
                        children(index).Select()
                        return True
                    except:
                        return False
                else:
                    self.target_index -= 1

        if objective == 'press_button':
            try:
                if self.field_name in children(index).Text or self.field_name in children(index).Tooltip:
                    children(index).press()
                    return True
                if self.session.info.transaction == 'CJ20N' or self.session.info.transaction == 'MD04':
                    try:
                        for i in range(101):
                            if children(index).GetButtonTooltip(i) != '':
                                id_button = children(index).GetButtonId(i)
                                tooltip_button = children(index).GetButtonTooltip(i)
                                if self.field_name in tooltip_button:
                                    children(index).pressButton(id_button)
                    except:
                        return False
            except:
                return False
            return False

        if objective == 'choose_text_combo':
            if children(index).Text == self.field_name:
                if self.target_index == 0:
                    try:
                        entries = children(index + 1).Entries
                        for cont in range(len(entries)):
                            entry = entries.Item(cont)
                            if self.desired_text == str(entry.Value):
                                children(index + 1).key = entry.key
                                return True
                    except:
                        return False
                    return False

        if objective == 'get_text_at_side':
            if children(index).Text == self.field_name:
                if self.target_index == 0:
                    try:
                        self.found_text = children(index + self.side_index).Text
                        return True
                    except:
                        return False
        return False

    def select_transaction(self, transaction: str) -> None:
        try:
            transaction_upper = transaction.upper()
            self.session.startTransaction(transaction_upper)
            if self.session.activeWindow.name == 'wnd[1]' and 'CN' in transaction_upper:
                self.session.findById("wnd[1]/usr/ctxtTCNT-PROF_DB").Text = "000000000001"
                self.session.findById("wnd[1]/tbar[0]/btn[0]").press()
            if not self.session.info.transaction == transaction_upper:
                raise Exception()
        except:
            raise Exception("Select transaction failed.\n" + self.get_footer_message())

    def select_main_screen(self, skip_error: bool = False) -> None:
        try:
            if not self.session.info.transaction == "SESSION_MANAGER":
                self.session.startTransaction('SESSION_MANAGER')
                if self.session.ActiveWindow.name == "wnd[1]":
                    self.session.findById("wnd[1]/tbar[0]/btn[0]").press()
        except:
            if not skip_error: raise Exception("Select main screen failed.")

    def clean_all_fields(self, selected_tab: int = 0, skip_error = False) -> None:
        try:
            self.window = self.__active_window()
            area = self.__scroll_through_tabs(self.session.findById(f"wnd[{self.window}]/usr"),
                                              f"wnd[{self.window}]/usr",
                                              selected_tab)
            children = area.Children
            for child in children:
                if child.Type == "GuiCTextField":
                    try:
                        child.Text = ""
                    except:
                        pass
        except:
            if not skip_error: raise Exception("Clean all fields failed.")

    def run_actual_transaction(self) -> None:
        try:
            self.window = self.__active_window()
            screen_title = self.session.activeWindow.text
            self.session.findById(f'wnd[{self.window}]').sendVKey(0)
            if screen_title == self.session.activeWindow.text:
                self.session.findById(f'wnd[{self.window}]').sendVKey(8)
        except:
            raise Exception("Run actual transaction failed.")

    def insert_variant(self, variant_name: str, skip_error: bool = False) -> None:
        try:
            self.session.findById("wnd[0]/tbar[1]/btn[17]").press()
            if self.session.activeWindow.name == 'wnd[1]':
                self.session.findById("wnd[1]/usr/txtV-LOW").Text = variant_name
                self.session.findById("wnd[1]/usr/txtENAME-LOW").Text = ""
                self.session.findById("wnd[1]/tbar[0]/btn[8]").press()
                if self.session.activewindow.name == 'wnd[1]':
                    raise Exception()
        except:
            if not skip_error: raise Exception("Insert variant failed.")

    def change_active_tab(self, selected_tab: int, skip_error: bool = False) -> None:
        try:
            self.window = self.__active_window()

            area = self.__scroll_through_tabs(self.session.findById(f"wnd[{self.window}]/usr"),
                                              f"wnd[{self.window}]/usr",
                                              selected_tab)
            try:
                area.Select()
            except:
                pass
        except:
            if not skip_error: raise Exception("Change active tab failed.")


    def write_text_field(self, field_name: str, desired_text: str, target_index: int = 0, selected_tab: int = 0, skip_error: bool = False) -> None:
        try:
            self.window = self.__active_window()
            self.field_name = field_name
            self.desired_text = desired_text
            self.target_index = target_index
            if selected_tab > 0:
                self.change_active_tab(selected_tab)
            if not self.__scroll_through_fields(f"wnd[{self.window}]/usr", 'write_text_field', selected_tab):
                raise Exception()
        except:
            if not skip_error: raise Exception("Write text field failed.")

    def write_text_field_until(self, field_name: str, desired_text: str, target_index: int = 0, selected_tab: int = 0, skip_error: bool = False) -> None:
        try:
            self.window = self.__active_window()
            self.field_name = field_name
            self.desired_text = desired_text
            self.target_index = target_index
            if selected_tab > 0:
                self.change_active_tab(selected_tab)
            if not self.__scroll_through_fields(f"wnd[{self.window}]/usr", 'write_text_field_until', selected_tab):
                raise Exception()
        except:
            if not skip_error: raise Exception("Write text field until failed.")

    def choose_text_combo(self, field_name: str, desired_text: str, target_index: int = 0, selected_tab: int = 0, skip_error: bool = False) -> None:
        try:
            self.window = self.__active_window()
            self.field_name = field_name
            self.desired_text = desired_text
            self.target_index = target_index
            if selected_tab > 0:
                self.change_active_tab(selected_tab)
            if not self.__scroll_through_fields(f"wnd[{self.window}]/usr", 'choose_text_combo', selected_tab):
                raise Exception()
        except:
            if not skip_error: raise Exception("Choose text combo failed.")

    def flag_field(self, field_name: str, desired_operator: bool, target_index: int = 0, selected_tab: int = 0, skip_error: bool = False) -> None:
        try:
            self.window = self.__active_window()
            self.field_name = field_name
            self.desired_operator = desired_operator
            self.target_index = target_index
            if selected_tab > 0:
                self.change_active_tab(selected_tab)
            if not self.__scroll_through_fields(f"wnd[{self.window}]/usr", 'flag_field', selected_tab):
                raise Exception()
        except:
            if not skip_error: raise Exception("Flag field failed.")

    def flag_field_at_side(self, field_name: str, desired_operator: bool, side_index: int = 0, target_index: int = 0, selected_tab: int = 0, skip_error: bool = False) -> None:
        try:
            self.window = self.__active_window()
            self.field_name = field_name
            self.desired_operator = desired_operator
            self.target_index = target_index
            self.side_index = side_index
            if selected_tab > 0:
                self.change_active_tab(selected_tab)
            if not self.__scroll_through_fields(f"wnd[{self.window}]/usr", 'flag_field_at_side', selected_tab):
                raise Exception()
        except:
            if not skip_error: raise Exception("Flag field at side failed.")

    def option_field(self, field_name: str, target_index: int = 0, selected_tab: int = 0, skip_error: bool = False) -> None:
        try:
            self.window = self.__active_window()
            self.field_name = field_name
            self.target_index = target_index
            if selected_tab > 0:
                self.change_active_tab(selected_tab)
            if not self.__scroll_through_fields(f"wnd[{self.window}]/usr", 'option_field', selected_tab):
                raise Exception()
        except:
            if not skip_error: raise Exception("Option field failed.")

    def press_button(self, field_name: str, target_index: int = 0, selected_tab: int = 0, skip_error: bool = False) -> None:
        try:
            self.window = self.__active_window()
            self.field_name = field_name
            self.target_index = target_index
            if selected_tab > 0:
                self.change_active_tab(selected_tab)
            if not self.__scroll_through_fields(f"wnd[{self.window}]", 'press_button', selected_tab):
                raise Exception()
        except:
            if not skip_error: raise Exception("Press button failed.")

    def multiple_selection_field(self, field_name: str, target_index: int = 0, selected_tab: int = 0, skip_error: bool = False) -> None:
        try:
            self.window = self.__active_window()
            self.field_name = field_name
            self.target_index = target_index
            if selected_tab > 0:
                self.change_active_tab(selected_tab)
            if not self.__scroll_through_fields(f"wnd[{self.window}]/usr", 'multiple_selection_field', selected_tab):
                raise Exception()
        except:
            if not skip_error: raise Exception("Multiple selection field failed.")

    def find_text_field(self, field_name: str, selected_tab=0) -> bool:
        self.window = self.__active_window()
        self.field_name = field_name
        if selected_tab > 0:
            self.change_active_tab(selected_tab)
        return self.__scroll_through_fields(f"wnd[{self.window}]/usr", 'find_text_field', selected_tab)

    def get_text_at_side(self, field_name, side_index: int, target_index: int = 0, selected_tab: int = 0) -> str:
        self.window = self.__active_window()
        self.field_name = field_name
        self.target_index = target_index
        self.side_index = side_index
        if selected_tab > 0:
            self.change_active_tab(selected_tab)
        if self.__scroll_through_fields(f"wnd[{self.window}]", 'get_text_at_side', selected_tab):
            return self.found_text

    def multiple_selection_paste_data(self, data: str, skip_error: bool = False) -> None:
        try:
            with open('C:/Temp/temp_paste.txt', 'w') as arquivo:
                arquivo.write(data)
            self.session.findById("wnd[1]/tbar[0]/btn[23]").press()
            self.session.findById("wnd[2]/usr/ctxtDY_PATH").text = 'C:/Temp'
            self.session.findById("wnd[2]/usr/ctxtDY_FILENAME").text = "temp_paste.txt"
            self.session.findById("wnd[2]/tbar[0]/btn[0]").press()
            self.session.findById("wnd[1]/tbar[0]/btn[8]").press()
            if os.path.exists('C:/Temp/temp_paste.txt'):
                os.remove('C:/Temp/temp_paste.txt')
        except:
            if not skip_error: raise Exception("Multiple selection paste data failed.")

    def navigate_into_menu_header(self, path: str) -> None:
        id_path = 'wnd[0]/mbar'
        if ';' not in path:
            raise Exception("The menu path must be in the format 'path1;path2;path3'")

        list_of_paths = path.split(';')
        for active_path in list_of_paths:
            children = self.session.findById(id_path).Children
            for i in range(children.Count):
                Obj = children(i)
                if active_path in Obj.Text:
                    menu_address = Obj.ID.split("/")[-1]
                    id_path += f'/{menu_address}'
                    break
        self.session.findById(id_path).Select()

    def save_file(self, file_name: str, path: str, option: int = 0, type_of_file: str = 'txt', skip_error: bool = False) -> None:
        try:
            if 'xls' in type_of_file:
                self.session.findById("wnd[0]/mbar/menu[0]/menu[1]/menu[1]").Select()
                self.session.findById("wnd[1]/tbar[0]/btn[0]").press()
            else:
                self.session.findById("wnd[0]/mbar/menu[0]/menu[1]/menu[2]").Select()
                self.session.findById(
                    f"wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[{option},0]").Select()
                self.session.findById("wnd[1]/tbar[0]/btn[0]").press()

            self.session.findById("wnd[1]/usr/ctxtDY_PATH").Text = path
            self.session.findById("wnd[1]/usr/ctxtDY_FILENAME").Text = f'{file_name}.{type_of_file}'
            self.session.findById("wnd[1]/tbar[0]/btn[11]").press()
        except:
            if not skip_error: raise Exception("Save file failed.")

    def view_in_list_form(self) -> None:
        warnings.warn("Deprecated in 0.1. "
                      "SAP.view_in_list_form will be removed in 1.0. "
                      "Use SAP.get_shell and its respective methods instead.", DeprecationWarning, stacklevel=2)
        try:
            my_grid = self.get_my_grid()
            my_grid.pressToolbarContextButton("&MB_VIEW")
            my_grid.SelectContextMenuItem("&PRINT_BACK_PREVIEW")
        except:
            raise Exception("View in list form failed.")

    def get_table(self) -> None:
        try:
            self.window = self.__active_window()
            table_obj = self.__scroll_through_table(f'wnd[{self.window}]/usr')
            if not table_obj:
                raise Exception()
            table = Table(table_obj, self.session)
            return table
        except:
            raise Exception("Get table failed.")

    def get_my_table(self) -> None:
        warnings.warn("Deprecated in 0.1. "
                      "SAP.get_my_table will be removed in 1.0. "
                      "Use SAP.get_table instead.", DeprecationWarning, stacklevel=2)
        try:
            self.window = self.__active_window()
            my_table = self.__scroll_through_table(f'wnd[{self.window}]/usr')
            if not my_table:
                raise Exception()
            return my_table
        except:
            raise Exception("Get my table failed.")

    def my_table_get_cell_value(self, my_table: win32com.client.CDispatch, row_index: int, column_index: int) -> str:
        warnings.warn("Deprecated in 0.1. "
                      "SAP.my_table_get_cell_value will be removed in 1.0. "
                      "Use SAP.get_table and its respective methods instead.", DeprecationWarning, stacklevel=2)
        try:
            return my_table.getCell(row_index, column_index).Text
        except:
            raise Exception("My table get cell value failed.")

    # my_table tips:
    # VisibleRowCount => Count the number of Visible Rows in the table
    # RowCount => Count the number of Rows inside the table

    def get_shell(self) -> Shell:
        try:
            self.window = self.__active_window()
            shell_obj = self.__scroll_through_shell(f'wnd[{self.window}]/usr')
            
            if not shell_obj:
                raise Exception()
            
            shell = Shell(shell_obj, self.session)
            return shell
        except:
            raise Exception("Get shell failed.")

    def get_my_grid(self) -> win32com.client.CDispatch:
        warnings.warn("Deprecated in 0.1. "
                      "SAP.get_my_grid will be removed in 1.0. "
                      "Use SAP.get_shell instead.", DeprecationWarning, stacklevel=2)
        try:
            self.window = self.__active_window()
            my_grid = self.__scroll_through_grid(f'wnd[{self.window}]/usr')
            if not my_grid:
                raise Exception()
            return my_grid
        except:
            raise Exception("Get my grid failed.")

    def my_grid_select_layout(self, layout: str, skip_error: bool = False) -> None:
        warnings.warn("Deprecated in 0.1. "
                      "SAP.my_grid_select_layout will be removed in 1.0. "
                      "Use SAP.get_shell and its respective methods instead.", DeprecationWarning, stacklevel=2)
        try:
            my_grid = self.get_my_grid()
            my_grid.selectColumn("VARIANT")
            my_grid.contextMenu()
            my_grid.selectContextMenuItem("&FILTER")
            self.session.findById("wnd[2]/usr/ssub%_SUBSCREEN_FREESEL:SAPLSSEL:1105/ctxt%%DYN001-LOW").text = layout
            self.session.findById("wnd[2]/tbar[0]/btn[0]").press()
            self.session.findById(
                "wnd[1]/usr/ssubD0500_SUBSCREEN:SAPLSLVC_DIALOG:0501/cntlG51_CONTAINER/shellcont/shell").selectedRows = "0"
            self.session.findById(
                "wnd[1]/usr/ssubD0500_SUBSCREEN:SAPLSLVC_DIALOG:0501/cntlG51_CONTAINER/shellcont/shell").clickCurrentCell()
        except:
            if not skip_error: raise Exception("My grid select layout failed.")

    def get_my_grid_count_rows(self, my_grid: win32com.client.CDispatch) -> int:
        warnings.warn("Deprecated in 0.1. "
                      "SAP.get_my_grid_count_rows will be removed in 1.0. "
                      "Use SAP.get_shell and its respective methods instead.", DeprecationWarning, stacklevel=2)
        try:
            self.window = self.__active_window()
            rows = my_grid.RowCount
            if rows > 0:
                visiblerow = my_grid.VisibleRowCount
                visiblerow0 = my_grid.VisibleRowCount
                npagedown = rows // visiblerow0
                if npagedown > 1:
                    for j in range(1, npagedown + 1):
                        try:
                            my_grid.firstVisibleRow = visiblerow - 1
                            visiblerow += visiblerow0
                        except:
                            break
                my_grid.firstVisibleRow = 0
            return rows
        except:
            raise Exception("Get my grid count rows failed.")

    def get_footer_message(self) -> str:
        try:
            return self.session.findById("wnd[0]/sbar").Text
        except:
            raise Exception("Get footer message failed.")
