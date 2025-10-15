# import lightgbm
#
#
# class LGBRModel:
#     internal_model = lightgbm.LGBMRegressor
#     mm_columns = None
#
#     def __init__(self, params):
#         self.model_params = params
#         self._model = self.internal_model(**self.model_params)
#
#     def fit(self, mm, targets, *args, **kwargs):
#         if kwargs.get("early_stopping_rounds"):
#             kwargs["eval_set"] = [
#                 (
#                     kwargs["early_stopping_data"]["mm"].values,
#                     kwargs["early_stopping_data"]["targets"],
#                 )
#             ]
#             kwargs.pop("early_stopping_data")
#         self.mm_columns = mm.columns
#         self._model.fit(mm.values, targets, *args, **kwargs)
#
#     def predict(self, mm, *args, **kwargs):
#         mm = mm[self.mm_columns]
#         predictions = self._model.predict(mm.values, *args, **kwargs)
#         return predictions
