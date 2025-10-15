# https://github.com/SamLau95/pandas_tutor/issues/86
# adapted from Thinking in Pandas
import pandas as pd

restaurants = pd.MultiIndex.from_tuples(
    (("Diner", (4, 2)), ("Pandas", (5, 4))),
    names=["restaurant", "location"],
)
inspections = pd.MultiIndex.from_tuples(
    ((0, "score"), (0, "date"), (1, "score"), (1, "date")),
    names=["inspection", None],
)

restaurant_inspections = pd.DataFrame(
    [[90, "02/18", 100, "05/18"], [55, "04/18", 76, "01/18"]],
    index=restaurants,
    columns=inspections,
)

(restaurant_inspections
 .stack(future_stack=True)
 .stack(future_stack=True)
 .unstack()
 .unstack()
 .unstack()
 .unstack()
)
