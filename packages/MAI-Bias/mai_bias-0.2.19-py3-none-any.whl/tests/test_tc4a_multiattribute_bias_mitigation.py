from mammoth_commons import testing
from mai_bias.catalogue.model_loaders.onnx_ensemble import model_onnx_ensemble
from mai_bias.catalogue.dataset_loaders.uci_csv import data_uci
from mai_bias.catalogue.metrics.model_card import model_card


def test_multiattribute_bias_mitigation():
    with testing.Env(model_onnx_ensemble, data_uci, model_card) as env:
        dataset_name = "credit"
        dataset = env.data_uci(dataset_name=dataset_name)
        model_path = "data/credit_mfppb.zip"
        model = env.model_onnx_ensemble(model_path)
        sensitive = ["X2", "X4", "X5"]
        markdown_result = env.model_card(dataset, model, sensitive=sensitive)
        markdown_result.show()


if __name__ == "__main__":
    test_multiattribute_bias_mitigation()
