"""Load registered RecBole checkpoints and reproduce their exact split."""

import hashlib
import sys
from pathlib import Path

import torch


def _fingerprint(values):
    return hashlib.sha256("\0".join(map(str, values)).encode()).hexdigest()


def _split_fingerprint(dataset):
    pairs = sorted(zip(dataset.inter_feat[dataset.uid_field].tolist(),
                       dataset.inter_feat[dataset.iid_field].tolist()))
    return _fingerprint(f"{u}:{i}" for u, i in pairs)


class CheckpointAdapter:
    def __init__(self, path, recbole_root, dataset_root, expected_model,
                 recbole_debias_root=None):
        recbole_root = Path(recbole_root).resolve()
        if str(recbole_root) not in sys.path:
            sys.path.insert(0, str(recbole_root))
        backend = "recbole_debias" if expected_model == "MF" else "recbole"
        if backend == "recbole_debias":
            if not recbole_debias_root:
                raise ValueError("MF requires --recbole-debias-root")
            debias = Path(recbole_debias_root).resolve()
            if str(debias) not in sys.path:
                sys.path.insert(0, str(debias))
            from recbole_debias.data import create_dataset, data_preparation
            from recbole_debias.utils import get_model
        else:
            from recbole.data import create_dataset, data_preparation
            from recbole.utils import get_model
        from recbole.utils import init_seed
        from recbole.utils.case_study import full_sort_scores

        try:
            saved = torch.load(str(Path(path).resolve()), map_location="cpu", weights_only=False)
        except TypeError:
            saved = torch.load(str(Path(path).resolve()), map_location="cpu")
        config = saved["config"]
        if config["model"] != expected_model or config["eval_args"]["order"] != "RO":
            raise ValueError("Checkpoint model or split protocol differs from registry")
        config["data_path"] = str(Path(dataset_root).resolve() / config["dataset"])
        config["device"] = torch.device("cpu")
        config["use_gpu"] = False
        init_seed(config["seed"], config["reproducibility"])
        dataset = create_dataset(config)
        train, valid, test = data_preparation(config, dataset)
        init_seed(config["seed"], config["reproducibility"])
        model = get_model(expected_model)(config, train._dataset).to("cpu")
        model.load_state_dict(saved["state_dict"], strict=True)
        model.load_other_parameter(saved.get("other_parameter"))
        model.eval()
        self.path, self.config, self.dataset = Path(path).resolve(), config, dataset
        self.train, self.valid, self.test, self.model = train, valid, test, model
        self._full_sort_scores = full_sort_scores
        uid, iid = config["USER_ID_FIELD"], config["ITEM_ID_FIELD"]
        self.mapping_hash = {"users": _fingerprint(dataset.field2id_token[uid]),
                             "items": _fingerprint(dataset.field2id_token[iid])}
        self.split_hash = {name: _split_fingerprint(loader._dataset) for name, loader in
                           (("train", train), ("valid", valid), ("test", test))}
        self.train_seen = self._items_by_user(train._dataset)
        self.test_items = self._items_by_user(test._dataset)

    @staticmethod
    def _items_by_user(dataset):
        result = {}
        for user, item in zip(dataset.inter_feat[dataset.uid_field].tolist(),
                              dataset.inter_feat[dataset.iid_field].tolist()):
            result.setdefault(int(user), set()).add(int(item))
        return result

    def candidates(self, users, size):
        result = {}
        for start in range(0, len(users), 16):
            batch = list(users[start:start + 16])
            scores = self._full_sort_scores(batch, self.model, self.test,
                                            torch.device("cpu"))
            for row, user in enumerate(batch):
                values = scores[row].tolist()
                eligible = [i for i, score in enumerate(values) if score != float("-inf")]
                items = sorted(eligible, key=lambda i: (-values[i], i))[:size]
                result[user] = {"item_ids": items,
                                "scores": [float(values[i]) for i in items]}
        return result
