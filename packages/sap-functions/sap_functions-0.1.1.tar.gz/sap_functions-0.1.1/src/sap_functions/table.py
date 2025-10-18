class Table:
    def __init__(self, table, session):
        self.table_obj = table
        self.session = session

    def __scroll_through_table(self, extension):
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

    def get_cell_value(self, row: int, column: str) -> str:
        try:
            return self.table_obj.getCell(row, column).text
        except:
            raise Exception("Get cell value failed.")

    def get_table_content(self):
        try:
            obj_now = self.__scroll_through_table(f'wnd[0]/usr')
            added_rows = []

            header = []
            content = []

            columns = obj_now.columns.count
            visible_rows = obj_now.visibleRowCount
            rows = obj_now.rowCount / visible_rows
            absolute_row = 0

            for c in range(columns):
                col_name = obj_now.columns.elementAt(c).title
                header.append(col_name)

            for i in range(int(rows)):
                for visible_row in range(visible_rows):
                    active_row = []
                    for c in range(columns):
                        try:
                            active_row.append(obj_now.getCell(visible_row, c).text)
                        except:
                            active_row.append(None)

                    absolute_row += 1

                    if not all(value is None for value in active_row) and absolute_row not in added_rows:
                        added_rows.append(absolute_row)
                        content.append(active_row)

                self.session.findById("wnd[0]").sendVKey(82)
                obj_now = self.__scroll_through_table(f'wnd[0]/usr')
            return {'header': header, 'content': content}

        except:
            raise Exception("Get table content failed.")
