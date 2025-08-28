import os

class Config:
    """
    Configuration class for the entire project.
    """

    def __init__(self):
        # =================================================================
        # Data & Feature Parameters
        # =================================================================
        # Use volumes directory for Qlib data to persist across runs.
        self.qlib_data_path = "./volumes/qlib_data/cn_data"
        self.instrument = 'csi300'

        # Overall time range for data loading from Qlib.
        self.dataset_begin_time = "2011-01-01"
        self.dataset_end_time = '2025-06-05'

        # Sliding window parameters for creating samples.
        self.lookback_window = 90  # Number of past time steps for input.
        self.predict_window = 10  # Number of future time steps for prediction.
        self.max_context = 512  # Maximum context length for the model.

        # Features to be used from the raw data.
        self.feature_list = ['open', 'high', 'low', 'close', 'vol', 'amt']
        # Time-based features to be generated.
        self.time_feature_list = ['minute', 'hour', 'weekday', 'day', 'month']

        # =================================================================
        # Dataset Splitting & Paths
        # =================================================================
        # Note: The validation/test set starts earlier than the training/validation set ends
        # to account for the `lookback_window`.
        self.train_time_range = ["2011-01-01", "2022-12-31"]
        self.val_time_range = ["2022-09-01", "2024-06-30"]
        self.test_time_range = ["2024-04-01", "2025-06-05"]
        self.backtest_time_range = ["2024-07-01", "2025-06-05"]

        # Persist processed datasets in volumes
        self.dataset_path = "./volumes/data/processed_datasets"

        # =================================================================
        # Training Hyperparameters
        # =================================================================
        self.clip = 5.0  # Clipping value for normalized data to prevent outliers.

        self.epochs = 30
        self.log_interval = 100  # Log training status every N batches.
        self.batch_size = 50  # Batch size per GPU.

        # Number of samples to draw for one "epoch" of training/validation.
        # This is useful for large datasets where a true epoch is too long.
        self.n_train_iter = 2000 * self.batch_size
        self.n_val_iter = 400 * self.batch_size

        # Learning rates for different model components.
        self.tokenizer_learning_rate = 2e-4
        self.predictor_learning_rate = 4e-5

        # Gradient accumulation to simulate a larger batch size.
        self.accumulation_steps = 1

        # AdamW optimizer parameters.
        self.adam_beta1 = 0.9
        self.adam_beta2 = 0.95
        self.adam_weight_decay = 0.1

        # Miscellaneous
        self.seed = 100  # Global random seed for reproducibility.

        # =================================================================
        # Experiment Logging & Saving
        # =================================================================
        self.use_comet = False  # Disable Comet for local CPU runs by default
        self.comet_config = {
            "api_key": os.getenv("COMET_API_KEY", ""),
            "project_name": os.getenv("COMET_PROJECT", "Kronos-Finetune-Demo"),
            "workspace": os.getenv("COMET_WORKSPACE", "")
        }
        self.comet_tag = 'finetune_demo'
        self.comet_name = 'finetune_demo'

        # Base directory for saving model checkpoints and results (persist in volumes)
        self.save_path = "./volumes/outputs/models"
        self.tokenizer_save_folder_name = 'finetune_tokenizer_demo'
        self.predictor_save_folder_name = 'finetune_predictor_demo'
        self.backtest_save_folder_name = 'finetune_backtest_demo'

        # Path for backtesting results (persist in volumes)
        self.backtest_result_path = "./volumes/outputs/backtest_results"

        # =================================================================
        # Model & Checkpoint Paths
        # =================================================================
        # Pretrained models under volumes for reuse
        self.pretrained_tokenizer_path = "./volumes/models/Kronos-Tokenizer-base"
        self.pretrained_predictor_path = "./volumes/models/Kronos-small"

        # Paths to the fine-tuned models, derived from the save_path.
        # These will be generated automatically during training.
        self.finetuned_tokenizer_path = f"{self.save_path}/{self.tokenizer_save_folder_name}/checkpoints/best_model"
        self.finetuned_predictor_path = f"{self.save_path}/{self.predictor_save_folder_name}/checkpoints/best_model"

        # =================================================================
        # Backtesting Parameters
        # =================================================================
        self.backtest_n_symbol_hold = 50  # Number of symbols to hold in the portfolio.
        self.backtest_n_symbol_drop = 5  # Number of symbols to drop from the pool.
        self.backtest_hold_thresh = 5  # Minimum holding period for a stock.
        self.inference_T = 0.6
        self.inference_top_p = 0.9
        self.inference_top_k = 0
        self.inference_sample_count = 5
        self.backtest_batch_size = 1000
        self.backtest_benchmark = self._set_benchmark(self.instrument)

    def _set_benchmark(self, instrument):
        dt_benchmark = {
            'csi800': "SH000906",
            'csi1000': "SH000852",
            'csi300': "SH000300",
        }
        if instrument in dt_benchmark:
            return dt_benchmark[instrument]
        else:
            raise ValueError(f"Benchmark not defined for instrument: {instrument}")
