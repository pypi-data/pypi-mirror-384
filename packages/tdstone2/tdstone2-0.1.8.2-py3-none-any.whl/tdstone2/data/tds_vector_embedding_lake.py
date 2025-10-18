import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

import time
import warnings
import sys
import csv
import torch
from torch.utils.data import Dataset, DataLoader
from sentence_transformers import SentenceTransformer
import uuid
import ast
import os
from collections import OrderedDict

warnings.warn("Beginning of the script.", UserWarning)

# Define the path to your preloaded models directory
models_directory = os.path.abspath("./models")
os.environ["TRANSFORMERS_CACHE"] = models_directory
os.environ["HF_HOME"] = models_directory
os.environ["TF_ENABLE_ONEDNN_OPTS"] = '0'

# Start measuring process and elapsed time
start_process_time = time.process_time()
start_time = time.time()


# Define the delimiter for splitting input lines
DELIMITER = ','

# Get parameters from sys.argv
model_name  = sys.argv[1] if len(sys.argv) > 1 else sys.exit("Please provide the model name")
batch_size  = int(sys.argv[2])  # the batch size
text_column = int(sys.argv[3])  # Convert the second argument to an integer (text_column)
try:
    accumulate    = ast.literal_eval(sys.argv[4].replace('-',',')) # Convert the third argument (accumulate) from string to list
except Exception as e:
    sys.exit()
DELIMITER   = sys.argv[5] if len(sys.argv[5])==1 else ast.literal_eval(sys.argv[5])
device      = sys.argv[6] # will take 'cuda' of 'cpu'
half        = int(sys.argv[7]) # if 1 then the model will run half precision


colNames = ['text_column'] + [f'accumulate_{idx}' for idx in range(len(accumulate))]
# Generate a unique identifier for this script instance
script_uuid = uuid.uuid4()

def restore_model_name(model_fname: str) -> str:
    if model_fname.startswith("models--"):
        model_name = model_fname[len("models--"):].replace("--", "/")
        return model_name
    else:
        return model_name

# Load SentenceTransformer model and move to CUDA if available
if device == 'cuda':
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
else:
    device = 'cpu'

# Update the model loading to handle local paths
model_path = os.path.join(models_directory, model_name, model_name)
sentence_transformer = SentenceTransformer(model_path).to(device)

if half == 1 and device == 'cuda':
    sentence_transformer = sentence_transformer.half()
else:
    half = 0

sentence_transformer.eval()

class StdinDataset(Dataset):
    def __init__(self, transform=None):
        self.transform = transform
        self.csv_reader = csv.DictReader(
            sys.stdin,
            fieldnames= colNames,
            delimiter = DELIMITER
        )
        self.eof_reached = False  # Initialize EOF flag

    def __len__(self):
        return 10**9  # Large number simulating indefinite streaming

    def parse_row(self, row):
        try:
            warnings.warn(f"row : {list(row.keys())}", UserWarning)
            text_data = row['text_column']
            additional_data = [row[f'accumulate_{idx}'] for idx in range(len(accumulate))]
            return text_data, additional_data
        except IndexError:
            sys.exit()

    def __getitem__(self, idx):
        if self.eof_reached:
            return [], [], True  # Return empty lists and EOF flag

        while not self.eof_reached:
            try:
                row = next(self.csv_reader)
                sample = self.parse_row(row)
                if sample is not None:
                    text_data, additional_data = sample
                    return additional_data, text_data, False
            except StopIteration:
                self.eof_reached = True
                return [], [], True

# Custom collate function to handle empty (EOF) items
def collate_fn(batch):
    # Filter out empty entries (EOF signals)
    batch = [item for item in batch if item[1] != []]
    if len(batch) == 0:
        return [], [], True  # Return EOF-only batch if nothing valid remains

    additional_data, text_data, eof_status = zip(*batch)
    return additional_data, text_data, any(eof_status)

def create_stdin_dataloader(batch_size=1):
    dataset = StdinDataset()
    return DataLoader(dataset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

def vect2dict(embedding_vector):
    #return str(OrderedDict((f"V{i}", value) for i, value in enumerate(embedding_vector))).replace("'", '"')
    return f"{len(embedding_vector)}{DELIMITER}{' '.join([str(v) for v in embedding_vector])}"


batch_no = 1
def optimized_output_flattened():
    # Prepare the base output data (constant part for all embeddings)
    base_output_data = (
        f"{script_uuid}{DELIMITER}"
        f"{process_time_used / len(embeddings)}{DELIMITER}"
        f"{elapsed_time / len(embeddings)}{DELIMITER}"
        f"{model_name}{DELIMITER}"
        f"{device}{DELIMITER}"
        f"{half}{DELIMITER}"
        f"{batch_size}{DELIMITER}"
        f"{batch_no}"
    )

    output_buffer = [
        f"{DELIMITER.join(map(str, additional_data[i]))}{DELIMITER}{base_output_data}{DELIMITER}{vect2dict(embedding_vector)}"
        for i, embedding_vector in enumerate(embeddings)
    ]
    # Write all output at once to stdout
    sys.stdout.write("\n".join(output_buffer) + "\n")

warnings.warn("Before create_stdin_dataloader.", UserWarning)
dataloader = create_stdin_dataloader(batch_size=batch_size)
warnings.warn("create_stdin_dataloader successful.", UserWarning)
try:
    warnings.warn("before the for loop.", UserWarning)

    for additional_data, text_data, eof_status in dataloader:
        if len(text_data) == 0 or len(text_data[0]) == 0:
            sys.exit()

        # Perform batch encoding
        with torch.no_grad():
            embeddings = sentence_transformer.encode(text_data, convert_to_tensor=True, device=device).cpu().numpy()

        # Calculate process and elapsed time
        process_time_used = time.process_time() - start_process_time
        elapsed_time      = time.time() - start_time

        optimized_output_flattened()
        batch_no = batch_no + 1
        start_process_time = time.process_time()
        start_time = time.time()

        if eof_status:
            sys.exit()  # Exit if EOF reached

except SystemExit:
    pass
except Exception as e:
    print("Script Failure :", sys.exc_info()[0], file=sys.stderr)
    raise
    sys.exit()