import numpy as np

X_train = np.loadtxt(
    "../data/train_data.csv", dtype=np.float64, delimiter=",", comments="#"
)
print("Input dataset shape: ", X_train.shape)

y_train = X_train[:, 0]
print(y_train)

X_train = X_train[:, 1:]
print(X_train)

from snapml import RandomForestClassifier

clf = RandomForestClassifier(random_state=42)
print(clf.get_params())

clf.fit(X_train, y_train)
preds = clf.predict(X_train)

from sklearn.metrics import accuracy_score

print("Accuracy score ", accuracy_score(y_train, preds))

clf.export_model("rf_model.pmml")

from xgboost import XGBClassifier
from sklearn2pmml.pipeline import PMMLPipeline
from sklearn2pmml import sklearn2pmml

model = XGBClassifier(random_state=42, colsample_bytree=0.5)
model.fit(X_train, y_train)

print(model.feature_importances_)

model.get_booster().save_model("xgb_model.json")
preds = model.predict(X_train)
print("Accuracy score ", accuracy_score(y_train, preds))

pipeline = PMMLPipeline([("estimator", model)])

sklearn2pmml(pipeline, "xgb_model.pmml", with_repr=True)

from snapml import BoostingMachineClassifier

snapml_model = BoostingMachineClassifier()
snapml_model.import_model("xgb_model.json", "xgb_json")

preds = snapml_model.predict(X_train)
print(preds)
preds[preds < 0] = 0
preds[preds > 0] = 1
print("Accuracy score ", accuracy_score(y_train, preds))
