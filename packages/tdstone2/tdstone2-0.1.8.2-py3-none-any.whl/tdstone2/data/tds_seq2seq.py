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
        stop_token = sp.id_to_piece(sp.eos_id())  # Get the stop token (usually </s>)
        return sp, False, stop_token
    elif os.path.exists(sp_path):
        from sentencepiece import SentencePieceProcessor
        sp = SentencePieceProcessor()
        sp.load(sp_path)
        #print("Loaded tokenizer from spiece.model")
        stop_token = sp.id_to_piece(sp.eos_id())  # Get the stop token (usually </s>)
        return sp, False, stop_token
    elif os.path.exists(tokenizer_json_path):
        from tokenizers import Tokenizer
        tokenizer = Tokenizer.from_file(tokenizer_json_path)
        #print("Loaded tokenizer from tokenizer.json")
        stop_token = tokenizer.token_to_id('<|endoftext|>')  # Example stop token for Tokenizer
        return tokenizer, True, stop_token
    else:
        raise FileNotFoundError("No suitable tokenizer model found in the folder.")

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
    max_sequence_length = int(max_sequence_length)
    # Run the model with dummy inputs to check the output shape
    dummy_input_ids = np.random.randint(0, 1000, (1, max_sequence_length)).astype(
        'int32')  # Use the determined max sequence length
    dummy_attention_mask = np.ones((1, max_sequence_length)).astype('int32')

    # Prepare dummy input for model inference
    onnx_inputs = {
        "input_ids": dummy_input_ids, 
        "attention_mask": dummy_attention_mask,
        "max_length": [max_sequence_length], 
        "min_length": min_length, 
        "repetition_penalty": repetition_penalty,
        'num_beams' : num_beams, 
        'num_return_sequences': num_return_sequences, 
        'length_penalty': length_penalty
    }
    # Run the model to inspect the output shape
    outputs = onnx_session.run(None, onnx_inputs)
    output_shape = outputs[0].shape  # Check the shape of the output

    # Return whether 'token_type_ids' is required, the max sequence length, and the output shape's rank
    return requires_token_type_ids, max_sequence_length, len(output_shape)



# Get the zip file path from sys.argv
zip_file_path        = sys.argv[1] if len(sys.argv) > 1 else sys.exit(0)
text_column          = int(sys.argv[2])  # Convert the first argument to an integer (text_column)
accumulate           = ast.literal_eval(sys.argv[3].replace('-',',')) # Convert the third argument (accumulate) from string to list
min_length           = [int(sys.argv[4])]
repetition_penalty   = [int(sys.argv[5])]
num_beams            = [int(sys.argv[6])]
num_return_sequences = [int(sys.argv[7])]
length_penalty       = [int(sys.argv[8])]
max_length_          = [int(sys.argv[9])]
model_type           = sys.argv[10]
prompt               = ''.join(sys.argv[11::])


# Load the data and print the output on the fly
counter = 0
#tokenizer = None  # Initialize as None to avoid errors if not instantiated
onnx_session = None  # Initialize as None to avoid errors if not instantiated

requires_token_type_ids = False
requires_mean_pooling = False

tokenizer, is_Tokenizer, stop_token = load_tokenizer_from_folder(zip_file_path)

# Get the stop token ID
stop_token_id = tokenizer.token_to_id(stop_token) if is_Tokenizer else tokenizer.piece_to_id(stop_token)


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
            options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            options.enable_mem_pattern = False
            options.enable_cpu_mem_arena = False
            providers = ['CPUExecutionProvider']

            # Create an InferenceSession with the model bytes
            with open(os.path.join(zip_file_path, "full_model.onnx"), "rb") as f:
                #model_bytes = f.read()
                onnx_session = ort.InferenceSession(f.read(), sess_options=options, providers=providers)

            # Inspect the ONNX model to determine required inputs and output shape
            requires_token_type_ids, max_sequence_length, output_rank = inspect_onnx_model_inputs(onnx_session)

            # Set counter to indicate that models are loaded
            counter = 1

        # Split input line using the defined delimiter
        input_data = line.split(DELIMITER)

        # Tokenize the line using the tokenizers library (returns list of IDs) 
        if '{}' in prompt:
            complete_prompt = prompt.replace("{}", input_data[text_column]).replace("[RET]","\n")
        else:
            complete_prompt = prompt + ' ' + input_data[text_column].replace("[RET]","\n")
        encoded_input = tokenizer.encode(complete_prompt)

        # Convert tokenized data into numpy arrays
        if type(encoded_input) == list:
            input_ids = np.array([encoded_input], dtype=np.int32)
            attention_mask = np.array([[1] * len(encoded_input)], dtype=np.int32)  # Create attention mask
        else:
            input_ids = np.array([encoded_input.ids], dtype=np.int32)
            attention_mask = np.array([[1] * len(encoded_input.ids)], dtype=np.int32)  # Create attention mask

        nb_tokens_input  = input_ids.shape[1]

        # Pad input_ids, attention_mask, and token_type_ids to max_length=512
        max_length = max_sequence_length
        #max_length = min(max_sequence_length,max_length_[0])
        nb_tokens  = input_ids.shape[1]
        if input_ids.shape[1] > max_length:
            input_ids      = input_ids[:, :max_length]  # Truncate to max_length
            attention_mask = attention_mask[:, :max_length]  # Truncate to max_length

        input_ids_padded = np.pad(input_ids, ((0, 0), (0, max_length - input_ids.shape[1])), mode='constant',
                                constant_values=0)
        attention_mask_padded = np.pad(attention_mask, ((0, 0), (0, max_length - attention_mask.shape[1])),
                                    mode='constant', constant_values=0)


        encoder_result = onnx_session.run(
            None, 
            {"input_ids": input_ids_padded, 
            "attention_mask": attention_mask_padded,
            "max_length": [min(max_sequence_length,max_length_[0])], 
            "min_length": [min(min_length[0],min(max_sequence_length,max_length_[0]))], 
            "repetition_penalty": repetition_penalty,
            'num_beams' : num_beams, 
            'num_return_sequences': num_return_sequences, 
            'length_penalty': length_penalty}
            )


        response = tokenizer.decode(encoder_result[0][0].tolist())[0]

        nb_tokens_output = len(tokenizer.encode(response))


        # Measure time taken up to this point
        process_time_used = time.process_time() - start_process_time
        elapsed_time = time.time() - start_time

        # Start measuring process time and elapsed time
        start_process_time = time.process_time()
        start_time = time.time()

        # Print the output embeddings along with input data
        list_2_print = [str(input_data[c]) for c in accumulate] + [str(script_uuid), str(process_time_used),
                str(elapsed_time)] + [ zip_file_path, str(nb_tokens_input), str(nb_tokens_output), response]
        print(DELIMITER.join(list_2_print))

    except EOFError:
        break

sys.exit(0)