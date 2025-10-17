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
        self.upper, self.lower = upper, lower

        self.plot_wsm_data = wsm
        self.path_wsm = path_wsm
        self.path_mean = path_mean
        self.own_data = own_data

        self.df_wsm = pd.DataFrame(columns=self.cols)
        self.df_mean = pd.DataFrame(columns=self.cols)
        self.df_own = pd.DataFrame(columns=self.cols)
        # self.df = pd.DataFrame(columns=self.cols)

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

    def set_path_wsm(self, name):
        self.path_wsm = name

    def get_path_wsm(self):
        return self.path_wsm

    def get_df_wsm(self):
        return self.df_wsm

    def set_path_mean(self, name):
        self.path_mean = name

    def get_path_mean(self):
        return self.path_mean

    def get_df_mean(self):
        return self.df_mean

    def set_own_data(self, own_data):
        self.own_data = own_data

    def get_own_data(self):
        return self.own_data

    def get_df_own(self):
        return self.df_own

    def read_data(self):
        if self.plot_wsm_data:
            self.df_wsm = pd.read_csv(self.path_wsm, usecols=self.cols)
        if self.path_mean != "":
            self.df_mean = pd.read_csv(self.path_mean, usecols=self.cols)
            self.regime.append("DIR")
            self.type.append("DIR")
            self.quality.append("DIR")

    def prepare_own_data(self):
        if len(self.own_data) > 0:
            data = []
            if "\n" in self.own_data:
                od = self.own_data.replace(" ", "")
                od = od.split("\n")
                for d in od:
                    tmp = d.split(",")
                    data.append(tmp)
            else:
                tmp = od.split("\n")
                data.append(tmp)
            self.df_own = pd.DataFrame.from_records(data, columns=self.cols)

    def crop_data(self):
        self.df = self.df.astype(
            {"LAT": "float64", "LON": "float64", "DEPTH": "float64"}
        )
        self.df = self.df[
            (self.df.LON >= self.x1)
            & (self.df.LON <= self.x2)
            & (self.df.LAT >= self.y1)
            & (self.df.LAT <= self.y2)
            & (self.df.DEPTH >= self.upper)
            & (self.df.DEPTH <= self.lower)
        ]
        self.df = self.df[
            (self.df.REGIME.isin(self.regime))
            & (self.df.TYPE.isin(self.type))
            & (self.df.QUALITY.isin(self.quality))
        ]

    def get_df(self):
        self.read_data()
        self.prepare_own_data()

        df = [self.df_wsm, self.df_mean, self.df_own]
        real_df = []
        for f in df:
            if not f.empty:
                real_df.append(f)
        self.df = pd.concat(real_df)
        self.crop_data()
        return self.df


if __name__ == "__main__":
    typ = ["GI", "OC"]
    quality = ["A", "B", "C"]
    regime = ["NF"]

    x1 = 17
    x2 = 19.5
    y1 = 59
    y2 = 62

    ds = DataSelection(x1, x2, y1, y2, typ, regime, quality)

    print(ds.get_coordinates())
    ds.set_path_wsm("~/casmo/data/wsm2025.csv")
    df = ds.get_df()
    print(df.head())
    print(df.info())
    own_data = """61.376, 18.171, 138, HF, 0.32, A, TF
59.376, 18.171, 138, GI, 0.32, B, NF
60.376, 17.171, 138, OC, 0.32, C, SS
61.376, 19.171, 138, OC, 0.32, D, TF"""

    ds.set_own_data(own_data)
    print(ds.get_own_data())

    ds.prepare_own_data()
    print(ds.get_df_own())

    ds.set_path_mean("~/casmo/data/mean_SHmax_r250_02.csv")

    df = ds.get_df()
    print(df.head())
    print(df.info())
