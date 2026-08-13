from evaluation_schema import IELTSScore

score = IELTSScore(
    fluency=7.0,
    lexical=7.5,
    grammar=6.5,
    pronunciation=7.0
)

print(
    "Overall:",
    score.overall()
)
