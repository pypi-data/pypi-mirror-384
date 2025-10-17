#! /usr/bin/env python3

""" """
import pandas as pd


class DataSelection:
    def __init__(
        self,
        x1,
        x2,
        y1,
        y2,
        typ,
        regime,
        quality,
        wsm=True,
        path_wsm="wsm2025.csv",
        path_mean="",
        own_data="",
        upper=0,
        lower=75,
    ):
        """
        Args:
            bla (test.type): does blub
        """
        self.cols = ["LAT", "LON", "AZI", "TYPE", "DEPTH", "QUALITY", "REGIME"]
        self.type = typ
        self.regime = regime
        self.quality = quality

        self.x1, self.x2, self.y1, self.y2 = x1, x2, y1, y2

        self.plot_wsm_data = wsm
        self.path_wsm = path_wsm
        self.path_mean = path_mean
        self.own_data = own_data

        self.df_wsm = pd.DataFrame(columns=self.cols)
        self.df_mean = pd.DataFrame(columns=self.cols)
        self.df_own = pd.DataFrame(columns=self.cols)
        self.df = pd.DataFrame(columns=self.cols)

    def set_coordinates(self, x1, x2, y1, y2):
        self.x1, self.x2, self.y1, self.y2 = x1, x2, y1, y2

    def get_coordinates(self):
        return self.x1, self.x2, self.y1, self.y2

    def set_type(self, typ):
        self.type = typ

    def get_type(self):
        return self.type

    def set_regime(self, regime):
        self.regime = regime

    def get_regime(self):
        return self.regime

    def set_quality(self, quality):
        self.quality = quality

    def get_quality(self):
        return self.quality

    def set_columns(self, columns):
        self.cols = columns

    def get_columns(self):
        return self.cols

    def set_plot_wsm_data(self, boolean):
        self.plot_wsm_data = boolean

    def get_plot_wsm_data(self):
        return self.plot_wsm_data

    def set_db_wsm(self, name):
        self.db_wsm = name

    def get_db_wsm(self):
        return self.db_wsm

    def set_db_mean(self, name):
        self.db_mean = name

    def get_db_wsm(self):
        return self.db_mean

    def set_own_data(self, own_data):
        self.own_data = own_data

    def get_own_data(self):
        return self.own_data

    def read_data(self):
        if self.plot_wsm_data:
            self.df_wsm = pd.read(self.path_wsm, usecols=self.cols)
        if self.db_mean != "":
            self.df_mean = pd.read(self.path_mean, usecols=self.cols)
            self.regime.append("DIR")
            self.type.append("DIR")
            self.quality.append("DIR")

    def prepare_own_data(self):
        if len(self.own_data) > 0:
            data = []
            if "\n" in self.own_data:
                od = self.own_data.replace(" ", "")
                od = od.split("/n")
                for d in od:
                    tmp = d.split(",")
                    data.append(tmp)
            else:
                tmp = od.split("/n")
                data.append(tmp)
            self.own_data = pd.DataFrame.from_records(data, columns=self.cols)

    def get_df(self):
        self.prepare_own_data()
        self.read_data()

        df = [self.df_wsm, self.df_mean, self.df_own]
        real_df = []
        for f in df:
            if not f.empty:
                real_df.append(f)
        self.df = pd.concat(real_df)


if __name__ == "__main__":
    ds = DataSelection()
