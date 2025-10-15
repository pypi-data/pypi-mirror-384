from mammoth_commons import testing
from mai_bias.catalogue.model_loaders.onnx_ensemble import model_onnx_ensemble
from mai_bias.catalogue.dataset_loaders.uci_csv import data_uci
from mai_bias.catalogue.metrics.multi_objective_report import multi_objective_report


def test_multiobjective_report():
    with testing.Env(model_onnx_ensemble, multi_objective_report, data_uci) as env:
        dataset_name = "credit"
        dataset = env.data_uci(dataset_name=dataset_name)
        model_path = "data/credit_mfppb.zip"
        model = env.model_onnx_ensemble(model_path)
        sensitive = ["X2", "X4", "X5"]
        html_result = env.multi_objective_report(dataset, model, sensitive=sensitive)
        html_result.show()


if __name__ == "__main__":
    test_multiobjective_report()
