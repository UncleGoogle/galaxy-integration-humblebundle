import webbrowser

import toga

from consts import IS_WINDOWS, IS_MAC

if IS_WINDOWS:
    from toga_winforms.libs import WinForms, Color
    from toga_winforms.widgets.label import Label as WinFormsLabel


# ---------- Tooltip implementation -------------

def set_tooltip(el: toga.Label, text):
    if IS_WINDOWS:
        tt = WinForms.ToolTip()
        tt.IsBalloon = True
        tt.InitialDelay = 500
        tt.ReshowDelay = 800
        tt.AutoPopDelay = 15000
        tt.SetToolTip(el._impl.native, text)
    elif IS_MAC:
        pass  # TODO, below snipets does not work
        # el._impl.native.toolTip = text
        # el._impl.native.setToolTip(text)


# ---------- LinkLabel implementation -----------

if IS_WINDOWS:
    class WinformsLinkLabel(WinFormsLabel):
        def create(self):
            self.native = WinForms.LinkLabel()
            self.native.LinkColor = Color.Black
            self.native.LinkClicked += WinForms.LinkLabelLinkClickedEventHandler(
                self.interface._link_clicked
            )

    
class LinkLabel(toga.Label):
    def __init__(self, text, link=None, id=None, style=None, factory=None):
        toga.Widget.__init__(self, id=id, style=style, factory=factory)

        if IS_WINDOWS:
            self._impl = WinformsLinkLabel(interface=self)
        elif IS_MAC:
            self._impl = self.factory.Label(interface=self)
            # no time for digging into cocoa NSTextField click handler
            # simple workaround for now
            self._impl.native.selectable = True

        self.link = link
        self.text = text
    
    @property
    def link(self):
        if self._link is None:
            return self.text
        return self._link
    
    @link.setter
    def link(self, link):
        self._link = link
    
    def _link_clicked(self, el, _):
        webbrowser.open(self.link)


# -----------------------------------------------

class OneColumnTable(toga.Table):
    """One column table"""
    MIN_WIDTH = 500

    def __init__(self, header: str, *args, **kwargs):
        super().__init__([header], *args, **kwargs)
        self.__set_full_width_one_column()

    def __set_full_width_one_column(self):
        if IS_WINDOWS:
            # self._impl.native in winforms is a ListView:
            # https://docs.microsoft.com/en-us/dotnet/api/system.windows.forms.listview?view=netframework-4.8
            width = self._impl.native.get_Width()
            # for some reason `width` is exactly half of the whole table
            self._impl.native.Columns[0].set_Width(width * 2)
        elif IS_MAC:
            pass  # TODO
    
    @property
    def not_empty(self):
        return len(self.data) > 0
    
    @property
    def selection(self):
        """Dummy addition for lacking toga implementation"""
        if IS_WINDOWS:
            idcs = self._impl.native.SelectedIndices
            selected_rows = []
            for i in idcs:
                selected_rows.append(self.data[i])
            if len(selected_rows) == 0:
                return None
            return selected_rows
        else:
            return super().selection


# -------------- Enhanced OptionsContainter -------------

class OptionContainer(toga.OptionContainer):
    def open_tab(self, index: int):
        if IS_WINDOWS:
            self._impl.native.SelectTab(index)
        elif IS_MAC:
            pass # TODO
