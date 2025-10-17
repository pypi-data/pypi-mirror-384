# file for tracking known "styles" of wine - for classification purposes
# important to note: this file is used to convert "style" into "grape", "region" or "sweetness"

# import re
# from collections import namedtuple
# from ..pygrape import grapes,


# WineStyle = namedtuple("WineStyle", ["grapes", "regions", "sweetness", "color"])


# mapping = {
#     "vin santo": {
#         regex: r"vin santo",
#         styles: [
#             WineStyle(grapes=["Malvasia"], regions=[regions.TUSCANY]),
#             WineStyle(grapes=["Trebbiano"], regions=[regions.TUSCANY]),
#         ]
#     },
#     "occhio di pernice": {
#         regex: r"occhio di pernice",
#         styles: [
#             WineStyle(grapes=["Sangiovese"], regions=[regions.TUSCANY]),
#         ]
#     },
#     "manzanilla": {
#         regex: r"(?:fino|manzanilla|fino sherry|sherry fino)",
#         styles: [
#             WineStyle(grapes=["Palomino"], regions=[regions.ANDALUSIA]),
#             WineStyle(grapes=["Pedro Ximenez"], regions=[regions.ANDALUSIA]),
#             WineStyle(grapes=["Moscatel de Grano Menudo"], regions=[regions.ANDALUSIA]),
#             WineStyle(grapes=["Moscatel de Alejandría"], regions=[regions.ANDALUSIA]),
#         ]
#     },
# }
