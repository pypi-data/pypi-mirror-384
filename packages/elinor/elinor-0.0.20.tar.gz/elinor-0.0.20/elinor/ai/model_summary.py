from collections import defaultdict, OrderedDict, namedtuple, Counter
import uuid

def get_input_output_per_layer(model, model_input):
    features = OrderedDict()
    handles = OrderedDict()
    HookData = namedtuple("HookData", ["type", "input", "output"])
    
    def hook(name):
        def hook_fn(module, input, output):
            features[name] = HookData(type(module), input, output)
        return hook_fn
    
    for name, module in model.named_modules():
        handles[name] = module.register_forward_hook(hook(name))
    
    with torch.no_grad():
        model(**model_input)
        
    for name, h in handles.items():
        h.remove()
        
    return features

def get_mapping_f2p(features, parameters):
    """
    Get a mapping from feature to parameter.
    """
    def get_main_key(key):
        return key.rsplit(".", 1)[0]  # 删除最后一个 '.' 后的部分（即 .weight, .bias）

    # 建立映射关系
    mapping = defaultdict(list)
    for p_key in parameters.keys():
        main_key = get_main_key(p_key)
        for f_key in features.keys():
            if f_key.startswith(main_key):
                mapping[f_key].append(p_key)
        
    return mapping

def summary(model, model_input):
    features = get_input_output_per_layer(model, model_input)
    parameters = {}
    for k, v in model.named_parameters():
        parameters[k] = v
    mapping = get_mapping_f2p(features, parameters)

    uuid.uuid4()
    fp = open(f"summary_{uuid.uuid4().hex}.txt", "w")

    fp.write("Model: " + type(model).__name__ + "\n")
    fp.write("Input: " + str(model_input.keys()) + "\n")
    fp.write("=" * 80 + "\n")

    for f_key, io_data in features.items():
        input_shape = io_data.input[0].shape if len(io_data.input) > 0 else None
        output_shape = io_data.output[0].shape if len(io_data.output) > 0 else None
        module_type = io_data.type.__name__
        fp.write(f"{f_key}: --- {module_type}\n")
        fp.write(" " * 4 + f">>> {input_shape} --> {output_shape}\n")
        
        for p_key in mapping[f_key]:
            fp.write(" "*4 + f"{p_key}: {parameters[p_key].shape}\n")
            
        fp.write("-" * 80 + "\n")
    fp.write("=" * 80 + "\n")
    fp.close()
    
    return features, parameters, mapping


if __name__ == '__main__':
    from diffusers import UNet2DModel
    import torch
    
    model = UNet2DModel()
    model_input = {
        "sample": torch.randn(1, 3, 64, 64),
        "timestep": 1,
    }
    
    summary(model, model_input)
        