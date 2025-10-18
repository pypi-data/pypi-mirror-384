import win32com

class Shell:
    def __init__(self, shell_obj: win32com.client.CDispatch, session: win32com.client.CDispatch):
        self.shell_obj = shell_obj
        self.session = session

    def select_layout(self, layout: str) -> None:
        try:
            self.shell_obj.selectColumn("VARIANT")
            self.shell_obj.contextMenu()
            self.shell_obj.selectContextMenuItem("&FILTER")
            self.session.findById("wnd[2]/usr/ssub%_SUBSCREEN_FREESEL:SAPLSSEL:1105/ctxt%%DYN001-LOW").text = layout
            self.session.findById("wnd[2]/tbar[0]/btn[0]").press()
            self.session.findById(
                "wnd[1]/usr/ssubD0500_SUBSCREEN:SAPLSLVC_DIALOG:0501/cntlG51_CONTAINER/shellcont/shell").selectedRows = "0"
            self.session.findById(
                "wnd[1]/usr/ssubD0500_SUBSCREEN:SAPLSLVC_DIALOG:0501/cntlG51_CONTAINER/shellcont/shell").clickCurrentCell()
        except:
            raise Exception("Select layout failed.")

    def count_rows(self) -> int:
        try:
            rows = self.shell_obj.RowCount
            if rows > 0:
                visiblerow = self.shell_obj.VisibleRowCount
                visiblerow0 = self.shell_obj.VisibleRowCount
                npagedown = rows // visiblerow0
                if npagedown > 1:
                    for j in range(1, npagedown + 1):
                        try:
                            self.shell_obj.firstVisibleRow = visiblerow - 1
                            visiblerow += visiblerow0
                        except:
                            break
                self.shell_obj.firstVisibleRow = 0
            return rows
        except:
            raise Exception("Count rows failed.")

    def get_cell_value(self, index: int, column_id: str) -> str:
        try:
            return self.shell_obj.getCellValue(index, column_id)
        except:
            raise Exception("Get cell value failed.")

    def get_shell_content(self) -> list:
        try:
            grid_column = self.shell_obj.ColumnOrder
            rows = self.count_rows()
            cols = self.shell_obj.ColumnCount

            header = [self.shell_obj.getCellValue(i, grid_column(c)) for c in range(cols) for i in range(-1, 0)]
            data = [[self.shell_obj.getCellValue(i, grid_column(c)) for c in range(cols)] for i in range(0, rows)]
            return {'header': header, 'content': data}

        except:
            raise Exception("Get all Shell Content Failed.")

    def select_all_content(self) -> None:
        try:
            self.shell_obj.selectAll()
        except:
            raise Exception("Select All Content Failed.")

    def select_column(self, column_id: int) -> None:
        try:
            self.shell_obj.selectColumn(column_id)
        except:
            raise Exception("Select Column Failed.")

    def click_cell(self, index: int, column_id: str) -> None:
        try:
            self.shell_obj.SetCurrentCell(index, column_id)
            self.shell_obj.doubleClickCurrentCell()
        except:
            raise Exception("Click Cell Failed.")

    def press_button(self, field_name: str, skip_error: bool = False) -> None:
        try:
            found = False
            for i in range(100):
                button_id = self.shell_obj.GetToolbarButtonId(i)
                button_tooltip = self.shell_obj.GetToolbarButtonTooltip(i)
                if field_name == button_tooltip:
                    self.shell_obj.pressToolbarContextButton(button_id)
                    found = True
            if not found and not skip_error:
                raise Exception()
        except:
            raise Exception("Press button failed")
        
    def press_nested_button(self, *nested_fields: str, skip_error: bool = False) -> None:
        try:
            found = False
            for i in range(100):
                    button_id = self.shell_obj.GetToolbarButtonId(i)
                    button_tooltip = self.shell_obj.GetToolbarButtonTooltip(i)
                    if nested_fields[0] == button_tooltip:
                        self.shell_obj.pressToolbarContextButton(button_id)
                        self.shell_obj.SelectContextMenuItemByText(nested_fields[1])
                        found = True
            if not found and not skip_error:
                raise Exception()
        except:
            raise Exception("Press nested button failed")
