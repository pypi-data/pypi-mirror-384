from .retro_star.common.prepare_utils import RSPlanner
import torch
import numpy as np
import sys

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources   # pip install importlib_resources


class RetroScoreArgs:
    def __init__(self, cost_weight=0.1, filter_ratio=0.9, coef=0.3, print_interval=50):
        self.mode = "sure_param"
        self.cost_weight = cost_weight
        self.filter_ratio = filter_ratio
        self.coef = coef
        self.print_interval = print_interval


class RetroPlanner:
    def __init__(self, expansion_topk: int = 10, iterations: int = 500, max_routes: int = 10):
        stock_abs_path = resources.files("RetroScore").joinpath("data/multi_step/retro_data/dataset/origin_dict.csv")
        one_step_model = resources.files("RetroScore").joinpath("experiments/uspto_full/epoch_65.pt")
        value_model = resources.files("RetroScore").joinpath("data/multi_step/retro_data/saved_models/best_epoch_final_4.pt")
        self.planner = RSPlanner(
            device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'),
            expansion_topk=expansion_topk,
            iterations=iterations,
            starting_molecules=stock_abs_path,
            model_dump=one_step_model,
            value_model=value_model,
            fp_dim=2048,
            max_routes_num=max_routes)

    def run_plan(self, mol: str, args: None or RetroScoreArgs = None):
        if args is None:
            args = RetroScoreArgs()

        succ_num, result = self.planner.plan(mol, args, need_action=False)
        return succ_num, result


class RetroScore:
    def __init__(self, w: float = 0.25, n: int = 10):
        self.w = w   # RNS weight
        self.n = n   # max route num
        self.planner = RetroPlanner(max_routes=n)

    def compute_score(self, r_num, r_len):
        if r_num == -1:    # target in stock
            return np.float64(9)
        elif r_num == 0:
            return np.float64(0)
        else:
            rns = np.clip(r_num, 0, self.n) / self.n
            r_len = np.clip(r_len, 1, 100)
            rls = 1 - np.log10(r_len)
            score = self.w * rns + (1 - self.w) * rls
            score = np.clip(score, 0, 1) * 9
            return score

    def calculate_score(self, mol: str):
        r_num, result = self.planner.run_plan(mol)
        r_len = result["multi_stage_best_length"]
        score = self.compute_score(r_num, r_len)
        return score






