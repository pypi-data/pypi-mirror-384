# ruff: noqa: INP001

import json
import os

import torch
import triton_python_backend_utils as pb_utils


class TritonPythonModel:
    """Your Python model must use the same class name. Every Python model
    that is created must have "TritonPythonModel" as the class name.
    """

    def initialize(self, args):
        """`initialize` is called only once when the model is being loaded.
        Implementing `initialize` function is optional. This function allows
        the model to initialize any state associated with this model.

        Parameters
        ----------
        args : dict
          Both keys and values are strings. The dictionary keys and values are:
          * model_config: A JSON string containing the model configuration
          * model_instance_kind: A string containing model instance kind
          * model_instance_device_id: A string containing model instance device ID
          * model_repository: Model repository path
          * model_version: Model version
          * model_name: Model name
        """

        # Convert the JSON string that specifies the model configurations into a Python dictionary.
        self.model_config = model_config = json.loads(args["model_config"])

        # Extract the properties from the model configuration file.
        output0_config = pb_utils.get_output_config_by_name(model_config, "output_0")
        output1_config = pb_utils.get_output_config_by_name(model_config, "output_1")

        # Convert Triton types into NumPy types.
        self.output0_dtype = pb_utils.triton_string_to_numpy(output0_config["data_type"])
        self.output1_dtype = pb_utils.triton_string_to_numpy(output1_config["data_type"])

        # Obtain the path of the model repository.
        self.model_directory = os.path.dirname(os.path.realpath(__file__))

        # Obtain the device that is used to run the model.
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load the PyTorch model.
        model_path = os.path.join(self.model_directory, "model.pt")
        if not os.path.exists(model_path):
            raise pb_utils.TritonModelException("Cannot find the pytorch model")

        self.model = torch.jit.load(model_path)

        # Use .to(self.device) to load the PyTorch model to a GPU device if availabe.
        self.model = self.model.to(self.device)

    def execute(self, requests):
        """`execute` must be implemented in every Python model. `execute`
        function receives a list of pb_utils.InferenceRequest as the only
        argument. This function is called when an inference is requested
        for this model. Depending on the batching configuration (e.g. Dynamic
        Batching) used, `requests` may contain multiple requests. Every
        Python model, must create one pb_utils.InferenceResponse for every
        pb_utils.InferenceRequest in `requests`. If there is an error, you can
        set the error argument when creating a pb_utils.InferenceResponse.

        Parameters
        ----------
        requests : list
          A list of pb_utils.InferenceRequest

        Returns
        -------
        list
          A list of pb_utils.InferenceResponse. The length of this list must
          be the same as `requests`
        """
        output0_dtype = self.output0_dtype
        output1_dtype = self.output1_dtype
        responses = []

        # Every Python backend must iterate over everyone of the requests
        # and create a pb_utils.InferenceResponse for each of them.
        for request in requests:
            in_0 = pb_utils.get_input_tensor_by_name(request, "input_0")
            # You can do some pre-processing here if needed
            out_0, out_1 = self.model(in_0.as_numpy())

            # Create output tensors. You need pb_utils.Tensor
            # objects to create pb_utils.InferenceResponse.
            out_tensor_0 = pb_utils.Tensor("output_0", out_0.astype(output0_dtype))
            out_tensor_1 = pb_utils.Tensor("output_1", out_1.astype(output1_dtype))

            # Create InferenceResponse. You can set an error here in case
            # there was a problem with handling this inference request.
            # Below is an example of how you can set errors in inference
            # response:
            #
            # pb_utils.InferenceResponse(
            #    output_tensors=..., TritonError("An error occurred"))
            inference_response = pb_utils.InferenceResponse(output_tensors=[out_tensor_0, out_tensor_1])
            responses.append(inference_response)

        # You should return a list of pb_utils.InferenceResponse. Length
        # of this list must match the length of `requests` list.
        return responses

    def finalize(self):
        """
        The finalize() function is optional. It is called when the model is unloaded to release resources.
        """
        print("Cleaning up...")
