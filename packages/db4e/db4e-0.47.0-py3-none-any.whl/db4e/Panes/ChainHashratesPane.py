"""
db4e/Panes/ChainHashratesPane.py

    Database 4 Everything
    Author: Nadim-Daniel Ghaznavi 
    Copyright: (c) 2024-2025 Nadim-Daniel Ghaznavi
    GitHub: https://github.com/NadimGhaznavi/db4e
    License: GPL 3.0
"""

from textual.containers import Container, Vertical, ScrollableContainer, Horizontal
from textual.widgets import Label, Select, Static
from textual.reactive import reactive


from db4e.Modules.P2Pool import P2Pool

from db4e.Widgets.Db4EPlot import Db4EPlot

from db4e.Constants.DLabel import DLabel
from db4e.Constants.DField import DField
from db4e.Constants.DForm import DForm
from db4e.Constants.DSelect import DSelect



# The values are for selecting the amount of data to show.
# There is one data point per hour....


class ChainHashratesPane(Container):

    selected_time = DSelect.ONE_WEEK
    intro_label = Label("", classes=DForm.INTRO)
    instance_label = Label("", id=DForm.INSTANCE_LABEL,classes=DForm.STATIC)
    hashrate_label = Label("", id=DForm.HASHRATE_LABEL, classes=DForm.STATIC)
    hashrate_plot = Db4EPlot(DLabel.HASHRATE, id=DField.DB4E_PLOT)
    select_widget = Select(compact=True, id=DForm.TIMES, options=DSelect.HOURS_SELECT_LIST)


    def compose(self):

        yield Vertical(
            ScrollableContainer(
                self.intro_label,

                Vertical(
                    Horizontal(
                        Label(DLabel.INSTANCE, classes=DForm.FORM_LABEL_15),
                        self.instance_label),
                    Horizontal(
                        Label(DLabel.HASHRATE, classes=DForm.FORM_LABEL_15),
                        self.hashrate_label),
                    classes=DForm.FORM_2),                 

                Vertical(
                    self.select_widget,
                    classes=DForm.SELECT_BOX),

                Vertical(
                    self.hashrate_plot,
                    classes=DForm.PANE_BOX)),

                classes=DForm.PANE_BOX)
    
    def on_select_changed(self, event: Select.Changed) -> None:
        selected_time = event.value
        self.hashrate_plot.update_time_range(selected_time)


    def set_data(self, p2pool: P2Pool):
        INTRO = f"View analytics information for the " \
            f"[cyan]{p2pool.instance()} {DLabel.P2POOL}[/] deployment."
        
        self.intro_label.update(INTRO)
        self.instance_label.update(p2pool.instance())
        self.hashrate_label.update(p2pool.hashrate())

        data = p2pool.hashrates()
        if type(data) == dict:
            days = data[DField.DAYS]
            hashrates = data[DField.VALUES]
            units = data[DField.UNITS]
            
            self.hashrate_plot.load_data(days=days, values=hashrates, units=units)
            self.hashrate_plot.db4e_plot()
            


