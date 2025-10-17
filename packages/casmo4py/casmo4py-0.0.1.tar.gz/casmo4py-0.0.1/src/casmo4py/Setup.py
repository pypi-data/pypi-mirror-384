#! /usr/bin/env python3

""" """


class Setup:
    def __init__(self):
        """
        Args:
            bla (test.type): does blub
        """

        print("hello setup")

        self.path_input = "/home/tim/casmo_ap/gmt_files_casmo/"
        self.path_output = "/home/tim/casmo_ap/static/output/"
        self.path_plate_boundary = self.path_input + "BIRD_plate_boundaries.dat"

        self.colors = {
            "lake": "22/135/183",
            "river": "22/135/183",
            "borders": "160/32/240",
            "plate_boundaries": "100/100/100",
            "NF": "255/0/0",
            "TF": "blue",
            "SS": "green",
            "U": "black",
            "DIR": "50/50/50",
        }
        self.pen = {}

        self.vec_len_qual = {
            "A": 0.7,
            "B": 0.55,
            "C": 0.4,
            "D": 0.3,
            "E": 0.2,
            "DIR": 0.25,
        }

    def set_input_path(self, path):
        self.path_input = path

    def get_input_path(self):
        return self.path_input

    def set_output_path(self, path):
        self.path_output = path

    def get_output_path(self):
        return self.path_output

    def set_plate_bound_path(self, path):
        self.path_plate_boundary = path

    def get_plate_bound_path(self):
        return self.path_plate_boundary

    def set_colors(self, key, col):
        if key in self.colors.keys():
            self.colors[key] = col
        else:
            print("No such item")

    def get_colors(self):
        return self.colors

    def set_colors(self, key, len):
        if key in self.vec_len_qual.keys():
            self.vec_len_qual[key] = len
        else:
            print("No such item")

    def get_colors(self):
        return self.vec_len_qual


if __name__ == "__main__":
    s = Setup()
    print(s.get_colors())

    s.set_colors("lake", "blue")

    print(s.get_colors())
