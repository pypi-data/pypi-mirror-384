import time
import sys
from typing import Callable

from activegraf_python.authentication_manager.AuthenticationManager import AuthenticationManager
from activegraf_python.communication.AuthorizationRequestMessage import AuthorizationRequestMessage
from activegraf_python.communication.GrafDataChange import GrafDataChange
from activegraf_python.models.GrafData import GrafData
from activegraf_python.models.ActiveGrafData import ActiveGrafData
from activegraf_python.utils.CellDataUtils import CellDataUtils

import pandas as pd


class pandasGrafData(ActiveGrafData):
    gd_id = str
    name: str
    data_frame: pd.DataFrame
    __calculation_func: Callable
    __already_synced: bool = False

    def __init__(self, id: str, name: str, data_frame: pd.DataFrame, calculation_func: Callable = None):
        self.gd_id = id
        self.name = name
        self.data_frame = data_frame
        # this function will get called if one grafdata did change and we need to call recalculation on the dataframes, this can be passed from outside
        self.__calculation_func = calculation_func
        super().__init__()

    def _build_graf_data(self, graf_data: GrafData) -> GrafDataChange:
        graf_data.definition = self._init_graf_data_definition(self.gd_id, self.name,
                                                               series=self.data_frame.index.array.tolist(),
                                                               categories=self.data_frame.columns.array.tolist())

        graf_data.values = list()

        for columnIterator in enumerate(self.data_frame.values):
            yIndex, row = columnIterator
            for rowIterator in enumerate(row):
                xIndex, value = rowIterator
                graf_data.values.append(CellDataUtils.createFrom(
                    value, self.is_readonly(xIndex, yIndex)))

    def _ready(self):
        self._mutable_graf_data.events.on_value_changed += self.__update_data_frame
        self._mutable_graf_data.events.changes_applied += self.__calculate

    def __update_data_frame(self, x: float, y: float):
        # updating the assigned pandas dataframe, gets called on every single cell change
        self.data_frame.iat[y, x] = self._mutable_graf_data.get(y, x).value

    def __calculate(self):
        # changes_applied event gets called only once when all the changes in the batch are handled (if there are multiple), different from the previous one
        self.__already_synced = False
        try:
            self._showLoadingIndicator()
            if self.__calculation_func != None:
                self.__calculation_func()
            self.sync_with_server()
        except Exception as e:
            print(f"An exception occurred: {str(e)}", file=sys.stderr)
        finally:
            self._hideLoadingIndicator()

    def sync_with_server(self):
        if self._mutable_graf_data != None and not self.__already_synced:
            self.__already_synced = True
            self._mutable_graf_data.set_full(self.__convert())

    def __convert(self):
        result = list()
        for columnIterator in enumerate(self.data_frame.values.tolist()):
            yIndex, row = columnIterator
            newRow = list()
            for rowIterator in enumerate(row):
                xIndex, value = rowIterator
                newRow.append(CellDataUtils.createFrom(
                    value, self.is_readonly(xIndex, yIndex)))
            result.append(newRow)
        return result

    def reset_sync_flag(self):
        self.__already_synced = False

    def update_data_frame(self, df: pd.DataFrame):
        self.data_frame = df
        series_diff = df.shape[0] - \
            len(self._mutable_graf_data.graf_data.definition.series)

        if series_diff > 0:
            self._mutable_graf_data.insert_series(
                len(self._mutable_graf_data.graf_data.definition.series), series_diff)

        if series_diff < 0:
            self._mutable_graf_data.delete_series(len(
                self._mutable_graf_data.graf_data.definition.series) + series_diff, abs(series_diff))

        categories_diff = df.shape[1] - \
            len(self._mutable_graf_data.graf_data.definition.categories)

        if categories_diff > 0:
            self._mutable_graf_data.insert_categories(
                len(self._mutable_graf_data.graf_data.definition.categories), categories_diff)

        if categories_diff < 0:
            self._mutable_graf_data.delete_categories(len(
                self._mutable_graf_data.graf_data.definition.categories) + categories_diff, abs(categories_diff))

        self._mutable_graf_data.set_series(list(
            map(lambda x: CellDataUtils.createFrom(str(x.item())), self.data_frame.index.array.tolist())))
        self._mutable_graf_data.set_categories(list(map(
            lambda x: CellDataUtils.createFrom(str(x)), self.data_frame.columns.array.tolist())))
        self._mutable_graf_data.set_full(self.__convert())


def calculate_data_frames():
    # reset_sync_flag needs to get reset before calculation, so we are not sending back changes multiple times
    control_gd.reset_sync_flag()
    gd.reset_sync_flag()

    # recalculate the extra series in dataframe based on the control_data_frame and the data_frame
    data_frame = pd.DataFrame()
    size = round(control_data_frame["size"]["size"])
    for c in range(size):
        data_frame["category " + str(c)] = list(range(size))

    data_frame.index = list(range(size))

    gd.update_data_frame(data_frame)
    gd.mark_readonly(0, 0)
    gd.mark_readonly(1, 1)
    gd.mark_readonly(0, 1)
    gd.mark_readonly(1, 0)
    # call synch with server to upload all the new things in the dataframe (this is mostly for those GD-s which didnt get any calculation event from server)
    control_gd.sync_with_server()
    gd.sync_with_server()


# init pandas data_frame and setup pandasGrafData (the first parameter must be different, as its an ID which is used to find the grafData in the charts it can be any string, but preferably something guid-like)
control_data_frame = pd.DataFrame({"size": [5.0]})
control_data_frame.index = ['size']
control_gd = pandasGrafData('2', 'size control',
                            control_data_frame, calculate_data_frames)

# pandas has strict value handling, so some charts wont be able to set its value if the types are not matching, like there we have to specify those as floating numbers.
# like most of the charts are sending back floating values and not integers
# same with tablechart if we type a string into an cell which was an int before, pandas wont be able to change to string type because it differs from the whole axis type
# there might be some magic in pandas which allows loosely-typed axis, but for now we define those values as floats
data_frame = pd.DataFrame()
gd = pandasGrafData('1', "dynamic pandas", data_frame, calculate_data_frames)

# init first calculation
calculate_data_frames()

# start graf_data communication with server
control_gd.start()
gd.start()

# idle while the graf-data running
while True:
    time.sleep(1)
