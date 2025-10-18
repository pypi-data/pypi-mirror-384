import gc
import time
import warnings
import sys
import numpy as np
import os
import ast
import onnxruntime as ort
from tokenizers import Tokenizer
import uuid

# Generate a UUID
script_uuid = uuid.uuid4()

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Ensure single-threaded execution
os.environ["OMP_NUM_THREADS"] = "1"

# Start measuring process time and elapsed time
start_process_time = time.process_time()
start_time = time.time()

# Define the delimiter for splitting input lines
DELIMITER = '\t'

def load_tokenizer_from_folder(folder_name: str):
    tokenizer = Tokenizer.from_file(os.path.join(folder_name, "tokenizer.json"))
    return tokenizer

def mean_pooling(token_embeddings, attention_mask):
    attention_mask = np.expand_dims(attention_mask, axis=-1).astype(np.float32)
    pooled_embeddings = np.sum(token_embeddings * attention_mask, axis=1) / np.clip(np.sum(attention_mask, axis=1), a_min=1e-9, a_max=None)
    return pooled_embeddings

def inspect_onnx_model_inputs(onnx_session):
    input_names = [input_tensor.name for input_tensor in onnx_session.get_inputs()]
    requires_token_type_ids = "token_type_ids" in input_names

    dummy_input_ids = np.random.randint(0, 1000, (1, 512)).astype('int64')
    dummy_attention_mask = np.ones((1, 512)).astype('int64')
    onnx_inputs = {'input_ids': dummy_input_ids, 'attention_mask': dummy_attention_mask}

    if requires_token_type_ids:
        onnx_inputs['token_type_ids'] = np.zeros((1, 512)).astype('int64')

    outputs = onnx_session.run(None, onnx_inputs)
    output_shape = outputs[0].shape

    return requires_token_type_ids, len(output_shape)

# Batch size
BATCH_SIZE = 1  # Set your desired batch size here

# Get the zip file path from sys.argv
zip_file_path = sys.argv[1] if len(sys.argv) > 1 else sys.exit(0)
text_column = int(sys.argv[2])
accumulate = ast.literal_eval(sys.argv[3])

# Set a custom cache directory (if needed)
os.environ['TRANSFORMERS_CACHE'] = zip_file_path

counter = 0
tokenizer = None
onnx_session = None

requires_token_type_ids = False
requires_mean_pooling = False

# Batch storage
input_batch = []

def process_batch(input_batch, tokenizer, onnx_session, requires_token_type_ids, requires_mean_pooling, zip_file_path):
    """
    Process the current batch, tokenize and pad, run the ONNX model, and print the embeddings.
    """
    # Start measuring process time and elapsed time for this batch
    start_process_time_batch = time.process_time()
    start_time_batch = time.time()

    encoded_inputs = [tokenizer.encode(input_data[text_column]) for input_data in input_batch]
    max_length = 512

    input_ids_batch = np.array([np.pad(e.ids, (0, max_length - len(e.ids)), mode='constant') for e in encoded_inputs], dtype=np.int64)
    attention_mask_batch = np.array([[1] * len(e.ids) + [0] * (max_length - len(e.ids)) for e in encoded_inputs], dtype=np.int64)

    if requires_token_type_ids:
        # Token type ids should have the same shape as input_ids and attention_mask
        token_type_ids_batch = np.array([[0] * len(e.ids) + [0] * (max_length - len(e.ids)) for e in encoded_inputs], dtype=np.int64)
    else:
        token_type_ids_batch = None  # No need to process this if not required


    onnx_inputs = {
        "input_ids": input_ids_batch,
        "attention_mask": attention_mask_batch
    }
    if requires_token_type_ids:
        onnx_inputs["token_type_ids"] = token_type_ids_batch

    # Run the model
    outputs = onnx_session.run(None, onnx_inputs)

    if requires_mean_pooling:
        embeddings_batch = mean_pooling(outputs[0], attention_mask_batch)
    else:
        embeddings_batch = outputs[0]

    # Measure time taken for this batch
    process_time_used = time.process_time() - start_process_time_batch
    elapsed_time = time.time() - start_time_batch

    # Process and print each result in the batch
    for i, embeddings in enumerate(embeddings_batch):
        input_data = input_batch[i]
        for idx, item in enumerate(embeddings):
            list_2_print = [input_data[c] for c in accumulate] + [str(script_uuid), str(process_time_used/len(input_batch)), str(elapsed_time/len(input_batch)), input_data[1], str(idx), str(item), zip_file_path]
            print(DELIMITER.join(list_2_print))



while True:
    try:
        line = input()
        if line == '':
            onnx_session = None
            gc.collect()
            break

        input_data = line.split(DELIMITER)
        input_batch.append(input_data)

        # Process the batch once it's full
        if len(input_batch) == BATCH_SIZE:
            if counter == 0:
                options = ort.SessionOptions()
                options.intra_op_num_threads = 1
                providers = ['CPUExecutionProvider']

                with open(os.path.join(zip_file_path, "full_model.onnx"), "rb") as f:
                    model_bytes = f.read()
                onnx_session = ort.InferenceSession(model_bytes, sess_options=options, providers=providers)

                tokenizer = load_tokenizer_from_folder(zip_file_path)
                requires_token_type_ids, output_rank = inspect_onnx_model_inputs(onnx_session)
                requires_mean_pooling = output_rank == 3

                gc.collect()
                counter = 1

            process_batch(input_batch, tokenizer, onnx_session, requires_token_type_ids, requires_mean_pooling, zip_file_path)
            input_batch = []  # Clear the batch after processing

            gc.collect()

    except EOFError:
        # Process any remaining batch that didn't reach BATCH_SIZE
        if input_batch:
            process_batch(input_batch, tokenizer, onnx_session, requires_token_type_ids, requires_mean_pooling, zip_file_path)
        gc.collect()
        break
