import time
# Start measuring process time and elapsed time
start_process_time = time.process_time()
start_time = time.time()

import warnings
import sys
import numpy as np
import os
import ast
import json


import onnxruntime as ort
from tokenizers import Tokenizer  # Replace AutoTokenizer with Tokenizer from the tokenizers package

import uuid
from collections import OrderedDict

# Generate a UUID
script_uuid = uuid.uuid4()

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Ensure single-threaded execution
os.environ["OMP_NUM_THREADS"] = "1"

# Define the delimiter for splitting input lines
DELIMITER = '\t'

import sentencepiece as spm       # For spiece.model

def load_tokenizer_from_folder(folder_name: str):
    """
    Load the tokenizer from the specified folder.
    If 'sentencepiece.bpe.model' is present, use it.
    Otherwise, fall back to 'spiece.model' or 'tokenizer.json'.

    Args:
        folder_name (str): The folder where the tokenizer is saved.

    Returns:
        tokenizer: The loaded tokenizer instance (SentencePieceProcessor or Tokenizer).
    """
    sp_bpe_path = os.path.join(folder_name, "sentencepiece.bpe.model")
    sp_path = os.path.join(folder_name, "spiece.model")
    tokenizer_json_path = os.path.join(folder_name, "tokenizer.json")

    if os.path.exists(sp_bpe_path):
        from sentencepiece import SentencePieceProcessor
        sp = SentencePieceProcessor()
        sp.load(sp_bpe_path)
        #print("Loaded tokenizer from sentencepiece.bpe.model")
        return sp, False
    elif os.path.exists(sp_path):
        from sentencepiece import SentencePieceProcessor
        sp = SentencePieceProcessor()
        sp.load(sp_path)
        #print("Loaded tokenizer from spiece.model")
        return sp, False
    elif os.path.exists(tokenizer_json_path):
        from tokenizers import Tokenizer
        tokenizer = Tokenizer.from_file(tokenizer_json_path)
        #print("Loaded tokenizer from tokenizer.json")
        return tokenizer, True
    else:
        raise FileNotFoundError("No suitable tokenizer model found in the folder.")

def mean_pooling(token_embeddings, attention_mask):
    """
    Perform mean pooling on token embeddings, taking the attention mask into account.
    Args:
        token_embeddings: The embeddings for each token in the sentence.
        attention_mask: The attention mask (to exclude padding tokens from pooling).
    Returns:
        sentence_embeddings: The pooled sentence embeddings.
    """
    # Expand attention mask dimensions for proper broadcasting (similar to unsqueeze in PyTorch)
    attention_mask = np.expand_dims(attention_mask, axis=-1).astype(np.float32)

    # Perform mean pooling (sum of token embeddings divided by the sum of attention mask)
    pooled_embeddings = np.sum(token_embeddings * attention_mask, axis=1) / np.clip(np.sum(attention_mask, axis=1),
                                                                                    a_min=1e-9, a_max=None)
    return pooled_embeddings

def vect2dict(embedding_vector):
    return json.dumps(OrderedDict((f"V{i}", float(value)) for i, value in enumerate(embedding_vector)))
    #return f"{len(embedding_vector)}{DELIMITER}{' '.join([str(v) for v in embedding_vector])}"

def inspect_onnx_model_inputs(onnx_session):
    """
    Inspect the ONNX model to check if 'token_type_ids' are required and determine the input sequence length.
    Args:
        onnx_session: The ONNX Runtime session.
    Returns:
        bool: Whether 'token_type_ids' are required.
        int: The max sequence length (or None if not specified).
        int: The rank (number of dimensions) of the model output.
    """
    # Get model input details
    input_names = [input_tensor.name for input_tensor in onnx_session.get_inputs()]

    # Check if 'token_type_ids' is one of the required inputs
    requires_token_type_ids = "token_type_ids" in input_names

    # Inspect the input shape of 'input_ids' to get the max sequence length
    input_ids_info = onnx_session.get_inputs()[input_names.index('input_ids')]
    input_shape = input_ids_info.shape  # Example shape could be [batch_size, sequence_length]

    # The max sequence length is typically the second dimension of 'input_ids'
    max_sequence_length = input_shape[1] if len(input_shape) > 1 else None

    # Run the model with dummy inputs to check the output shape
    dummy_input_ids = np.random.randint(0, 1000, (1, max_sequence_length)).astype(
        'int64')  # Use the determined max sequence length
    dummy_attention_mask = np.ones((1, max_sequence_length)).astype('int64')

    # Prepare dummy input for model inference
    onnx_inputs = {
        'input_ids': dummy_input_ids,
        'attention_mask': dummy_attention_mask
    }

    if requires_token_type_ids:
        onnx_inputs['token_type_ids'] = np.zeros((1, max_sequence_length)).astype(
            'int64')  # Dummy token_type_ids if needed

    # Run the model to inspect the output shape
    outputs = onnx_session.run(None, onnx_inputs)
    output_shape = outputs[0].shape  # Check the shape of the output

    # Return whether 'token_type_ids' is required, the max sequence length, and the output shape's rank
    return requires_token_type_ids, max_sequence_length, len(output_shape)



# Get the zip file path from sys.argv
zip_file_path = sys.argv[1] if len(sys.argv) > 1 else sys.exit(0)
text_column   = int(sys.argv[2])  # Convert the first argument to an integer (text_column)
try:
    accumulate    = ast.literal_eval(sys.argv[3].replace('-',',')) # Convert the third argument (accumulate) from string to list
except Exception as e:
    sys.exit()

# Set a custom cache directory (if needed)
os.environ['TRANSFORMERS_CACHE'] = zip_file_path


# Load the data and print the output on the fly
counter = 0
#tokenizer = None  # Initialize as None to avoid errors if not instantiated
onnx_session = None  # Initialize as None to avoid errors if not instantiated

requires_token_type_ids = False
requires_mean_pooling = False

tokenizer, is_Tokenizer = load_tokenizer_from_folder(zip_file_path)

while True:
    try:
        # Read the input line
        line = input()

        if line is None or line.strip() == '':
            break  # Properly handle end of input or empty lines

        if line == '':
            # Clear the session and force garbage collection
            onnx_session = None
            break  # End the loop if there's an empty input

        if counter == 0:
            # Create an ONNX Runtime session with memory optimization
            options = ort.SessionOptions()
            options.intra_op_num_threads = 1  # Limit parallelism to save memory
            providers = ['CPUExecutionProvider']

            # Create an InferenceSession with the model bytes
            with open(os.path.join(zip_file_path, "full_model.onnx"), "rb") as f:
                model_bytes = f.read()
            onnx_session = ort.InferenceSession(model_bytes, sess_options=options, providers=providers)

            # Inspect the ONNX model to determine required inputs and output shape
            requires_token_type_ids, max_sequence_length, output_rank = inspect_onnx_model_inputs(onnx_session)

            # If the output is token-level (3D), mean pooling is required
            requires_mean_pooling = output_rank == 3

            # Set counter to indicate that models are loaded
            counter = 1

        # Split input line using the defined delimiter
        input_data = line.split(DELIMITER)

        # Tokenize the line using the tokenizers library (returns list of IDs) 
        if is_Tokenizer:
            encoded_input = tokenizer.encode(input_data[text_column])
        else:    
            encoded_input = tokenizer.Encode(input_data[text_column])

        # Convert tokenized data into numpy arrays
        if type(encoded_input) == list:
            input_ids = np.array([encoded_input], dtype=np.int64)
            attention_mask = np.array([[1] * len(encoded_input)], dtype=np.int64)  # Create attention mask
            token_type_ids = np.array([[0] * len(encoded_input)],
                                    dtype=np.int64)  # Create token_type_ids, all zeros for single sequences
        else:
            input_ids = np.array([encoded_input.ids], dtype=np.int64)
            attention_mask = np.array([[1] * len(encoded_input.ids)], dtype=np.int64)  # Create attention mask
            token_type_ids = np.array([[0] * len(encoded_input.ids)],
                                    dtype=np.int64)  # Create token_type_ids, all zeros for single sequences

    
        # Pad input_ids, attention_mask, and token_type_ids to max_length=512
        max_length = max_sequence_length
        nb_tokens  = input_ids.shape[1]
        if input_ids.shape[1] > max_length:
            input_ids      = input_ids[:, :max_length]  # Truncate to max_length
            attention_mask = attention_mask[:, :max_length]  # Truncate to max_length
            token_type_ids = token_type_ids[:, :max_length]  # Truncate to max_length

        input_ids_padded = np.pad(input_ids, ((0, 0), (0, max_length - input_ids.shape[1])), mode='constant',
                                constant_values=0)
        attention_mask_padded = np.pad(attention_mask, ((0, 0), (0, max_length - attention_mask.shape[1])),
                                    mode='constant', constant_values=0)
        token_type_ids_padded = np.pad(token_type_ids, ((0, 0), (0, max_length - token_type_ids.shape[1])),
                                    mode='constant', constant_values=0)

        # Prepare the inputs dictionary for ONNX Runtime with correct dimensions
        onnx_inputs = {
            "input_ids": input_ids_padded,  # 2D tensor with padding
            "attention_mask": attention_mask_padded,  # 2D tensor with padding
        }
        if requires_token_type_ids:
            onnx_inputs["token_type_ids"] = token_type_ids_padded

        # Run the ONNX model session
        outputs = onnx_session.run(None, onnx_inputs)

        # Check if mean pooling is required (if output is token-level embeddings)
        if requires_mean_pooling:
            #embeddings = mean_pooling(outputs[0], inputs["attention_mask"])
            embeddings = mean_pooling(outputs[0], attention_mask_padded)
        else:
            embeddings = outputs[0]

        # Measure time taken up to this point
        process_time_used = time.process_time() - start_process_time
        elapsed_time = time.time() - start_time

        # Start measuring process time and elapsed time
        start_process_time = time.process_time()
        start_time = time.time()

        # Print the output embeddings along with input data
        list_2_print = [str(input_data[c]) for c in accumulate] + [str(script_uuid), str(process_time_used),
                                                            str(elapsed_time)] + [str(len(embeddings[0])), zip_file_path, str(nb_tokens), vect2dict(embeddings[0])]
        print(DELIMITER.join(list_2_print))

    except EOFError:
        break

sys.exit(0)