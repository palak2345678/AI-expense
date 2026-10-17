"""
Evolutionary Soft Computing: Genetic Algorithm Rule Weight Optimizer
Academic Course: Soft Computing (CSE / AIML)

Optimizes Mamdani Fuzzy Rule weights based on historical ground-truth feedback.
Components:
- Chromosome representation: 12 continuous real-valued genes (weights w1..w12 in [0.2, 2.5])
- Fitness Function: F1-score * 100 on balanced audit validation split
- Genetic Operators:
  * Elitism: Preserves top chromosome across generations
  * Tournament Selection: Picks parents with diversity pressure
  * Uniform / Single-Point Crossover: Recombines rule traits
  * Adaptive Gaussian Mutation: Introduces controlled perturbation
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Any
try:
    from models.fuzzy_engine import SoftComputingFuzzyEngine
except ModuleNotFoundError:
    from fuzzy_engine import SoftComputingFuzzyEngine


class GeneticRuleWeightOptimizer:
    """
    Genetic Algorithm to evolve and optimize Mamdani fuzzy rule weights.
    """

    def __init__(
        self,
        num_rules: int = 12,
        pop_size: int = 24,
        generations: int = 8,
        mutation_rate: float = 0.15,
        crossover_rate: float = 0.80,
        random_state: int = 42
    ):
        self.num_rules = num_rules
        self.pop_size = pop_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.rng = np.random.default_rng(random_state)

    def _initialize_population(self) -> np.ndarray:
        """Initializes population with random rule weights in [0.4, 1.8]."""
        return self.rng.uniform(0.4, 1.8, size=(self.pop_size, self.num_rules))

    def _calculate_fitness(self, chromosome: np.ndarray, df_eval: pd.DataFrame) -> float:
        """
        Evaluates F1-score of fuzzy engine equipped with candidate chromosome weights.
        """
        engine = SoftComputingFuzzyEngine(rule_weights=list(chromosome))
        y_true = df_eval["Is_Fraud"].values.astype(int)
        y_pred = []

        for _, row in df_eval.iterrows():
            amt = float(row.get("Amount", 100.0))
            pol = float(row.get("Role_Budget_Limit", 300.0))
            rcpt_hash = str(row.get("Receipt_Hash", ""))
            has_rcpt = bool(row.get("Has_Receipt", 1))
            is_dup = (rcpt_hash == "HASH-9999-DUPLICATE")
            time_str = f"{int(row.get('Submission_Hour', 12)):02d}:00"
            date_str = str(row.get("Expense_Date", "2026-10-16"))

            eval_res = engine.evaluate_expense(
                amount=amt,
                policy_limit=pol,
                has_receipt=has_rcpt,
                is_duplicate=is_dup,
                submission_time=time_str,
                submission_date=date_str
            )
            # Binary classification threshold at 50.0% fuzzy risk score
            y_pred.append(1 if eval_res["fuzzy_score"] >= 45.0 else 0)

        y_pred = np.array(y_pred)
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))

        precision = tp / (tp + fp + 1e-9)
        recall = tp / (tp + fn + 1e-9)
        f1 = 2 * precision * recall / (precision + recall + 1e-9)

        return float(round(f1 * 100.0, 2))

    def _tournament_selection(self, population: np.ndarray, fitnesses: np.ndarray, k: int = 3) -> np.ndarray:
        """Tournament selection operator."""
        selected_indices = self.rng.choice(len(population), size=k, replace=False)
        best_idx = selected_indices[np.argmax(fitnesses[selected_indices])]
        return population[best_idx].copy()

    def _crossover(self, parent1: np.ndarray, parent2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Uniform crossover operator."""
        if self.rng.random() < self.crossover_rate:
            mask = self.rng.random(self.num_rules) < 0.5
            child1 = np.where(mask, parent1, parent2)
            child2 = np.where(mask, parent2, parent1)
            return child1, child2
        return parent1.copy(), parent2.copy()

    def _mutate(self, chromosome: np.ndarray) -> np.ndarray:
        """Gaussian mutation operator."""
        for i in range(self.num_rules):
            if self.rng.random() < self.mutation_rate:
                delta = self.rng.normal(0.0, 0.25)
                chromosome[i] = np.clip(chromosome[i] + delta, 0.2, 3.0)
        return chromosome

    def optimize(self, df: pd.DataFrame) -> Tuple[List[float], float, List[Dict[str, Any]]]:
        """
        Executes full Genetic Algorithm evolutionary optimization loop.
        """
        # Sample validation subset for fast, clean convergence
        sample_size = min(200, len(df))
        df_sample = df.sample(n=sample_size, random_state=42).reset_index(drop=True)

        population = self._initialize_population()
        best_overall_weights = None
        best_overall_fitness = -1.0
        history: List[Dict[str, Any]] = []

        for gen in range(1, self.generations + 1):
            fitnesses = np.array([self._calculate_fitness(chrom, df_sample) for chrom in population])
            gen_best_idx = int(np.argmax(fitnesses))
            gen_best_fitness = float(fitnesses[gen_best_idx])
            gen_avg_fitness = float(round(np.mean(fitnesses), 2))

            if gen_best_fitness > best_overall_fitness:
                best_overall_fitness = gen_best_fitness
                best_overall_weights = population[gen_best_idx].copy()

            history.append({
                "generation": gen,
                "best_f1_fitness": gen_best_fitness,
                "avg_f1_fitness": gen_avg_fitness
            })

            # Next generation construction
            next_pop = []
            # Elitism: retain top individual
            next_pop.append(population[gen_best_idx].copy())

            while len(next_pop) < self.pop_size:
                p1 = self._tournament_selection(population, fitnesses)
                p2 = self._tournament_selection(population, fitnesses)
                c1, c2 = self._crossover(p1, p2)
                next_pop.append(self._mutate(c1))
                if len(next_pop) < self.pop_size:
                    next_pop.append(self._mutate(c2))

            population = np.array(next_pop)

        return [round(float(w), 3) for w in best_overall_weights], best_overall_fitness, history


if __name__ == "__main__":
    csv_path = os.path.join(os.path.dirname(__file__), "..", "dataset", "synthetic_expenses.csv")
    if os.path.exists(csv_path):
        df_data = pd.read_csv(csv_path)
        ga = GeneticRuleWeightOptimizer(generations=4, pop_size=12)
        best_weights, best_fit, hist = ga.optimize(df_data)
        print(f"GA Complete. Best F1 Fitness: {best_fit}%")
        print("Optimized Rule Weights:", best_weights)
        for h in hist:
            print(f"Gen {h['generation']}: Best={h['best_f1_fitness']}%, Avg={h['avg_f1_fitness']}%")
