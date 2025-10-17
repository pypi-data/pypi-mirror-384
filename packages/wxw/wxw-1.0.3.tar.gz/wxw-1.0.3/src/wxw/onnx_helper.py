class ONNXRunner:
    """
    A class to run ONNX models using ONNX Runtime.

    Attributes:
        session (onnxruntime.InferenceSession): The ONNX Runtime session for inference.
    """

    def __init__(self, path):
        """
        Initializes the ONNXRunner with the given model path.

        Args:
            path (str): The path to the ONNX model file.
        """
        import onnxruntime

        providers = [
            "CUDAExecutionProvider",
            "CoreMLExecutionProvider",
            "CPUExecutionProvider",
        ]
        self.session = onnxruntime.InferenceSession(path, providers=providers)
        print("Inputs: ", [input.name for input in self.session.get_inputs()])
        print("Outputs: ", [output.name for output in self.session.get_outputs()])

    def __call__(self, img):
        """
        Runs inference on the provided image.

        Args:
            img (numpy.ndarray): The input image for inference.

        Returns:
            list: The inference results.
        """
        try:
            return self.session.run(
                [output.name for output in self.session.get_outputs()],
                {self.session.get_inputs()[0].name: img},
            )
        except Exception as e:
            print("[ONNXRunner] Error during inference:")
            print(e)
            print("Input details:", self.session.get_inputs()[0])
            print("Image shape:", img.shape)


def onnx_model_gflops(path):
    """Calculate and print the GFLOPs of an ONNX model.

    Args:
        path (str): The path to the ONNX model file.
    """
    import onnx_tool

    onnx_tool.model_profile(path)
